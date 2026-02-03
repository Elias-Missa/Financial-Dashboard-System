# strategies/bear_engulf_ibs_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df, ibs_limit: float = 0.3) -> pd.DataFrame:
    """
    Bearish Engulfing + IBS mean-reversion:
      1) Yesterday: Close > Open
      2) Today:  Close < Open
      3) Today:  Open > Yesterday's Close
      4) Today:  Close < Yesterday's Open
      5) IBS = (Close - Low)/(High - Low) < ibs_limit
      → Buy at today's close when all true
      → Sell at close when Close > yesterday's High

    Returns a DataFrame with Date, Close, Signal, EquityCurve.
    """
    df = df.copy()

    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    # Check if there's enough data to calculate signals
    if len(df) < 2:
        print("⚠️ Not enough data to calculate signals")
        # Return an empty DataFrame with required columns
        empty_df = pd.DataFrame(columns=["Date", "Close", "Signal", "EquityCurve"])
        empty_df["Signal"] = 0
        empty_df["EquityCurve"] = 1.0
        if not df.empty:
            empty_df["Date"] = df.index.to_series().reset_index(drop=True)
            empty_df["Close"] = df["Close"].reset_index(drop=True)
        return empty_df

    # calculate IBS
    df['range'] = df['High'] - df['Low']
    df['IBS']   = (df['Close'] - df['Low']) / df['range'].replace(0, np.nan)

    # yesterday's OHLC
    df['Open_prev']  = df['Open'].shift(1)
    df['Close_prev'] = df['Close'].shift(1)
    df['High_prev']  = df['High'].shift(1)

    # drop rows with NaNs in any of the above - but make a safety check first
    prev_len = len(df)
    df = df.dropna(subset=['IBS','Open_prev','Close_prev','High_prev'])
    
    # If we lost all data after dropna, return empty dataframe with required columns
    if df.empty:
        print("⚠️ No valid data after removing NaN values")
        empty_df = pd.DataFrame(columns=["Date", "Close", "Signal", "EquityCurve"])
        empty_df["Signal"] = 0
        empty_df["EquityCurve"] = 1.0
        return empty_df
        
    # Check if we have sufficient data after cleaning
    if len(df) < 2:
        print(f"⚠️ Insufficient data after cleaning: {len(df)} rows")
        empty_df = pd.DataFrame(columns=["Date", "Close", "Signal", "EquityCurve"])
        empty_df = df.reset_index()[["Date", "Close"]].copy()
        empty_df["Signal"] = 0
        empty_df["EquityCurve"] = 1.0
        return empty_df

    # raw buy/sell conditions
    buy_cond = (
        (df['Close_prev'] > df['Open_prev'])   # yesterday bullish
        & (df['Close'] < df['Open'])           # today bearish
        & (df['Open'] > df['Close_prev'])      # engulfing
        & (df['Close'] < df['Open_prev'])
        & (df['IBS'] < ibs_limit)
    )
    sell_cond = df['Close'] > df['High_prev']

    # stateful signal generation
    df['Signal'] = 0
    in_position = False

    for i in range(len(df)):
        if not in_position and buy_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_position = True
        elif in_position and sell_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_position = False
        # else leave 0

    # equity curve
    df['EquityCurve'] = 1.0
    in_position  = False
    entry_price  = 0.0

    for i in range(1, len(df)):
        prev_sig = df['Signal'].iat[i-1]
        prev_eq  = df['EquityCurve'].iat[i-1]
        px       = df['Close'].iat[i-1]

        if prev_sig == 1 and not in_position:
            in_position = True
            entry_price = px
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == -1 and in_position:
            in_position = False
            ret = (px - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            df['EquityCurve'].iat[i] = prev_eq

    # format output
    df = df.reset_index().rename(columns={'index': 'Date'})
    result_df = df[['Date', 'Close', 'Signal', 'EquityCurve']]
    
    # Check if we have any signals
    if (result_df["Signal"] != 0).sum() == 0:
        print("⚠️ No trading signals generated for this date range")
    
    return result_df
