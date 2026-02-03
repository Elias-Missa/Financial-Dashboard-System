# strategies/short_percent_b_short_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    %b Short Strategy:
      1) ETF closes below its 200-day MA
      2) %b closes above 0.80 for 3 days in a row -> Short on close
      3) Exit when ETF closes under its 5-period MA or above 200-day MA

    Returns:
      DataFrame with columns [Date, Close, Signal, EquityCurve]
    """
    df = df.copy()

    # 1) Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 2) Compute indicators
    # 200-day moving average
    df['MA200'] = df['Close'].rolling(window=200).mean()
    # 5-day moving average (added for exit condition)
    df['MA5'] = df['Close'].rolling(window=5).mean()
    
    # Calculate Bollinger Bands and %b
    window = 20
    sma = df['Close'].rolling(window=window).mean()
    std = df['Close'].rolling(window=window).std()
    df['BollingerUpper'] = sma + 2 * std
    df['BollingerLower'] = sma - 2 * std
    df['percentB'] = (df['Close'] - df['BollingerLower']) / (df['BollingerUpper'] - df['BollingerLower'])
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)
    
    # 4) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    percentb_above_80_today = df['percentB'] > 0.80
    percentb_above_80_yesterday = df['percentB'].shift(1) > 0.80
    percentb_above_80_two_days_ago = df['percentB'].shift(2) > 0.80
    percentb_above_80_three_days = percentb_above_80_today & percentb_above_80_yesterday & percentb_above_80_two_days_ago
    
    # Updated exit conditions to match short_multiple_days_up_strategy
    exit_below_ma5 = df['Close'] < df['MA5']
    exit_above_ma200 = df['Close'] > df['MA200']
    
    # 5) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    
    in_position = False
    
    for i in range(3, len(df)):  # Start at index 3 due to the 3-day lookback
        # Default to previous values
        df['Units'].iat[i] = df['Units'].iat[i-1]
        
        # Check exit conditions first
        if in_position and (exit_below_ma5.iloc[i] or exit_above_ma200.iloc[i]):
            # Exit signal (cover all units)
            df['Signal'].iat[i] = 1
            df['Units'].iat[i] = 0
            in_position = False
            continue
        
        # Initial entry condition
        if not in_position and below_ma200.iloc[i] and percentb_above_80_three_days.iloc[i]:
            # Short entry
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = 1
            in_position = True
            continue
    
    # 6) Calculate equity curve
    df['EquityCurve'] = 1.0
    in_position = False
    entry_price = None  # Track entry price for return calculation
    running_equity = 1.0

    for i in range(1, len(df)):
        curr_signal = df['Signal'].iloc[i]
        curr_price = df['Close'].iloc[i]
        
        df.loc[df.index[i], 'EquityCurve'] = running_equity
        
        if curr_signal == -1:
            # Enter short position
            in_position = True
            entry_price = curr_price
                
        elif curr_signal == 1 and in_position:
            # Exit short position
            in_position = False
            
            # Calculate return
            ret = (entry_price - curr_price) / entry_price
            running_equity *= (1 + ret)
            
            # Reset tracking
            entry_price = None
            df.loc[df.index[i], 'EquityCurve'] = running_equity

    # 7) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']] 