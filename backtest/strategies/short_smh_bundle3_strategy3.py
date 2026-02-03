# strategies/smh_bundle3_strategy3.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    SMH Bundle 3 Strategy 3 – Threshold‐breakout short with MA filter:
      1) Today’s close > yesterday’s close × 1.003
      2) Yesterday’s close > the day‐before’s close × 1.002
      3) Today’s close < 200-day SMA
      4) Today’s close >  5-day SMA
         → Enter short at today’s close (Signal = -1)
      5) Exit (cover) when Close < 5-day SMA (Signal = +1)

    Returns:
      DataFrame with columns [Date, Close, Signal, EquityCurve]
    """
    df = df.copy()

    # Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Compute moving averages
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA5']   = df['Close'].rolling(window=5).mean()

    # Drop rows with NaNs so everything lines up
    df.dropna(subset=['MA200', 'MA5'], inplace=True)

    # Build look-back series
    close    = df['Close']
    close_1  = close.shift(1)
    close_2  = close.shift(2)

    # Entry and exit conditions
    entry_cond = (
        (close >  close_1 * 1.003) &    # +0.3% today vs. yesterday
        (close_1 > close_2 * 1.002) &   # +0.2% yesterday vs. day-before
        (close <  df['MA200']) &        # below 200-day trend
        (close >  df['MA5'])            # above 5-day trend
    )
    exit_cond  = close < df['MA5']      # cover when price dips below 5-day MA

    # Stateful signal generation
    df['Signal'] = 0
    in_short     = False

    for i in range(len(df)):
        if not in_short and entry_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_short           = True
        elif in_short and exit_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_short           = False
        # else leave Signal = 0

    # Equity curve for shorts
    df['EquityCurve'] = 1.0
    in_short    = False
    entry_price = 0.0

    for i in range(1, len(df)):
        prev_sig = df['Signal'].iat[i-1]
        prev_eq  = df['EquityCurve'].iat[i-1]
        price    = df['Close'].iat[i-1]

        if prev_sig == -1 and not in_short:
            # Enter short at yesterday's close
            in_short    = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == 1 and in_short:
            # Cover at yesterday's close
            in_short = False
            ret      = (entry_price - price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            # No change
            df['EquityCurve'].iat[i] = prev_eq

    # Final formatting
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
