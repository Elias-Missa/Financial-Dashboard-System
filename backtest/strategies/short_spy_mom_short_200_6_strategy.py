# strategies/spy_mom_short_200_6_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    SPY Momentum Short Strategy with MA filter:
      1) Rising prices: Close > Close[1] AND Close[1] > Close[2] 
      2) Accelerating momentum: Today's % change > yesterday's % change
      3) Below long-term trend: Close < 200-day SMA
         → Enter short at today's close (signal = -1)
      4) Exit (cover) when price closes below short-term trend: Close < 6-day SMA (signal = +1)

    Returns:
      DataFrame with columns [Date, Close, Signal, EquityCurve]
    """
    df = df.copy()

    # 1) Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 2) Compute indicators
    df['pct_change'] = df['Close'].pct_change()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA6'] = df['Close'].rolling(window=6).mean()

    # 3) Drop rows with NaNs so everything lines up
    df.dropna(subset=['pct_change', 'MA200', 'MA6'], inplace=True)

    # 4) Build look-back series
    close_today = df['Close']
    close_yesterday = close_today.shift(1)
    close_day_before = close_today.shift(2)
    
    pct_change_today = df['pct_change']
    pct_change_yesterday = df['pct_change'].shift(1)

    # 5) Define entry condition: 
    # - Prices are rising (bullish) but we're below the 200-day MA (bearish overall)
    # - Momentum is accelerating (stronger short-term bullish moves often precede reversals)
    # This combination suggests a potential short-term top and reversal opportunity
    entry_condition = (
        (close_today > close_yesterday) &               # Today higher than yesterday
        (close_yesterday > close_day_before) &          # Yesterday higher than day before
        (pct_change_today > pct_change_yesterday) &     # Today's change greater than yesterday's (acceleration)
        (close_today < df['MA200'])                      # Price below 200-day MA (bearish context)
    )
    
    # Exit condition: Price drops below the short-term trend (6-day MA)
    # This captures a successful short move, suggesting we take profits
    exit_condition = close_today < df['MA6']

    # 6) Stateful signal generation to prevent duplicate signals
    df['Signal'] = 0
    in_short = False  # Trading state variable

    for i in range(len(df)):
        if not in_short and entry_condition.iloc[i]:
            # Enter short position
            df['Signal'].iat[i] = -1
            in_short = True
        elif in_short and exit_condition.iloc[i]:
            # Exit short position (cover)
            df['Signal'].iat[i] = 1
            in_short = False
        # Else maintain current position (Signal remains 0)

    # 7) Calculate equity curve for short trades
    df['EquityCurve'] = 1.0
    in_short = False
    entry_price = 0.0

    for i in range(1, len(df)):
        prev_signal = df['Signal'].iat[i-1]
        prev_equity = df['EquityCurve'].iat[i-1]
        price = df['Close'].iat[i-1]

        if prev_signal == -1 and not in_short:
            # Enter short at yesterday's close
            in_short = True
            entry_price = price
            df['EquityCurve'].iat[i] = prev_equity  # Equity unchanged on entry

        elif prev_signal == 1 and in_short:
            # Cover short at yesterday's close
            in_short = False
            # For short positions, profit = entry price - exit price
            ret = (entry_price - price) / entry_price  # Return as a percentage of entry
            df['EquityCurve'].iat[i] = prev_equity * (1 + ret)  # Update equity with return

        else:
            # No change in position
            df['EquityCurve'].iat[i] = prev_equity

    # 8) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']]
