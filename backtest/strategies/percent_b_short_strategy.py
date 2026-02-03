# strategies/percent_b_short_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    %b Short Strategy:
      1) ETF closes below its 200-day MA
      2) %b closes above 0.80 for 3 days in a row -> Short on close
      3) Aggressive Version - Short another unit if %b is above 0.80 any additional day
      4) Cover when %b closes under 0.20 or price closes above 200-day MA

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
    
    exit_percentb_below_20 = df['percentB'] < 0.20
    exit_ma200 = df['Close'] > df['MA200']  # Common exit condition
    
    # 5) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    df['DaysInPosition'] = 0  # Track days in position for aggressive version
    
    in_position = False
    
    for i in range(3, len(df)):  # Start at index 3 due to the 3-day lookback
        # Default to previous values
        df['Units'].iat[i] = df['Units'].iat[i-1]
        
        # Update days in position counter
        if in_position:
            df['DaysInPosition'].iat[i] = df['DaysInPosition'].iat[i-1] + 1
        else:
            df['DaysInPosition'].iat[i] = 0
        
        # Check exit conditions first
        if in_position and (exit_percentb_below_20.iloc[i] or exit_ma200.iloc[i]):
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
        
        # Aggressive version - add unit if %b is above 0.80 any additional day in position
        if in_position and percentb_above_80_today.iloc[i] and df['DaysInPosition'].iat[i] > 1:
            # Currently in position (not first day) and %b still above 0.80
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = df['Units'].iat[i-1] + 1
    
    # 6) Calculate equity curve
    df['EquityCurve'] = 1.0
    in_position = False
    entry_prices = []  # List to track entry prices for multiple units
    running_equity = 1.0

    for i in range(1, len(df)):
        curr_signal = df['Signal'].iloc[i]
        curr_price = df['Close'].iloc[i]
        curr_units = df['Units'].iloc[i]
        prev_units = df['Units'].iloc[i-1]
        
        # Fix: Use loc instead of chained assignment
        df.loc[df.index[i], 'EquityCurve'] = running_equity
        
        if curr_signal == -1:
            # Enter or add to short position
            in_position = True
            
            # Handle initial position or adding units
            if prev_units < curr_units:
                # Add new unit(s)
                for _ in range(curr_units - prev_units):
                    entry_prices.append(curr_price)
                
        elif curr_signal == 1 and in_position:
            # Exit short position (all units)
            in_position = False
            
            # Calculate return on each unit and apply to equity
            for entry_price in entry_prices:
                ret = (entry_price - curr_price) / entry_price
                running_equity *= (1 + ret)
            
            # Reset tracking
            entry_prices = []
            # Fix: Use loc instead of chained assignment
            df.loc[df.index[i], 'EquityCurve'] = running_equity

    # 7) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']] 