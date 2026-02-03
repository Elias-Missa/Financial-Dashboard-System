# strategies/volatility_bundle2_strategy2.py

import pandas as pd
import numpy as np

def generate_signals(df,
                     abs_ma_period: int = 25,
                     fall_mult: float = 0.75) -> pd.DataFrame:
    """
    Bundle 2 – Volatility Strategy 2:
      Entry (long) at close when:
        1) Today’s fall (yesterday’s close – today’s close)
           > (25-day MA of |close–close[1]| shifted 1 bar) * fall_mult
        2) Yesterday’s fall (close[1]–close[2])
           > (25-day MA of |close–close[1]| shifted 2 bars) * fall_mult
      Exit (sell) at close when Close > yesterday’s High.

    Returns DataFrame [Date, Close, Signal, EquityCurve].
    """
    df = df.copy()

    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 1) Absolute close-to-close change and its 25-day MA
    df['AbsCh']   = (df['Close'] - df['Close'].shift(1)).abs()
    df['AbsMA25'] = df['AbsCh'].rolling(window=abs_ma_period).mean()

    # 2) Yesterday's high for exit rule
    df['High_prev'] = df['High'].shift(1)

    # drop initial NaNs so everything lines up
    df.dropna(subset=['AbsMA25', 'High_prev'], inplace=True)

    # 3) Define fall curves
    fall_today     = (df['Close'].shift(1) - df['Close']) > (df['AbsMA25'].shift(1) * fall_mult)
    fall_yesterday = (df['Close'].shift(2) - df['Close'].shift(1)) > (df['AbsMA25'].shift(2) * fall_mult)

    # 4) Raw entry/exit conditions
    buy_cond  = fall_today & fall_yesterday
    sell_cond = df['Close'] > df['High_prev']

    # 5) Stateful signal generation
    df['Signal'] = 0
    in_long      = False

    for i in range(len(df)):
        if not in_long and buy_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_long             = True
        elif in_long and sell_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_long             = False
        # else leave 0

    # 6) Equity curve calculation
    df['EquityCurve'] = 1.0
    in_long           = False
    entry_price       = 0.0

    for i in range(1, len(df)):
        prev_sig = df['Signal'].iat[i-1]
        prev_eq  = df['EquityCurve'].iat[i-1]
        price    = df['Close'].iat[i-1]

        if prev_sig == 1 and not in_long:
            # Enter long at yesterday's close
            in_long     = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == -1 and in_long:
            # Exit long at yesterday's close
            in_long = False
            ret     = (price - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            # Carry forward equity
            df['EquityCurve'].iat[i] = prev_eq

    # 7) Final formatting
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
