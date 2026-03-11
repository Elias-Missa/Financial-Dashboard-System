import os
import sys
import json
import time
import datetime
import importlib
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ML_DIR = ROOT / "machine_learning"
BACKTEST_DIR = ROOT / "backtest"
sys.path.insert(0, str(ML_DIR))
sys.path.insert(0, str(BACKTEST_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

app = FastAPI(title="Financial Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Simple in-memory cache
# ---------------------------------------------------------------------------
_cache: dict = {}
CACHE_TTL = 300


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < CACHE_TTL:
        return entry["data"]
    return None


def _set_cached(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fetch_spy_prices(years: int = 5) -> pd.DataFrame:
    """Download SPY OHLCV from yfinance, cached."""
    cached = _get_cached(f"spy_{years}")
    if cached is not None:
        return cached

    import yfinance as yf
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=years * 365)
    df = yf.download("SPY", start=start, end=end, progress=False, timeout=15)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel("Ticker")

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    _set_cached(f"spy_{years}", df)
    return df


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    for date, row in df.iterrows():
        records.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]),
        })
    return records


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    ticker: str = "SPY"
    strategy: str = "strategy1"
    start_date: str | None = None
    end_date: str | None = None


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


# ---------------------------------------------------------------------------
# Market routes
# ---------------------------------------------------------------------------

@app.get("/api/market/historical")
def get_historical(years: int = 5):
    try:
        df = _fetch_spy_prices(years)
        return {"data": _df_to_records(df), "ticker": "SPY"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/market/predictions")
def get_predictions():
    """Return ML predictions converted to predicted prices."""
    if "latest" in _predictions_cache:
        return {"predictions": _predictions_cache["latest"], "metadata": None}

    try:
        from db_helpers import load_latest_predictions
        pred_df, metadata = load_latest_predictions()
    except Exception:
        return {"predictions": [], "metadata": None}

    if pred_df.empty:
        return {"predictions": [], "metadata": metadata}

    spy = _fetch_spy_prices(years=5)

    results = []
    for date, row in pred_df.iterrows():
        y_pred = row.get("y_pred")
        if y_pred is None or pd.isna(y_pred):
            continue
        date_ts = pd.Timestamp(date)
        target_date = date_ts + pd.offsets.BDay(21)

        close_on_date = None
        if date_ts in spy.index:
            close_on_date = float(spy.loc[date_ts, "Close"])
        else:
            mask = spy.index <= date_ts
            if mask.any():
                close_on_date = float(spy.loc[spy.index[mask][-1], "Close"])

        if close_on_date is None:
            continue

        predicted_close = round(close_on_date * (1 + float(y_pred)), 2)
        actual_close = None
        if target_date in spy.index:
            actual_close = round(float(spy.loc[target_date, "Close"]), 2)

        results.append({
            "predictionDate": date_ts.strftime("%Y-%m-%d"),
            "targetDate": target_date.strftime("%Y-%m-%d"),
            "predictedReturn": round(float(y_pred), 6),
            "predictedClose": predicted_close,
            "actualClose": actual_close,
            "baseClose": round(close_on_date, 2),
        })

    clean_metadata = None
    if metadata:
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, (datetime.datetime, pd.Timestamp)):
                clean_metadata[k] = str(v)
            elif isinstance(v, (int, float, str, bool)):
                clean_metadata[k] = v

    return {"predictions": results, "metadata": clean_metadata}


@app.get("/api/market/stats")
def get_market_stats():
    """Current market statistics."""
    try:
        import yfinance as yf

        spy = _fetch_spy_prices(years=2)
        if spy.empty:
            raise ValueError("No SPY data")

        current = float(spy["Close"].iloc[-1])
        prev_close = float(spy["Close"].iloc[-2])
        change = current - prev_close
        change_pct = (change / prev_close) * 100

        ma200 = float(spy["Close"].rolling(200).mean().iloc[-1])
        above_200ma = current > ma200
        dist_200ma = ((current - ma200) / ma200) * 100

        high_52w = float(spy["High"].rolling(252).max().iloc[-1])
        low_52w = float(spy["Low"].rolling(252).min().iloc[-1])

        ytd_start = spy.index[spy.index >= pd.Timestamp(f"{datetime.datetime.now().year}-01-01")]
        ytd_return = 0.0
        if len(ytd_start) > 0:
            ytd_open = float(spy.loc[ytd_start[0], "Close"])
            ytd_return = ((current - ytd_open) / ytd_open) * 100

        month_ago_idx = spy.index[spy.index <= pd.Timestamp.now() - pd.DateOffset(months=1)]
        monthly_return = 0.0
        if len(month_ago_idx) > 0:
            month_ago_price = float(spy.loc[month_ago_idx[-1], "Close"])
            monthly_return = ((current - month_ago_price) / month_ago_price) * 100

        vix_val = None
        try:
            vix_df = yf.download("^VIX", period="5d", progress=False, timeout=10)
            if isinstance(vix_df.columns, pd.MultiIndex):
                vix_df.columns = vix_df.columns.droplevel("Ticker")
            if not vix_df.empty:
                vix_val = round(float(vix_df["Close"].iloc[-1]), 2)
        except Exception:
            pass

        prediction_info = None
        if "latest" in _predictions_cache and _predictions_cache["latest"]:
            last_p = _predictions_cache["latest"][-1]
            prediction_info = {
                "predictedReturn": round(last_p["predictedReturn"] * 100, 2),
                "predictedPrice": last_p["predictedClose"],
                "predictionDate": last_p["predictionDate"],
                "targetDate": last_p["targetDate"],
            }
        else:
            try:
                from db_helpers import load_latest_predictions
                pred_df, meta = load_latest_predictions()
                if not pred_df.empty:
                    latest = pred_df.iloc[-1]
                    y_pred = float(latest.get("y_pred", 0))
                    prediction_info = {
                        "predictedReturn": round(y_pred * 100, 2),
                        "predictedPrice": round(current * (1 + y_pred), 2),
                        "predictionDate": str(pred_df.index[-1].date()),
                        "targetDate": str((pred_df.index[-1] + pd.offsets.BDay(21)).date()),
                    }
            except Exception:
                pass

        return {
            "price": round(current, 2),
            "change": round(change, 2),
            "changePct": round(change_pct, 2),
            "ma200": round(ma200, 2),
            "above200ma": above_200ma,
            "dist200ma": round(dist_200ma, 2),
            "high52w": round(high_52w, 2),
            "low52w": round(low_52w, 2),
            "ytdReturn": round(ytd_return, 2),
            "monthlyReturn": round(monthly_return, 2),
            "vix": vix_val,
            "prediction": prediction_info,
            "lastUpdate": spy.index[-1].strftime("%Y-%m-%d"),
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# ---------------------------------------------------------------------------
# Backtest routes
# ---------------------------------------------------------------------------

@app.get("/api/backtest/strategies")
def list_strategies():
    strat_dir = BACKTEST_DIR / "strategies"
    strategies = []
    for f in sorted(strat_dir.glob("*.py")):
        name = f.stem
        if name.startswith("_") or name == "strategy_metadata" or name == "strategy_descriptions":
            continue
        display = name.replace("_", " ").title()
        stype = "Short" if name.startswith("short") else "Long"
        strategies.append({"name": name, "displayName": display, "type": stype})
    return {"strategies": strategies}


@app.post("/api/backtest/run")
def run_backtest(req: BacktestRequest):
    try:
        import backtest as bt

        start = pd.Timestamp(req.start_date) if req.start_date else None
        end = pd.Timestamp(req.end_date) if req.end_date else None
        metrics, trades_df, strategy_df = bt.main(
            req.ticker, req.strategy, start, end, show_plot=False
        )

        if metrics is None:
            raise HTTPException(400, detail="No trades executed for this configuration.")

        equity_curve = []
        if strategy_df is not None and not strategy_df.empty:
            for _, row in strategy_df.iterrows():
                equity_curve.append({
                    "date": row["Date"].strftime("%Y-%m-%d") if hasattr(row["Date"], "strftime") else str(row["Date"]),
                    "equity": round(float(row["EquityCurve"]), 4),
                    "close": round(float(row["Close"]), 2),
                    "signal": int(row["Signal"]),
                })

        monthly = None
        if strategy_df is not None and not strategy_df.empty:
            try:
                monthly_df = bt.calculate_monthly_returns(strategy_df)
                monthly_df = monthly_df.where(monthly_df.notna(), None)
                monthly = json.loads(monthly_df.to_json(orient="records"))
            except Exception:
                pass

        return {
            "metrics": metrics,
            "equityCurve": equity_curve,
            "monthlyReturns": monthly,
            "ticker": req.ticker,
            "strategy": req.strategy,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ---------------------------------------------------------------------------
# Chatbot routes
# ---------------------------------------------------------------------------

@app.post("/api/chatbot/message")
def chat(req: ChatRequest):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, detail="OPENAI_API_KEY not configured in .env")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system_prompt = (
            "You are a senior financial analyst and quantitative researcher. "
            "You help users understand market conditions, trading strategies, "
            "technical indicators, and financial concepts. You provide data-driven "
            "insights and can discuss S&P 500 analysis, backtesting strategies, "
            "risk management, and portfolio construction. Be concise but thorough. "
            "Use specific numbers and data when possible. Format responses with "
            "markdown for readability."
        )

        messages = [{"role": "system", "content": system_prompt}]
        for msg in req.history[-20:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        reply = response.choices[0].message.content
        return {"response": reply}
    except Exception as e:
        raise HTTPException(500, detail=f"Chat error: {str(e)}")


# ---------------------------------------------------------------------------
# ML Prediction Generation
# ---------------------------------------------------------------------------

_predictions_cache: dict = {}


def _build_features_from_yfinance() -> pd.DataFrame:
    """Build technical features from yfinance SPY data for ML prediction."""
    import yfinance as yf

    df = yf.download("SPY", start="2008-01-01", progress=False, timeout=20)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel("Ticker")

    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    c = df["Close"]

    feats = pd.DataFrame(index=df.index)
    feats["ret_1d"] = c.pct_change(1)
    feats["ret_5d"] = c.pct_change(5)
    feats["ret_21d"] = c.pct_change(21)
    feats["ret_63d"] = c.pct_change(63)

    feats["ma50_dist"] = (c - c.rolling(50).mean()) / c.rolling(50).mean()
    feats["ma200_dist"] = (c - c.rolling(200).mean()) / c.rolling(200).mean()
    feats["ma50_slope"] = c.rolling(50).mean().pct_change(10)
    feats["ma200_slope"] = c.rolling(200).mean().pct_change(20)

    feats["vol_20d"] = c.pct_change().rolling(20).std()
    feats["vol_60d"] = c.pct_change().rolling(60).std()
    feats["vol_ratio"] = feats["vol_20d"] / (feats["vol_60d"] + 1e-8)

    feats["rsi_14"] = _compute_rsi(c, 14)
    feats["rsi_5"] = _compute_rsi(c, 5)

    h, l = df["High"], df["Low"]
    feats["atr_14"] = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1).rolling(14).mean() / c

    feats["volume_ratio"] = df["Volume"] / df["Volume"].rolling(50).mean()
    feats["high_52w_dist"] = (c - c.rolling(252).max()) / c.rolling(252).max()

    feats["month"] = df.index.month
    feats["Target_1M"] = c.shift(-21).pct_change(21).shift(21)
    feats["Target_1M"] = (c.shift(-21) - c) / c

    feats["SPY_Close"] = c
    return feats


def _compute_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / (loss + 1e-8)
    return 100 - (100 / (1 + rs))


@app.post("/api/ml/generate-predictions")
def generate_predictions():
    """Train Ridge model on all available SPY data and generate future predictions."""
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler

        feats = _build_features_from_yfinance()

        target_col = "Target_1M"
        exclude = ["Target_1M", "SPY_Close"]
        feature_cols = [c for c in feats.columns if c not in exclude]

        spy_closes = feats["SPY_Close"]
        today = feats.index[-1]

        # --- Prepare training data: all rows with known targets ---
        labeled = feats.copy()
        labeled.replace([np.inf, -np.inf], np.nan, inplace=True)
        labeled = labeled.dropna(subset=[target_col])
        labeled[feature_cols] = labeled[feature_cols].ffill().bfill()
        labeled = labeled.dropna()

        if len(labeled) < 500:
            raise HTTPException(400, detail="Not enough training data")

        # Train on ALL labeled data (expanding window up to today)
        X_train = labeled[feature_cols]
        y_train = labeled[target_col]

        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)

        model = Ridge(alpha=100)
        model.fit(X_train_sc, y_train)

        train_end_date = labeled.index[-1].strftime("%Y-%m-%d")

        # --- Historical comparison predictions (2023+, out-of-sample-ish) ---
        # For honest evaluation, also train a separate model on pre-2023 data
        embargo = 22
        test_start = pd.Timestamp("2023-01-01")
        test_data = labeled[labeled.index >= test_start]
        pre_test = labeled[labeled.index < test_start]

        results = []
        if len(pre_test) > 252 and len(test_data) > 0:
            train_oos = pre_test.iloc[: -embargo] if len(pre_test) > embargo else pre_test
            X_oos = train_oos[feature_cols]
            y_oos = train_oos[target_col]
            scaler_oos = StandardScaler()
            X_oos_sc = scaler_oos.fit_transform(X_oos)
            model_oos = Ridge(alpha=100)
            model_oos.fit(X_oos_sc, y_oos)

            X_test_sc = scaler_oos.transform(test_data[feature_cols])
            y_pred_oos = model_oos.predict(X_test_sc)

            for i, (date, _) in enumerate(test_data.iterrows()):
                close_on_date = float(spy_closes.loc[date]) if date in spy_closes.index else None
                if close_on_date is None:
                    continue
                target_date = date + pd.offsets.BDay(21)
                predicted_close = round(close_on_date * (1 + float(y_pred_oos[i])), 2)
                actual_close = None
                if target_date in spy_closes.index:
                    actual_close = round(float(spy_closes.loc[target_date]), 2)

                results.append({
                    "predictionDate": date.strftime("%Y-%m-%d"),
                    "targetDate": target_date.strftime("%Y-%m-%d"),
                    "predictedReturn": round(float(y_pred_oos[i]), 6),
                    "predictedClose": predicted_close,
                    "actualClose": actual_close,
                    "baseClose": round(close_on_date, 2),
                    "isFuture": False,
                })

        # --- Forward predictions using full model ---
        # Predict from each of the last 30 trading days through today.
        # Each prediction targets 21 business days ahead, so we get a
        # spread of future dates extending ~21 days past today.
        all_feats = feats[feature_cols].ffill().bfill().dropna()
        recent_rows = all_feats.iloc[-30:]

        forward_results = []
        for date in recent_rows.index:
            row_sc = scaler.transform(recent_rows.loc[[date]])
            pred_return = float(model.predict(row_sc)[0])
            close_on_date = float(spy_closes.loc[date]) if date in spy_closes.index else None
            if close_on_date is None:
                continue
            target_date = date + pd.offsets.BDay(21)

            actual_close = None
            if target_date in spy_closes.index:
                actual_close = round(float(spy_closes.loc[target_date]), 2)

            is_future = target_date > today

            forward_results.append({
                "predictionDate": date.strftime("%Y-%m-%d"),
                "targetDate": target_date.strftime("%Y-%m-%d"),
                "predictedReturn": round(pred_return, 6),
                "predictedClose": round(close_on_date * (1 + pred_return), 2),
                "actualClose": actual_close,
                "baseClose": round(close_on_date, 2),
                "isFuture": is_future,
            })

        # Merge: historical + forward, deduplicate by targetDate
        seen_targets = {r["targetDate"] for r in forward_results}
        combined = [r for r in results if r["targetDate"] not in seen_targets]
        combined.extend(forward_results)
        combined.sort(key=lambda r: r["targetDate"])

        _predictions_cache["latest"] = combined
        _predictions_cache["ts"] = time.time()

        latest_future = [r for r in forward_results if r["isFuture"]]
        latest_pred_info = latest_future[-1] if latest_future else forward_results[-1]

        try:
            from db_helpers import save_predictions
            all_pred_returns = [r["predictedReturn"] for r in combined]
            all_dates = [pd.Timestamp(r["predictionDate"]) for r in combined]
            pred_df = pd.DataFrame({
                "y_pred": all_pred_returns,
                "y_true": [r.get("actualClose") for r in combined],
            }, index=all_dates)
            run_id = f"dashboard_ridge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            save_predictions(run_id, pred_df, {"model_type": "Ridge", "process": "Dashboard"})
        except Exception:
            pass

        n_future = len([r for r in combined if r["isFuture"]])
        return {
            "status": "success",
            "n_predictions": len(combined),
            "n_future": n_future,
            "train_end_date": train_end_date,
            "latest_prediction": {
                "date": latest_pred_info["predictionDate"],
                "target_date": latest_pred_info["targetDate"],
                "predicted_return_pct": round(latest_pred_info["predictedReturn"] * 100, 2),
                "predicted_price": latest_pred_info["predictedClose"],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ---------------------------------------------------------------------------
# ML Feature Inventory
# ---------------------------------------------------------------------------

FEATURE_INVENTORY = [
    # ── Trend (machine_learning/features/trend.py) ──
    {"name": "Hurst", "source": "trend", "status": "raw", "desc": "Rolling Hurst exponent (100-day window). Values near 0.5 indicate a random walk; >0.5 suggests trending behavior; <0.5 suggests mean-reversion."},
    {"name": "Trend_200MA_Slope", "source": "trend", "status": "raw", "desc": "1-month percentage change in the 200-day moving average. Captures the direction and acceleration of the long-term trend."},
    {"name": "Dist_from_200MA", "source": "trend", "status": "raw", "desc": "Distance of price from its 200-day MA as a fraction: (price / MA200) - 1. Positive = above trend, negative = below."},
    {"name": "Trend_Efficiency", "source": "trend", "status": "raw", "desc": "ADX-like efficiency ratio over 21 days. Higher values mean price is moving directionally rather than chopping sideways."},
    {"name": "Return_1M", "source": "trend", "status": "raw", "desc": "Trailing 21-day (1-month) return. Basic momentum signal."},
    {"name": "Return_3M", "source": "trend", "status": "dropped", "desc": "Trailing 63-day return. Dropped by rehab (non-stationary) and replaced by Return_3M_Z."},
    {"name": "Return_6M", "source": "trend", "status": "dropped", "desc": "Trailing 126-day return. Dropped by rehab (non-stationary) and replaced by Return_6M_Z."},
    {"name": "Return_12M", "source": "trend", "status": "dropped", "desc": "Trailing 252-day return. Dropped by rehab (non-stationary) and replaced by Return_12M_Z."},
    {"name": "Slope_50", "source": "trend", "status": "raw", "desc": "Rolling linear regression slope over the last 50 trading days. Measures the rate of price change over ~2.5 months."},
    {"name": "Slope_100", "source": "trend", "status": "raw", "desc": "Rolling linear regression slope over the last 100 trading days. Measures the rate of price change over ~5 months."},

    # ── Volatility (machine_learning/features/volatility.py) ──
    {"name": "RV_Ratio", "source": "volatility", "status": "dropped", "desc": "Ratio of 5-day to 20-day realized volatility. Dropped by rehab as toxic/noisy."},
    {"name": "GARCH_Forecast", "source": "volatility", "status": "raw", "desc": "GARCH(1,1) next-day variance forecast. Captures volatility clustering and provides a forward-looking vol estimate."},

    # ── Breadth (machine_learning/features/breadth.py) ──
    {"name": "Vol_ROC", "source": "breadth", "status": "raw", "desc": "5-day rate of change in volume. Spikes indicate unusual participation, often at turning points."},
    {"name": "Sectors_Above_50MA", "source": "breadth", "status": "raw", "desc": "Percentage of 9 major sector ETFs trading above their 50-day MA. A market-internals breadth measure (0-1)."},

    # ── Cross-Asset (machine_learning/features/cross_asset.py) ──
    {"name": "HY_Spread", "source": "cross_asset", "status": "dropped", "desc": "High-yield credit spread proxy (HYG/SHY ratio). Dropped by rehab (non-stationary) and replaced by HY_Spread_Diff."},
    {"name": "USD_Trend", "source": "cross_asset", "status": "dropped", "desc": "50-day SMA slope of the US Dollar Index (DXY). Dropped by rehab and replaced by USD_Trend_Chg."},
    {"name": "Oil_Deviation", "source": "cross_asset", "status": "dropped", "desc": "Oil price deviation from its 50-day SMA as a fraction. Dropped by rehab and replaced by Oil_Deviation_Chg."},

    # ── Macro (machine_learning/features/macro.py) ──
    {"name": "Yield_Curve", "source": "macro", "status": "dropped", "desc": "3-month change in the 10Y-2Y Treasury spread. Dropped by rehab and replaced by Yield_Curve_Chg."},
    {"name": "ISM_PMI", "source": "macro", "status": "raw", "desc": "ISM Manufacturing PMI (forward-filled monthly). Leading indicator of economic expansion (>50) or contraction (<50)."},
    {"name": "UMich_Sentiment", "source": "macro", "status": "dropped", "desc": "Z-scored University of Michigan consumer sentiment (252-day window). Dropped by rehab and replaced by UMich_Sentiment_Chg."},

    # ── Sentiment (machine_learning/features/sentiment.py) ──
    {"name": "Put_Call_Ratio", "source": "sentiment", "status": "dropped", "desc": "CBOE put/call ratio. Dropped by rehab as non-stationary."},
    {"name": "Imp_Real_Gap", "source": "sentiment", "status": "raw", "desc": "Implied vs realized vol gap: VIX/100 minus 20-day annualized realized vol. Positive = market pricing in more fear than recent moves justify."},

    # ── Rehab Transformed (machine_learning/ML/feature_rehab.py) ──
    {"name": "HY_Spread_Diff", "source": "rehab", "status": "transformed", "desc": "21-day difference in HY_Spread. Captures the direction of credit stress change rather than the absolute level.", "transform_from": "HY_Spread", "transform_type": "diff(21)"},
    {"name": "Yield_Curve_Chg", "source": "rehab", "status": "transformed", "desc": "21-day difference in Yield_Curve. Rising = steepening (risk-on), falling = flattening/inverting (risk-off).", "transform_from": "Yield_Curve", "transform_type": "diff(21)"},
    {"name": "USD_Trend_Chg", "source": "rehab", "status": "transformed", "desc": "21-day difference in USD_Trend. Captures dollar momentum shifts rather than absolute trend level.", "transform_from": "USD_Trend", "transform_type": "diff(21)"},
    {"name": "Oil_Deviation_Chg", "source": "rehab", "status": "transformed", "desc": "21-day difference in Oil_Deviation. Captures whether oil is moving further from or reverting to its mean.", "transform_from": "Oil_Deviation", "transform_type": "diff(21)"},
    {"name": "UMich_Sentiment_Chg", "source": "rehab", "status": "transformed", "desc": "21-day percentage change in UMich Sentiment. Captures sentiment momentum rather than level.", "transform_from": "UMich_Sentiment", "transform_type": "pct_change(21)"},
    {"name": "Return_3M_Z", "source": "rehab", "status": "transformed", "desc": "Z-score of trailing 3-month return over a 252-day rolling window. Stationary version that measures how extreme the return is historically.", "transform_from": "Return_3M", "transform_type": "z_score(252)"},
    {"name": "Return_6M_Z", "source": "rehab", "status": "transformed", "desc": "Z-score of trailing 6-month return over a 252-day rolling window.", "transform_from": "Return_6M", "transform_type": "z_score(252)"},
    {"name": "Return_12M_Z", "source": "rehab", "status": "transformed", "desc": "Z-score of trailing 12-month return over a 252-day rolling window.", "transform_from": "Return_12M", "transform_type": "z_score(252)"},
    {"name": "Month_Sin", "source": "rehab", "status": "transformed", "desc": "Sine of month-of-year (cyclical encoding). Captures seasonality effects like January effect without ordinal encoding artifacts.", "transform_from": "month", "transform_type": "sin(2pi*m/12)"},
    {"name": "Month_Cos", "source": "rehab", "status": "transformed", "desc": "Cosine of month-of-year (cyclical encoding). Paired with Month_Sin for full cyclical representation.", "transform_from": "month", "transform_type": "cos(2pi*m/12)"},
    {"name": "Breadth_Thrust", "source": "rehab", "status": "transformed", "desc": "5-day change in Sectors_Above_50MA. A rapid breadth improvement signals a breadth thrust, historically bullish.", "transform_from": "Sectors_Above_50MA", "transform_type": "diff(5)"},
    {"name": "Breadth_Regime", "source": "rehab", "status": "transformed", "desc": "Binary regime flag: 1 if Sectors_Above_50MA > 50% (bull), 0 otherwise (bear). Used by regime-gated models.", "transform_from": "Sectors_Above_50MA", "transform_type": "threshold(0.5)"},
    {"name": "Vol_Trend_Interact", "source": "rehab", "status": "transformed", "desc": "Interaction: Imp_Real_Gap * Return_1M. Captures whether vol fear aligns with or contradicts recent momentum.", "transform_from": "Imp_Real_Gap x Return_1M", "transform_type": "interaction"},
    {"name": "Breadth_Vol_Interact", "source": "rehab", "status": "transformed", "desc": "Interaction: Breadth_Thrust * Imp_Real_Gap. Captures whether breadth surges coincide with elevated volatility fear.", "transform_from": "Breadth_Thrust x Imp_Real_Gap", "transform_type": "interaction"},

    # ── Leakage / Internal (dropped) ──
    {"name": "Log_Target_1M", "source": "pipeline", "status": "dropped", "desc": "Log of 1-month forward return. Dropped by rehab to prevent target leakage."},

    # ── Dashboard-only features (api/main.py _build_features_from_yfinance) ──
    {"name": "ret_1d", "source": "dashboard", "status": "dashboard", "desc": "1-day return. Short-term momentum signal for the dashboard Ridge model."},
    {"name": "ret_5d", "source": "dashboard", "status": "dashboard", "desc": "5-day (1-week) return."},
    {"name": "ret_21d", "source": "dashboard", "status": "dashboard", "desc": "21-day (1-month) return."},
    {"name": "ret_63d", "source": "dashboard", "status": "dashboard", "desc": "63-day (3-month) return."},
    {"name": "ma50_dist", "source": "dashboard", "status": "dashboard", "desc": "Distance from 50-day MA as a fraction: (Close - MA50) / MA50."},
    {"name": "ma200_dist", "source": "dashboard", "status": "dashboard", "desc": "Distance from 200-day MA as a fraction: (Close - MA200) / MA200."},
    {"name": "ma50_slope", "source": "dashboard", "status": "dashboard", "desc": "10-day percentage change of the 50-day MA. Captures short-term trend acceleration."},
    {"name": "ma200_slope", "source": "dashboard", "status": "dashboard", "desc": "20-day percentage change of the 200-day MA. Captures long-term trend acceleration."},
    {"name": "vol_20d", "source": "dashboard", "status": "dashboard", "desc": "20-day rolling standard deviation of daily returns. Short-term realized volatility."},
    {"name": "vol_60d", "source": "dashboard", "status": "dashboard", "desc": "60-day rolling standard deviation of daily returns. Medium-term realized volatility."},
    {"name": "vol_ratio", "source": "dashboard", "status": "dashboard", "desc": "Ratio of vol_20d to vol_60d. Values > 1 mean short-term vol is elevated (risk-off regime)."},
    {"name": "rsi_14", "source": "dashboard", "status": "dashboard", "desc": "14-day Relative Strength Index. Classic momentum oscillator (>70 overbought, <30 oversold)."},
    {"name": "rsi_5", "source": "dashboard", "status": "dashboard", "desc": "5-day RSI. More responsive short-term overbought/oversold signal."},
    {"name": "atr_14", "source": "dashboard", "status": "dashboard", "desc": "14-day Average True Range normalized by price. Measures recent price range volatility."},
    {"name": "volume_ratio", "source": "dashboard", "status": "dashboard", "desc": "Current volume divided by 50-day average volume. Spikes indicate unusual activity."},
    {"name": "high_52w_dist", "source": "dashboard", "status": "dashboard", "desc": "Distance from 52-week high as a fraction. More negative = deeper drawdown from peak."},
    {"name": "month", "source": "dashboard", "status": "dashboard", "desc": "Calendar month (1-12). Captures seasonality for the dashboard model."},
]

REHAB_TRANSFORMS = [
    {"original": "HY_Spread", "result": "HY_Spread_Diff", "transform": "diff(21)", "reason": "Non-stationary level replaced by 1-month change"},
    {"original": "Yield_Curve", "result": "Yield_Curve_Chg", "transform": "diff(21)", "reason": "Non-stationary level replaced by 1-month change"},
    {"original": "USD_Trend", "result": "USD_Trend_Chg", "transform": "diff(21)", "reason": "Non-stationary level replaced by 1-month change"},
    {"original": "Oil_Deviation", "result": "Oil_Deviation_Chg", "transform": "diff(21)", "reason": "Non-stationary level replaced by 1-month change"},
    {"original": "UMich_Sentiment", "result": "UMich_Sentiment_Chg", "transform": "pct_change(21)", "reason": "Non-stationary level replaced by 1-month % change"},
    {"original": "Return_3M", "result": "Return_3M_Z", "transform": "z_score(252)", "reason": "Random-walk return replaced by rolling Z-score"},
    {"original": "Return_6M", "result": "Return_6M_Z", "transform": "z_score(252)", "reason": "Random-walk return replaced by rolling Z-score"},
    {"original": "Return_12M", "result": "Return_12M_Z", "transform": "z_score(252)", "reason": "Random-walk return replaced by rolling Z-score"},
    {"original": "month", "result": "Month_Sin, Month_Cos", "transform": "cyclical encoding", "reason": "Ordinal month replaced by sin/cos pair"},
    {"original": "Sectors_Above_50MA", "result": "Breadth_Thrust", "transform": "diff(5)", "reason": "5-day momentum of breadth (original also kept)"},
    {"original": "Sectors_Above_50MA", "result": "Breadth_Regime", "transform": "threshold(0.5)", "reason": "Binary bull/bear regime flag (original also kept)"},
    {"original": "Imp_Real_Gap x Return_1M", "result": "Vol_Trend_Interact", "transform": "multiplication", "reason": "Interaction: vol fear vs momentum"},
    {"original": "Breadth_Thrust x Imp_Real_Gap", "result": "Breadth_Vol_Interact", "transform": "multiplication", "reason": "Interaction: breadth surge vs vol fear"},
    {"original": "RV_Ratio", "result": "(dropped)", "transform": "removed", "reason": "Toxic / noisy feature"},
    {"original": "Put_Call_Ratio", "result": "(dropped)", "transform": "removed", "reason": "Non-stationary, no stable transform found"},
    {"original": "Log_Target_1M", "result": "(dropped)", "transform": "removed", "reason": "Target leakage"},
]

FINAL_PIPELINE_FEATURES = [
    "Hurst", "Trend_200MA_Slope", "Dist_from_200MA", "Trend_Efficiency",
    "Return_1M", "Slope_50", "Slope_100",
    "GARCH_Forecast", "Vol_ROC", "Sectors_Above_50MA", "ISM_PMI", "Imp_Real_Gap",
    "HY_Spread_Diff", "Yield_Curve_Chg", "USD_Trend_Chg", "Oil_Deviation_Chg",
    "UMich_Sentiment_Chg", "Return_3M_Z", "Return_6M_Z", "Return_12M_Z",
    "Month_Sin", "Month_Cos", "Breadth_Thrust", "Breadth_Regime",
    "Vol_Trend_Interact", "Breadth_Vol_Interact",
]

FINAL_DASHBOARD_FEATURES = [
    "ret_1d", "ret_5d", "ret_21d", "ret_63d",
    "ma50_dist", "ma200_dist", "ma50_slope", "ma200_slope",
    "vol_20d", "vol_60d", "vol_ratio",
    "rsi_14", "rsi_5", "atr_14", "volume_ratio", "high_52w_dist", "month",
]


@app.get("/api/ml/features")
def get_feature_inventory():
    """Return the complete feature inventory, rehab transforms, and final feature lists."""
    return {
        "inventory": FEATURE_INVENTORY,
        "rehab_transforms": REHAB_TRANSFORMS,
        "final_pipeline": FINAL_PIPELINE_FEATURES,
        "final_dashboard": FINAL_DASHBOARD_FEATURES,
    }


# ---------------------------------------------------------------------------
# ML Config routes
# ---------------------------------------------------------------------------

CONFIG_OVERRIDES_PATH = ML_DIR / "ML" / "config_overrides.json"

_CONFIG_KEYS_META: dict = {
    # Model
    "MODEL_TYPE": {"type": "select", "options": ["LinearRegression", "Ridge", "RandomForest", "XGBoost", "MLP", "LSTM", "CNN", "Transformer", "TFT", "RegimeGatedRidge", "RegimeGatedHybrid", "TrendGatedHybrid", "Ridge_Residual_XGB"], "group": "model", "label": "Model Type",
                   "desc": "Which ML algorithm to use for training and prediction. Ranges from simple linear models (Ridge) to deep learning (LSTM, Transformer) and custom ensemble/regime-gated architectures."},
    "REGIME_COL": {"type": "string", "group": "model", "label": "Regime Column",
                   "desc": "Feature column used to split data into two market regimes (e.g. low vs high volatility) for regime-gated models. The median of this column determines the split point."},
    "BASIC_MODEL_SUITE": {"type": "list_string", "group": "model", "label": "Basic Model Suite",
                          "desc": "List of model types to train and compare in batch benchmark runs, letting you evaluate multiple algorithms side-by-side in one sweep."},
    # Ridge
    "RIDGE_ALPHA_GRID": {"type": "list_number", "group": "model", "label": "Ridge Alpha Grid",
                         "desc": "Candidate L2 regularization strengths tested during walk-forward CV. Higher alpha = stronger regularization = simpler model. Best alpha is selected per fold by validation Spearman IC.",
                         "show_when": {"MODEL_TYPE": ["Ridge", "RegimeGatedRidge", "RegimeGatedHybrid", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    # Random Forest
    "RF_N_ESTIMATORS": {"type": "int", "group": "model", "label": "RF: Estimators",
                        "desc": "Number of decision trees in the Random Forest ensemble. More trees reduce variance but increase training time.",
                        "show_when": {"MODEL_TYPE": ["RandomForest", "RegimeGatedHybrid"]}},
    "RF_MAX_DEPTH": {"type": "int", "group": "model", "label": "RF: Max Depth",
                     "desc": "Maximum depth of each decision tree. Deeper trees capture more complex patterns but are more prone to overfitting.",
                     "show_when": {"MODEL_TYPE": ["RandomForest", "RegimeGatedHybrid"]}},
    "RF_MIN_SAMPLES_SPLIT": {"type": "int", "group": "model", "label": "RF: Min Samples Split",
                             "desc": "Minimum number of samples required to split an internal node. Higher values act as regularization by preventing very specific splits.",
                             "show_when": {"MODEL_TYPE": ["RandomForest", "RegimeGatedHybrid"]}},
    "RF_MIN_SAMPLES_LEAF": {"type": "int", "group": "model", "label": "RF: Min Samples Leaf",
                            "desc": "Minimum number of samples required at each leaf node. Prevents the tree from creating leaves that memorize individual data points.",
                            "show_when": {"MODEL_TYPE": ["RandomForest", "RegimeGatedHybrid"]}},
    "RF_RANDOM_STATE": {"type": "int", "group": "model", "label": "RF: Random State",
                        "desc": "Seed for the random number generator. Keeps results reproducible across runs.",
                        "show_when": {"MODEL_TYPE": ["RandomForest", "RegimeGatedHybrid"]}},
    # XGBoost
    "XGB_N_ESTIMATORS": {"type": "int", "group": "model", "label": "XGB: Estimators",
                         "desc": "Number of boosting rounds (trees built sequentially). More rounds can improve accuracy but risk overfitting.",
                         "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_LEARNING_RATE": {"type": "float", "group": "model", "label": "XGB: Learning Rate",
                          "desc": "Step size shrinkage applied to each tree's contribution. Lower values require more estimators but generalize better.",
                          "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_MAX_DEPTH": {"type": "int", "group": "model", "label": "XGB: Max Depth",
                      "desc": "Maximum depth per boosted tree. Shallow trees (3-6) are usually best for financial data to avoid overfitting.",
                      "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_MIN_CHILD_WEIGHT": {"type": "int", "group": "model", "label": "XGB: Min Child Weight",
                             "desc": "Minimum sum of instance weight (hessian) needed in a child node. Higher values make the algorithm more conservative.",
                             "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_SUBSAMPLE": {"type": "float", "group": "model", "label": "XGB: Subsample",
                      "desc": "Fraction of training rows sampled per tree (0-1). Values below 1.0 add stochasticity that can reduce overfitting.",
                      "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_COLSAMPLE_BYTREE": {"type": "float", "group": "model", "label": "XGB: ColSample ByTree",
                             "desc": "Fraction of features randomly sampled for each tree (0-1). Reduces correlation between trees and can improve generalization.",
                             "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_GAMMA": {"type": "float", "group": "model", "label": "XGB: Gamma",
                  "desc": "Minimum loss reduction required to make a further partition on a leaf node. Acts as a pruning threshold; higher = more conservative.",
                  "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_REG_ALPHA": {"type": "float", "group": "model", "label": "XGB: Reg Alpha (L1)",
                      "desc": "L1 regularization term on weights. Encourages sparsity by driving some feature weights to exactly zero.",
                      "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_REG_LAMBDA": {"type": "float", "group": "model", "label": "XGB: Reg Lambda (L2)",
                       "desc": "L2 regularization term on weights. Penalizes large weights to prevent any single feature from dominating.",
                       "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    "XGB_MAX_DELTA_STEP": {"type": "float", "group": "model", "label": "XGB: Max Delta Step",
                           "desc": "Maximum delta step allowed for each tree's weight estimation. Useful for imbalanced data; 0 means no constraint.",
                           "show_when": {"MODEL_TYPE": ["XGBoost", "TrendGatedHybrid", "Ridge_Residual_XGB"]}},
    # MLP
    "MLP_HIDDEN_LAYERS": {"type": "list_int", "group": "model", "label": "MLP: Hidden Layers",
                          "desc": "Tuple of layer sizes for the neural network. E.g. [64, 32] means two hidden layers with 64 and 32 neurons respectively.",
                          "show_when": {"MODEL_TYPE": ["MLP"]}},
    "MLP_LEARNING_RATE_INIT": {"type": "float", "group": "model", "label": "MLP: Learning Rate",
                               "desc": "Initial learning rate for the Adam optimizer. Controls how large each weight update step is.",
                               "show_when": {"MODEL_TYPE": ["MLP"]}},
    "MLP_ALPHA": {"type": "float", "group": "model", "label": "MLP: Alpha (L2)",
                  "desc": "L2 penalty (regularization) term. Prevents overfitting by penalizing large weights in the network.",
                  "show_when": {"MODEL_TYPE": ["MLP"]}},
    "MLP_MAX_ITER": {"type": "int", "group": "model", "label": "MLP: Max Iterations",
                     "desc": "Maximum number of training epochs. The solver iterates until convergence or this limit is reached.",
                     "show_when": {"MODEL_TYPE": ["MLP"]}},
    # LSTM
    "LSTM_CONFIG_NAME": {"type": "select", "options": ["default", "alpha_v1", "trend_long", "deep_value", "debug"], "group": "model", "label": "LSTM: Config Preset",
                         "desc": "Named preset that bundles recommended LSTM hyperparameters. Each preset is tuned for a different use case (e.g. alpha_v1 for daily 21d horizon).",
                         "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_TIME_STEPS": {"type": "int", "group": "model", "label": "LSTM: Time Steps",
                        "desc": "Number of past trading days fed as a sequence to the LSTM. This is the lookback window for each prediction.",
                        "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_LOOKBACK_CANDIDATES": {"type": "list_int", "group": "model", "label": "LSTM: Lookback Candidates",
                                 "desc": "List of lookback window sizes for Optuna to search over during hyperparameter tuning.",
                                 "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_HIDDEN_DIM": {"type": "int", "group": "model", "label": "LSTM: Hidden Dim",
                        "desc": "Number of hidden units in each LSTM layer. More units = more capacity to learn complex temporal patterns, but higher overfit risk.",
                        "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_LAYERS": {"type": "int", "group": "model", "label": "LSTM: Layers",
                    "desc": "Number of stacked LSTM layers. Deeper networks can learn hierarchical temporal features.",
                    "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_EPOCHS": {"type": "int", "group": "model", "label": "LSTM: Epochs",
                    "desc": "Number of full passes through the training data. More epochs allow better convergence but increase training time.",
                    "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_BATCH_SIZE": {"type": "int", "group": "model", "label": "LSTM: Batch Size",
                        "desc": "Number of samples per gradient update. Smaller batches add noise that can help generalization; larger batches are faster.",
                        "show_when": {"MODEL_TYPE": ["LSTM"]}},
    "LSTM_LEARNING_RATE": {"type": "float", "group": "model", "label": "LSTM: Learning Rate",
                           "desc": "Step size for the optimizer. Too high causes instability; too low causes slow convergence.",
                           "show_when": {"MODEL_TYPE": ["LSTM"]}},
    # CNN
    "CNN_TIME_STEPS": {"type": "int", "group": "model", "label": "CNN: Time Steps",
                       "desc": "Length of the input sequence window for the 1D CNN. Each prediction uses this many past days as input.",
                       "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_LOOKBACK_CANDIDATES": {"type": "list_int", "group": "model", "label": "CNN: Lookback Candidates",
                                "desc": "List of lookback window sizes for Optuna to search over during CNN hyperparameter tuning.",
                                "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_FILTERS": {"type": "int", "group": "model", "label": "CNN: Filters",
                    "desc": "Number of convolutional filters (feature detectors) per layer. More filters can detect more patterns but increase model size.",
                    "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_KERNEL_SIZE": {"type": "int", "group": "model", "label": "CNN: Kernel Size",
                        "desc": "Width of the convolutional window. A kernel of 3 looks at 3 consecutive time steps at once to detect local patterns.",
                        "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_POOL_SIZE": {"type": "int", "group": "model", "label": "CNN: Pool Size",
                      "desc": "Size of the pooling window that downsamples the feature maps after convolution, reducing dimensionality.",
                      "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_LAYERS": {"type": "int", "group": "model", "label": "CNN: Layers",
                   "desc": "Number of stacked convolutional layers. More layers can capture increasingly abstract temporal patterns.",
                   "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_DROPOUT": {"type": "float", "group": "model", "label": "CNN: Dropout",
                    "desc": "Fraction of neurons randomly dropped during training (0-1). Regularization technique to prevent overfitting.",
                    "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_EPOCHS": {"type": "int", "group": "model", "label": "CNN: Epochs",
                   "desc": "Number of full training passes through the dataset.",
                   "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_BATCH_SIZE": {"type": "int", "group": "model", "label": "CNN: Batch Size",
                       "desc": "Number of samples per gradient update during CNN training.",
                       "show_when": {"MODEL_TYPE": ["CNN"]}},
    "CNN_LEARNING_RATE": {"type": "float", "group": "model", "label": "CNN: Learning Rate",
                          "desc": "Optimizer step size for CNN training.",
                          "show_when": {"MODEL_TYPE": ["CNN"]}},
    # Transformer
    "TRANSFORMER_TIME_STEPS": {"type": "int", "group": "model", "label": "Transformer: Time Steps",
                               "desc": "Sequence length (lookback window) fed to the Transformer. For monthly data use shorter windows (3); for daily, 10-20.",
                               "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_LOOKBACK_CANDIDATES": {"type": "list_int", "group": "model", "label": "Transformer: Lookback Candidates",
                                        "desc": "Optuna search space for Transformer lookback window sizes.",
                                        "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_MODEL_DIM": {"type": "int", "group": "model", "label": "Transformer: Model Dim",
                              "desc": "Embedding dimension of the Transformer. Each input feature is projected to this size before attention layers.",
                              "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_FEEDFORWARD_DIM": {"type": "int", "group": "model", "label": "Transformer: FF Dim",
                                    "desc": "Hidden dimension of the feedforward network inside each Transformer layer. Typically 2-4x the model dim.",
                                    "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_LAYERS": {"type": "int", "group": "model", "label": "Transformer: Layers",
                           "desc": "Number of stacked Transformer encoder layers. More layers add capacity but increase compute and overfit risk.",
                           "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_HEADS": {"type": "int", "group": "model", "label": "Transformer: Heads",
                          "desc": "Number of attention heads. Multi-head attention lets the model attend to different representation subspaces simultaneously.",
                          "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_DROPOUT": {"type": "float", "group": "model", "label": "Transformer: Dropout",
                            "desc": "Dropout rate applied within attention and feedforward layers for regularization.",
                            "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_EPOCHS": {"type": "int", "group": "model", "label": "Transformer: Epochs",
                           "desc": "Number of full training passes for the Transformer model.",
                           "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_BATCH_SIZE": {"type": "int", "group": "model", "label": "Transformer: Batch Size",
                               "desc": "Samples per gradient update during Transformer training.",
                               "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_LR": {"type": "float", "group": "model", "label": "Transformer: Learning Rate",
                       "desc": "Optimizer learning rate. Conservative values (1e-4) recommended for stable overnight training runs.",
                       "show_when": {"MODEL_TYPE": ["Transformer"]}},
    "TRANSFORMER_WEIGHT_DECAY": {"type": "float", "group": "model", "label": "Transformer: Weight Decay",
                                 "desc": "L2 regularization applied by the AdamW optimizer. Helps prevent overfitting in Transformer models.",
                                 "show_when": {"MODEL_TYPE": ["Transformer"]}},
    # TFT
    "TFT_HIDDEN_DIM": {"type": "int", "group": "model", "label": "TFT: Hidden Dim",
                       "desc": "Hidden state size for the Temporal Fusion Transformer. Controls the model's internal representation capacity.",
                       "show_when": {"MODEL_TYPE": ["TFT"]}},
    "TFT_NUM_HEADS": {"type": "int", "group": "model", "label": "TFT: Heads",
                      "desc": "Number of multi-head attention heads in the TFT interpretable attention layer.",
                      "show_when": {"MODEL_TYPE": ["TFT"]}},
    "TFT_LAYERS": {"type": "int", "group": "model", "label": "TFT: Layers",
                   "desc": "Number of stacked layers in the TFT encoder. More layers increase capacity for complex temporal dependencies.",
                   "show_when": {"MODEL_TYPE": ["TFT"]}},
    "TFT_DROPOUT": {"type": "float", "group": "model", "label": "TFT: Dropout",
                    "desc": "Dropout rate for regularization within TFT attention and gating layers.",
                    "show_when": {"MODEL_TYPE": ["TFT"]}},

    # Data & Target
    "DATA_SOURCE": {"type": "select", "options": ["csv", "mongodb"], "group": "data", "label": "Data Source",
                    "desc": "Where to load feature data from. 'csv' reads a local file; 'mongodb' fetches from MongoDB Atlas (requires MONGODB_URI in .env)."},
    "MONGODB_DB_NAME": {"type": "string", "group": "data", "label": "MongoDB Database Name",
                        "desc": "Name of the MongoDB database to read features from when DATA_SOURCE is 'mongodb'."},
    "DATA_FREQUENCY": {"type": "select", "options": ["daily", "monthly"], "group": "data", "label": "Data Frequency",
                       "desc": "Observation frequency. 'daily' uses every trading day; 'monthly' uses month-end observations only, affecting sample count and embargo sizing."},
    "MONTHLY_ANCHOR": {"type": "select", "options": ["month_end"], "group": "data", "label": "Monthly Anchor",
                       "desc": "How to select the observation date for monthly frequency. 'month_end' uses the last trading day of each month."},
    "TARGET_MODE": {"type": "select", "options": ["forward_21d", "next_month"], "group": "data", "label": "Target Mode",
                    "desc": "How the prediction target is defined. 'forward_21d' uses the return 21 trading days ahead; 'next_month' uses the return to next month-end."},
    "TARGET_HORIZON_DAYS": {"type": "int", "group": "data", "label": "Target Horizon (Days)",
                            "desc": "Number of trading days ahead for the forward return target. 21 days is roughly 1 calendar month."},
    "TARGET_COL": {"type": "string", "group": "data", "label": "Target Column",
                   "desc": "Name of the target column in the feature dataset (e.g. 'Target_1M' for 1-month forward return)."},
    "BIG_MOVE_THRESHOLD": {"type": "float", "group": "data", "label": "Big Move Threshold",
                           "desc": "Absolute return threshold that defines a 'big move' for the big-move classifier. E.g. 0.03 means |return| > 3%."},
    "BIG_MOVE_ALPHA": {"type": "float", "group": "data", "label": "Big Move Alpha",
                       "desc": "Extra weight factor applied to big-move samples in tail-weighted loss. 0.0 disables tail weighting."},
    "APPLY_MACRO_LAG": {"type": "bool", "group": "data", "label": "Apply Macro Lag",
                        "desc": "Whether to lag macro series (e.g. ISM PMI, UMich Sentiment) to approximate their publication delay, reducing look-ahead bias."},
    "MACRO_LAG_DAYS": {"type": "int", "group": "data", "label": "Macro Lag (Days)",
                       "desc": "Number of trading days to lag macro columns by, approximating the real-world release delay (~22 days = ~1 month)."},
    "MACRO_LAG_RELEASE_COLS": {"type": "list_string", "group": "data", "label": "Macro Lag Columns",
                               "desc": "Which macro columns to apply the publication-delay lag to. Only columns with known release delays should be listed."},
    "MACRO_FFILL_COLS": {"type": "list_string", "group": "data", "label": "Macro Forward-Fill Columns",
                         "desc": "Columns allowed to be forward-filled (carry last known value). Appropriate for macro/fundamental series but not rolling indicators."},

    # Features
    "FEAT_Z_SCORE_WINDOW": {"type": "int", "group": "features", "label": "Z-Score Window",
                            "desc": "Rolling window (in trading days) for computing Z-scores to make features stationary. 252 = 1 year for robust mean/std estimates."},
    "FEAT_SHORT_Z_WINDOW": {"type": "int", "group": "features", "label": "Short Z-Score Window",
                            "desc": "Shorter rolling window for Z-scores on more reactive signals like credit spreads. 126 days = ~6 months."},
    "FEAT_DETREND_WINDOW": {"type": "int", "group": "features", "label": "Detrend Window",
                            "desc": "Rolling window for short-term detrending of sentiment-type features. 20 days = ~1 month."},
    "FEAT_ROC_WINDOW": {"type": "int", "group": "features", "label": "Rate of Change Window",
                        "desc": "Window for computing rate-of-change (momentum) transformations on features. 21 days = ~1 month."},
    "FEAT_BREADTH_THRUST_WINDOW": {"type": "int", "group": "features", "label": "Breadth Thrust Window",
                                   "desc": "Rolling window for breadth momentum calculation. 5 days = 1 trading week, capturing short-term breadth surges."},
    "REGIME_BREADTH_THRESHOLD": {"type": "float", "group": "features", "label": "Breadth Regime Threshold",
                                 "desc": "Percentage of stocks above their 50-day MA that defines a bull regime. 0.5 means >50% above MA = bullish."},
    "APPLY_DATA_REHAB": {"type": "bool", "group": "features", "label": "Apply Data Rehab",
                         "desc": "Whether to run the feature rehabilitation pipeline (differencing, Z-scores, drops) in the dataset builder to improve stationarity."},
    "INCLUDE_QC_FEATURES": {"type": "bool", "group": "features", "label": "Include QC Features",
                            "desc": "Whether to include data-quality indicator columns (prefixed 'QC_') as model features. Usually disabled."},
    "FEATURE_STANDARDIZE_PER_FOLD": {"type": "bool", "group": "features", "label": "Standardize Per Fold",
                                     "desc": "Whether to standardize features (zero mean, unit variance) using only training-set statistics per fold, preventing information leakage from validation/test data."},

    # Training
    "TEST_START_DATE": {"type": "string", "group": "training", "label": "Test Start Date",
                        "desc": "Date from which out-of-sample test data begins (e.g. '2023-01-01'). All data before this is available for training/validation."},
    "TRAIN_START_DATE": {"type": "string_nullable", "group": "training", "label": "Train Start Date (null = rolling)",
                         "desc": "If set, fixes the start of training data (expanding window). If null, uses a rolling window of TRAIN_WINDOW_YEARS."},
    "TRAIN_WINDOW_YEARS": {"type": "int", "group": "training", "label": "Train Window (Years)",
                           "desc": "Number of years of data in the rolling training window. Only used when TRAIN_START_DATE is null. 10 years is the default."},
    "VAL_WINDOW_MONTHS": {"type": "int", "group": "training", "label": "Validation Window (Months)",
                          "desc": "Size of the validation window in months, placed between training and test periods for hyperparameter selection."},
    "EMBARGO_MODE": {"type": "select", "options": ["rows"], "group": "training", "label": "Embargo Mode",
                     "desc": "How embargo gaps are measured. 'rows' counts by row index positions (trading days or months depending on frequency)."},
    "EMBARGO_ROWS_DAILY": {"type": "int", "group": "training", "label": "Embargo Rows (Daily)",
                           "desc": "Number of rows to skip between train and val/test splits for daily data. Should be >= target horizon (21) to prevent label leakage."},
    "EMBARGO_ROWS_MONTHLY": {"type": "int", "group": "training", "label": "Embargo Rows (Monthly)",
                             "desc": "Number of rows to skip between splits for monthly data. 1 row = 1 month gap."},
    "WF_VAL_MONTHS": {"type": "int", "group": "training", "label": "WF: Validation Months",
                      "desc": "Validation window size (months) within each walk-forward fold, used for early stopping and hyperparameter selection."},
    "WF_TRAIN_ON_TRAIN_PLUS_VAL": {"type": "bool", "group": "training", "label": "WF: Train on Train+Val",
                                   "desc": "If true, retrains on combined train+val data after selecting hyperparameters. False keeps validation pure for early stopping."},
    "WF_USE_TUNED_PARAMS": {"type": "bool", "group": "training", "label": "WF: Use Tuned Params",
                            "desc": "Whether to load previously tuned hyperparameters from a JSON file instead of using the defaults in config."},
    "WF_BEST_PARAMS_PATH": {"type": "string_nullable", "group": "training", "label": "WF: Best Params Path",
                            "desc": "File path to a JSON file containing tuned hyperparameters (e.g. 'Output/best_params_transformer.json'). Null means use defaults."},
    "WF_GRAD_CLIP_NORM": {"type": "float", "group": "training", "label": "WF: Gradient Clip Norm",
                          "desc": "Maximum gradient norm for deep model training. Clips gradients that exceed this to prevent exploding gradients."},
    "WF_EARLY_STOPPING": {"type": "bool", "group": "training", "label": "WF: Early Stopping",
                          "desc": "Whether to stop training early if validation loss stops improving, acting as a safety net against overfitting."},
    "WF_PATIENCE": {"type": "int", "group": "training", "label": "WF: Patience",
                    "desc": "Number of epochs to wait for validation improvement before triggering early stopping. 10 means stop if no improvement for 10 epochs."},
    "USE_OPTUNA": {"type": "bool", "group": "training", "label": "Use Optuna",
                   "desc": "Whether to enable Optuna-based hyperparameter optimization for deep models (LSTM, CNN, Transformer)."},
    "OPTUNA_TRIALS": {"type": "int", "group": "training", "label": "Optuna Trials",
                      "desc": "Number of hyperparameter combinations Optuna will try. More trials = better search but longer runtime."},
    "TUNE_START_DATE": {"type": "string", "group": "training", "label": "Tune Start Date",
                        "desc": "Start date for the data range used in Optuna tuning folds. Should cover enough history for robust tuning."},
    "TUNE_END_DATE": {"type": "string", "group": "training", "label": "Tune End Date",
                      "desc": "End date for the data range used in Optuna tuning folds. Should end before test period to avoid leakage."},
    "TUNE_TRAIN_YEARS": {"type": "int", "group": "training", "label": "Tune Train Years",
                         "desc": "Training window size (years) per fold during Optuna tuning."},
    "TUNE_VAL_MONTHS": {"type": "int", "group": "training", "label": "Tune Val Months",
                        "desc": "Validation window size (months) per fold during Optuna tuning."},
    "TUNE_STEP_MONTHS": {"type": "int", "group": "training", "label": "Tune Step Months",
                         "desc": "Step size (months) between consecutive tuning folds. Smaller steps = more folds = more robust but slower tuning."},
    "TUNE_EMBARGO_ROWS": {"type": "int", "group": "training", "label": "Tune Embargo Rows",
                          "desc": "Embargo rows between train and val within tuning folds. Should match EMBARGO_ROWS to keep consistency."},
    "TUNE_MAX_FOLDS": {"type": "int", "group": "training", "label": "Tune Max Folds",
                       "desc": "Maximum number of walk-forward folds used per Optuna trial. Caps runtime while still covering multiple market regimes."},
    "TUNE_EPOCHS": {"type": "int", "group": "training", "label": "Tune Epochs",
                    "desc": "Reduced epoch count per fold during tuning. Fewer than production epochs to keep search fast while still informative."},
    "WF_TUNE_THRESHOLD": {"type": "bool", "group": "training", "label": "WF: Tune Threshold",
                          "desc": "Whether to tune the trading signal threshold per walk-forward fold on validation data, preventing policy overfit to a fixed threshold."},
    "WF_THRESHOLD_CRITERION": {"type": "select", "options": ["sharpe", "ic_spread", "total_return", "hit_rate"], "group": "training", "label": "WF: Threshold Criterion",
                               "desc": "Metric used to select the optimal threshold during per-fold tuning. 'sharpe' optimizes risk-adjusted return."},
    "WF_THRESHOLD_N_GRID": {"type": "int", "group": "training", "label": "WF: Threshold Grid Size",
                            "desc": "Number of percentile-based threshold values to evaluate during threshold tuning. More values = finer search."},
    "WF_THRESHOLD_MIN_TRADE_FRAC": {"type": "float", "group": "training", "label": "WF: Min Trade Fraction",
                                    "desc": "Minimum fraction of periods that must generate trades for a threshold to be valid. Prevents degenerate thresholds that rarely trade."},
    "WF_THRESHOLD_VOL_TARGETING": {"type": "bool", "group": "training", "label": "WF: Vol Targeting",
                                   "desc": "Whether to apply volatility targeting (position sizing by inverse volatility) during threshold tuning evaluation."},

    # Loss & Scaling
    "LOSS_MODE": {"type": "select", "options": ["mse", "huber", "tail_weighted"], "group": "loss", "label": "Loss Function",
                  "desc": "Training loss function for deep models. 'mse' is standard; 'huber' is robust to outliers; 'tail_weighted' emphasizes big-move predictions."},
    "HUBER_DELTA": {"type": "float", "group": "loss", "label": "Huber Delta",
                    "desc": "Threshold where Huber loss transitions from quadratic (MSE) to linear (MAE). Smaller delta = more robust to outliers."},
    "TAIL_ALPHA": {"type": "float", "group": "loss", "label": "Tail Alpha",
                   "desc": "Extra weight multiplier applied to samples exceeding the tail threshold. 0.0 disables tail weighting entirely."},
    "TAIL_THRESHOLD": {"type": "float", "group": "loss", "label": "Tail Threshold",
                       "desc": "Absolute return level that defines a tail event. Samples beyond this get extra weight in tail_weighted loss mode."},
    "TARGET_SCALING_MODE": {"type": "select", "options": ["standardize", "vol_scale"], "group": "loss", "label": "Target Scaling Mode",
                            "desc": "How to scale the target variable for deep models. 'standardize' centers and scales; 'vol_scale' divides by std only (keeps 0 at 0)."},
    "PRED_CLIP": {"type": "float_nullable", "group": "loss", "label": "Prediction Clip Bound",
                  "desc": "If set, clips model predictions to [-value, +value] in strategy calculations only. Prevents extreme predictions from oversizing positions. Null = no clipping."},

    # Policy & Risk
    "POLICY_MODE": {"type": "select", "options": ["threshold", "monthly_continuous"], "group": "policy", "label": "Policy Mode",
                    "desc": "Trading policy type. 'threshold' goes long/flat based on a signal cutoff; 'monthly_continuous' sizes positions proportionally to predicted return."},
    "POLICY_K_GRID": {"type": "list_number", "group": "policy", "label": "Policy K-Factor Grid",
                      "desc": "Grid of k-factor multipliers for continuous sizing. k scales the predicted return to determine position size; tuned on validation data."},
    "EXECUTION_FREQUENCY": {"type": "select", "options": ["daily", "monthly"], "group": "policy", "label": "Execution Frequency",
                            "desc": "How often trades are executed. 'monthly' aggregates the last 5 days of predictions into one trade per month and holds for one month."},
    "EVAL_THRESHOLDED_POLICY": {"type": "bool", "group": "policy", "label": "Evaluate Thresholded Policy",
                                "desc": "Whether to evaluate the thresholded (long/flat) trading strategy during walk-forward backtesting."},
    "EVAL_CONTINUOUS_SIZING_POLICY": {"type": "bool", "group": "policy", "label": "Evaluate Continuous Sizing",
                                     "desc": "Whether to evaluate the continuous position-sizing strategy during walk-forward backtesting."},
    "REGIME_RISK_CAP_GRID": {"type": "list_number", "group": "policy", "label": "Regime Risk Cap Grid",
                             "desc": "Candidate cap values (0-1) for limiting position size in low-regime (high-risk) periods. 0.0 = no cap; 0.5 = max 50% position."},
    "REGIME_ORACLE_COL": {"type": "string", "group": "policy", "label": "Regime Oracle Column",
                          "desc": "Feature column used to determine the current risk regime for position capping (e.g. 'RV_Ratio' for realized volatility ratio)."},
    "STACK_LAMBDA_GRID": {"type": "list_number", "group": "policy", "label": "Stack Lambda Grid",
                          "desc": "Candidate mixing weights for the Ridge+XGB residual stack. Lambda controls how much of the XGB residual is added to the Ridge base prediction."},
    "STACK_LAMBDA_CRITERION": {"type": "select", "options": ["rmse", "ic", "decile_spread", "monthly_sharpe"], "group": "policy", "label": "Stack Lambda Criterion",
                               "desc": "Metric used to select the best stack lambda on validation data. 'monthly_sharpe' optimizes for risk-adjusted monthly returns."},
}


def _read_config_values() -> dict:
    """Import ML config and return all known keys with current values."""
    try:
        from ML import config as ml_config
        importlib.reload(ml_config)
    except Exception:
        import importlib as _il
        spec = importlib.util.spec_from_file_location("ml_config", ML_DIR / "ML" / "config.py")
        ml_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ml_config)

    values = {}
    for key in _CONFIG_KEYS_META:
        val = getattr(ml_config, key, None)
        if isinstance(val, tuple):
            val = list(val)
        values[key] = val
    return values


def _read_overrides() -> dict:
    if CONFIG_OVERRIDES_PATH.exists():
        try:
            return json.loads(CONFIG_OVERRIDES_PATH.read_text())
        except Exception:
            return {}
    return {}


def _write_overrides(overrides: dict):
    CONFIG_OVERRIDES_PATH.write_text(json.dumps(overrides, indent=2))


@app.get("/api/ml/config")
def get_ml_config():
    """Return all ML config values + field metadata."""
    values = _read_config_values()
    overrides = _read_overrides()
    return {"values": values, "meta": _CONFIG_KEYS_META, "overrides": overrides}


class MLConfigUpdate(BaseModel):
    updates: dict


@app.put("/api/ml/config")
def update_ml_config(req: MLConfigUpdate):
    """Merge partial updates into the overrides file and reload config."""
    overrides = _read_overrides()
    for key, val in req.updates.items():
        if key not in _CONFIG_KEYS_META:
            raise HTTPException(400, detail=f"Unknown config key: {key}")
        overrides[key] = val
    _write_overrides(overrides)

    try:
        from ML import config as ml_config
        ml_config._apply_overrides()
    except Exception:
        pass

    return {"status": "ok", "overrides": overrides}


@app.post("/api/ml/config/reset")
def reset_ml_config_section(req: MLConfigUpdate):
    """Remove specified keys from overrides to restore defaults."""
    overrides = _read_overrides()
    for key in req.updates:
        overrides.pop(key, None)
    _write_overrides(overrides)

    try:
        from ML import config as ml_config
        importlib.reload(ml_config)
    except Exception:
        pass

    values = _read_config_values()
    return {"status": "ok", "values": values, "overrides": overrides}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}
