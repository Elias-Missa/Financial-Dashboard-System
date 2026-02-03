# strategies/vol_ibs_adx_strategy.py

import pandas as pd
import numpy as np
from ta.trend import ADXIndicator

def generate_signals(df,
                     ibs_limit: float = 0.5,
                     adx_limit: float = 45,
                     adx_period: int = 5,
                     range_period: int = 7) -> pd.DataFrame:
    """
    Volatility + IBS + ADX strategy:
      - Daily range = High - Low
      - IBS = (Close - Low) / Range
      - ADX over `adx_period` bars
      - Go long when:
          * Today's range is the lowest of the last `range_period` days
          * IBS < ibs_limit
          * ADX > adx_limit
          * Close < yesterday's High
      - Exit (sell) when Close > yesterday's High

    Returns a DataFrame with Date, Close, Signal, EquityCurve.
    """
    df = df.copy()

    # --- Calculate indicators ---
    df['range'] = df['High'] - df['Low']
    df['IBS'] = (df['Close'] - df['Low']) / df['range'].replace(0, np.nan)

    adx_ind = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=adx_period)
    df['ADX'] = adx_ind.adx()

    df['lowest_range'] = df['range'].rolling(window=range_period).min()
    df['high_prev'] = df['High'].shift(1)

    # Drop initial NaNs
    df.dropna(subset=['range', 'IBS', 'ADX', 'lowest_range', 'high_prev'], inplace=True)

    # --- Define raw buy/sell conditions ---
    buy_cond  = (
        (df['range'] == df['lowest_range']) &
        (df['IBS']   < ibs_limit) &
        (df['ADX']   > adx_limit) &
        (df['Close'] < df['high_prev'])
    )
    sell_cond = df['Close'] > df['high_prev']

    # --- Generate signals with explicit position tracking ---
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

    # --- Build equity curve ---
    df['EquityCurve'] = 1.0
    in_position = False
    entry_price = 0.0

    for i in range(1, len(df)):
        prev_signal = df['Signal'].iat[i-1]
        prev_equity = df['EquityCurve'].iat[i-1]
        price       = df['Close'].iat[i-1]

        if prev_signal == 1 and not in_position:
            in_position = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_equity

        elif prev_signal == -1 and in_position:
            in_position = False
            ret = (price - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_equity * (1 + ret)

        else:
            df['EquityCurve'].iat[i] = prev_equity

    # --- Final formatting ---
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
