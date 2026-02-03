# strategies/open_breakout_ibs_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df,
                     ibs_limit: float = 0.2,
                     time_stop: int  = None) -> pd.DataFrame:
    """
    Breakout-and-IBS strategy:
      - Buy when:
          * Today's Open > Yesterday's High
          * IBS = (Close - Low) / (High - Low) < ibs_limit
      - Sell when:
          * Close > Yesterday's High
          * OR you’ve held for `time_stop` days (if time_stop is not None)
      - No other stops or money management.
      - Entry and exits at the Close price.

    Args:
      df         : DataFrame with index = date, columns = [Open, High, Low, Close]
      ibs_limit  : IBS threshold
      time_stop  : optional holding period (in bars) to force exit

    Returns:
      DataFrame with columns [Date, Close, Signal, EquityCurve]
    """

    df = df.copy()
    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # calculate IBS
    df['range'] = df['High'] - df['Low']
    df['IBS']   = (df['Close'] - df['Low']) / df['range'].replace(0, np.nan)

    # yesterday’s high
    df['high_prev'] = df['High'].shift(1)

    # drop initial NaNs
    df.dropna(subset=['IBS', 'high_prev'], inplace=True)

    # raw conditions
    buy_cond  = (df['Open'] > df['high_prev']) & (df['IBS'] < ibs_limit)
    sell_cond = df['Close'] > df['high_prev']

    # signal generation with position & time-stop tracking
    df['Signal'] = 0
    in_position  = False
    entry_idx    = None

    for i in range(len(df)):
        if not in_position and buy_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_position         = True
            entry_idx           = i

        elif in_position:
            # time-stop exit
            if time_stop is not None and (i - entry_idx) >= time_stop:
                df['Signal'].iat[i] = -1
                in_position         = False
                entry_idx           = None

            # normal breakout exit
            elif sell_cond.iloc[i]:
                df['Signal'].iat[i] = -1
                in_position         = False
                entry_idx           = None

        # otherwise leave Signal = 0

    # equity curve calculation
    df['EquityCurve'] = 1.0
    in_position       = False
    entry_price       = 0.0

    for i in range(1, len(df)):
        prev_sig = df['Signal'].iat[i-1]
        prev_eq  = df['EquityCurve'].iat[i-1]
        price    = df['Close'].iat[i-1]

        # on buy
        if prev_sig == 1 and not in_position:
            in_position = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_eq

        # on sell
        elif prev_sig == -1 and in_position:
            in_position = False
            ret = (price - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        # hold
        else:
            df['EquityCurve'].iat[i] = prev_eq

    # format for backtester
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
 # optional to lower risk because of time stoprun the strategy on your price data, forcing an exit after 7 days if no breakout sell occurs
# df_signals = generate_signals(df, ibs_limit=0.2, time_stop=7)