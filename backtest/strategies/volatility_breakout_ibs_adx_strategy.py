# strategies/volatility_bundle2_strategy1.py

import pandas as pd
import numpy as np
from ta.volatility import AverageTrueRange
from ta.trend import ADXIndicator

def generate_signals(df,
                     ma_period: int = 10,
                     atr_period: int = 10,
                     atr_mult: float = 1.5,
                     ibs_limit: float = 0.6,
                     adx_period: int = 10,
                     adx_limit: float = 20.0) -> pd.DataFrame:
    """
    Bundle 2 – Volatility Strategy 1:
      Entry (long) at close when:
        1) Close < 10-day MA of ((H+L+C)/3) - atr_mult * ATR(atr_period)
        2) IBS < ibs_limit
        3) ADX(adx_period) > adx_limit
      Exit (sell) at close when Close > Yesterday's High.

    Returns DataFrame [Date, Close, Signal, EquityCurve].
    """
    df = df.copy()

    # ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 1) Typical price MA
    typical = (df['High'] + df['Low'] + df['Close']) / 3
    df['TP_MA'] = typical.rolling(window=ma_period).mean()

    # 2) ATR
    atr_ind = AverageTrueRange(high=df['High'], low=df['Low'], close=df['Close'], window=atr_period)
    df['ATR'] = atr_ind.average_true_range()

    # 3) Lower Band
    df['LowerBand'] = df['TP_MA'] - (atr_mult * df['ATR'])

    # 4) IBS
    df['IBS'] = (df['Close'] - df['Low']) / (df['High'] - df['Low']).replace(0, np.nan)

    # 5) ADX
    adx_ind = ADXIndicator(high=df['High'], low=df['Low'], close=df['Close'], window=adx_period)
    df['ADX'] = adx_ind.adx()

    # 6) Yesterday's high
    df['High_prev'] = df['High'].shift(1)

    # drop rows until all indicators are available
    df.dropna(subset=['TP_MA','ATR','LowerBand','IBS','ADX','High_prev'], inplace=True)

    # raw entry/exit conditions
    buy_cond  = (df['Close'] < df['LowerBand']) & (df['IBS'] < ibs_limit) & (df['ADX'] > adx_limit)
    sell_cond = df['Close'] > df['High_prev']

    # stateful signal generation
    df['Signal'] = 0
    in_long     = False

    for i in range(len(df)):
        if not in_long and buy_cond.iloc[i]:
            df['Signal'].iat[i] = 1
            in_long             = True
        elif in_long and sell_cond.iloc[i]:
            df['Signal'].iat[i] = -1
            in_long             = False
        # else remain 0

    # equity curve calculation
    df['EquityCurve'] = 1.0
    in_long     = False
    entry_price = 0.0

    for i in range(1, len(df)):
        prev_sig   = df['Signal'].iat[i-1]
        prev_eq    = df['EquityCurve'].iat[i-1]
        price      = df['Close'].iat[i-1]

        if prev_sig == 1 and not in_long:
            in_long     = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_eq

        elif prev_sig == -1 and in_long:
            in_long = False
            ret     = (price - entry_price) / entry_price
            df['EquityCurve'].iat[i] = prev_eq * (1 + ret)

        else:
            df['EquityCurve'].iat[i] = prev_eq

    # format output
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
