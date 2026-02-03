# strategies/xlp_ibs_rsi_short_strategy.py

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator

def generate_signals(df,
                     ibs_entry: float = 0.75,
                     ibs_prev_entry: float = 0.5,
                     rsi_period: int = 5,
                     rsi_entry: float = 70.0,
                     ibs_exit: float = 0.5) -> pd.DataFrame:
    """
    XLP Bundle 3 Strategy 2 – IBS + RSI + seasonality short:
      Entry (signal = -1) when:
        • IBS(today)    > ibs_entry
        • IBS(yesterday)> ibs_prev_entry
        • RSI(rsi_period) > rsi_entry
        • Month != 12
        • Open > Close(yesterday)
      Exit/Cover (signal = +1) when:
        • IBS < ibs_exit   OR
        • Close < Close(yesterday)
    Returns DataFrame [Date, Close, Signal, EquityCurve].
    """
    df = df.copy()

    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # calculate IBS
    df['range'] = df['High'] - df['Low']
    df['IBS']   = (df['Close'] - df['Low']) / df['range'].replace(0, np.nan)
    df['IBS_prev'] = df['IBS'].shift(1)

    # RSI
    rsi = RSIIndicator(close=df['Close'], window=rsi_period)
    df['RSI'] = rsi.rsi()

    # month
    df['Month'] = df.index.month

    # yesterday's close
    df['Close_prev'] = df['Close'].shift(1)

    # drop NaNs
    df.dropna(subset=['IBS','IBS_prev','RSI','Close_prev'], inplace=True)

    # raw conditions
    entry_cond = (
        (df['IBS']      > ibs_entry) &
        (df['IBS_prev'] > ibs_prev_entry) &
        (df['RSI']      > rsi_entry) &
        (df['Month']    != 12) &
        (df['Open']     > df['Close_prev'])
    )
    exit_cond = (
        (df['IBS'] < ibs_exit) |
        (df['Close'] < df['Close_prev'])
    )

    # stateful signal generation
    df['Signal'] = 0
    in_short    = False

    for i in range(len(df)):
        if not in_short and entry_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_short = True
        elif in_short and exit_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_short = False
        # else leave 0

    # equity curve for shorts
    df['EquityCurve'] = 1.0
    in_short    = False
    entry_price = 0.0

    for i in range(1, len(df)):
        prev_sig = df['Signal'].iat[i-1]
        prev_eq  = df['EquityCurve'].iat[i-1]
        price    = df['Close'].iat[i-1]

        if prev_sig == -1 and not in_short:
            in_short    = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == 1 and in_short:
            in_short = False
            ret      = (entry_price - price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            df['EquityCurve'].iat[i] = prev_eq

    # finalize output
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
