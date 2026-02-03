# strategies/rsi_ibs_strategy.py

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator

def generate_signals(df,
                     rsi_period: int = 3,
                     rsi_threshold: float = 20.0,
                     ibs_threshold: float = 0.2) -> pd.DataFrame:
    """
    Mean-reversion using 3-day RSI and IBS:
      - RSI(3) < 20
      - IBS = (Close - Low) / (High - Low) < 0.2
      - Buy at close when both true
      - Sell at close when Close > yesterday's High

    Returns DataFrame with Date, Close, Signal, EquityCurve.
    """
    df = df.copy()

    # --- Ensure datetime index ---
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # --- Indicators ---
    # IBS
    df['range'] = df['High'] - df['Low']
    df['IBS'] = (df['Close'] - df['Low']) / df['range'].replace(0, np.nan)

    # RSI
    rsi_ind = RSIIndicator(close=df['Close'], window=rsi_period)
    df['RSI'] = rsi_ind.rsi()

    # Yesterday's high
    df['high_prev'] = df['High'].shift(1)

    # Drop initial NaNs
    df.dropna(subset=['IBS', 'RSI', 'high_prev'], inplace=True)

    # --- Raw buy/sell conditions ---
    buy_cond  = (df['RSI'] < rsi_threshold) & (df['IBS'] < ibs_threshold)
    sell_cond = df['Close'] > df['high_prev']

    # --- Stateful signal loop ---
    df['Signal'] = 0
    in_position = False

    for i in range(len(df)):
        if not in_position and buy_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_position = True
        elif in_position and sell_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_position = False
        # else leave Signal = 0

    # --- Equity curve calculation ---
    df['EquityCurve'] = 1.0
    in_position  = False
    entry_price  = 0.0

    for i in range(1, len(df)):
        prev_sig  = df['Signal'].iat[i-1]
        prev_eq   = df['EquityCurve'].iat[i-1]
        trade_px  = df['Close'].iat[i-1]

        if prev_sig == 1 and not in_position:
            in_position = True
            entry_price = trade_px
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == -1 and in_position:
            in_position = False
            ret = (trade_px - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            df['EquityCurve'].iat[i] = prev_eq

    # --- Final formatting ---
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
