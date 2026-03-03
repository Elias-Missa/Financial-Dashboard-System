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
    df = yf.download("SPY", start=start, end=end, progress=False)

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
async def get_historical(years: int = 5):
    try:
        df = _fetch_spy_prices(years)
        return {"data": _df_to_records(df), "ticker": "SPY"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@app.get("/api/market/predictions")
async def get_predictions():
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
async def get_market_stats():
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
            vix_df = yf.download("^VIX", period="5d", progress=False)
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
async def list_strategies():
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
async def run_backtest(req: BacktestRequest):
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
async def chat(req: ChatRequest):
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

    df = yf.download("SPY", start="2008-01-01", progress=False)
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
async def generate_predictions():
    """Train Ridge model on SPY features and generate predictions."""
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler

        feats = _build_features_from_yfinance()

        target_col = "Target_1M"
        exclude = ["Target_1M", "SPY_Close"]
        feature_cols = [c for c in feats.columns if c not in exclude]

        df = feats.copy()
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df = df.dropna(subset=[target_col])
        df[feature_cols] = df[feature_cols].ffill().bfill()
        df = df.dropna()

        test_start = pd.Timestamp("2023-01-01")
        embargo = 22
        test_mask = df.index >= test_start
        if not test_mask.any():
            raise HTTPException(400, detail="No test data after 2023-01-01")

        test_start_pos = test_mask.argmax()
        train_end_pos = test_start_pos - embargo - 1
        if train_end_pos < 252:
            raise HTTPException(400, detail="Not enough training data")

        train = df.iloc[:train_end_pos + 1]
        test = df.iloc[test_start_pos:]

        X_train, y_train = train[feature_cols], train[target_col]
        X_test, y_test = test[feature_cols], test[target_col]

        scaler = StandardScaler()
        X_train_sc = scaler.fit_transform(X_train)
        X_test_sc = scaler.transform(X_test)

        model = Ridge(alpha=100)
        model.fit(X_train_sc, y_train)

        y_pred_test = model.predict(X_test_sc)

        all_feats = feats[feature_cols].ffill().bfill().dropna()
        latest_row = all_feats.iloc[[-1]]
        latest_date = latest_row.index[0]
        latest_sc = scaler.transform(latest_row)
        latest_pred = float(model.predict(latest_sc)[0])
        latest_close = float(feats["SPY_Close"].dropna().iloc[-1])

        results = []
        spy_closes = feats["SPY_Close"]
        for i, (date, row) in enumerate(test.iterrows()):
            close_on_date = float(spy_closes.loc[date]) if date in spy_closes.index else None
            if close_on_date is None:
                continue
            target_date = date + pd.offsets.BDay(21)
            predicted_close = round(close_on_date * (1 + float(y_pred_test[i])), 2)

            actual_close = None
            if target_date in spy_closes.index:
                actual_close = round(float(spy_closes.loc[target_date]), 2)

            results.append({
                "predictionDate": date.strftime("%Y-%m-%d"),
                "targetDate": target_date.strftime("%Y-%m-%d"),
                "predictedReturn": round(float(y_pred_test[i]), 6),
                "predictedClose": predicted_close,
                "actualClose": actual_close,
                "baseClose": round(close_on_date, 2),
            })

        future_target = latest_date + pd.offsets.BDay(21)
        results.append({
            "predictionDate": latest_date.strftime("%Y-%m-%d"),
            "targetDate": future_target.strftime("%Y-%m-%d"),
            "predictedReturn": round(latest_pred, 6),
            "predictedClose": round(latest_close * (1 + latest_pred), 2),
            "actualClose": None,
            "baseClose": round(latest_close, 2),
        })

        _predictions_cache["latest"] = results
        _predictions_cache["ts"] = time.time()

        try:
            from db_helpers import save_predictions
            pred_df = pd.DataFrame({
                "y_pred": np.concatenate([y_pred_test, [latest_pred]]),
                "y_true": np.concatenate([y_test.values, [np.nan]]),
            }, index=list(X_test.index) + [latest_date])
            run_id = f"dashboard_ridge_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            save_predictions(run_id, pred_df, {"model_type": "Ridge", "process": "Dashboard"})
        except Exception:
            pass

        return {
            "status": "success",
            "n_predictions": len(results),
            "latest_prediction": {
                "date": latest_date.strftime("%Y-%m-%d"),
                "predicted_return_pct": round(latest_pred * 100, 2),
                "predicted_price": round(latest_close * (1 + latest_pred), 2),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}
