# strategies/price_pattern_reversal_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    Price Pattern Reversal Strategy:
      1) ETF is below the 200-day moving average
      2) Today the ETF closes above its 5-day moving average
      3) Two days ago the high and low price of the day is above the previous day's
      4) Yesterday the high and low price of the day was above the previous day's
      5) Today's high and low price was above yesterday's
      6) Aggressive Version - Short a second unit if prices close higher than initial entry
      7) Exit when ETF closes below its 5-day MA or above 200-day MA

    Returns:
      DataFrame with columns [Date, Close, Signal, EquityCurve]
    """
    df = df.copy()

    # 1) Ensure datetime index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 2) Compute indicators
    # 200-day and 5-day moving averages
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['MA5'] = df['Close'].rolling(window=5).mean()
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)
    
    # 4) Create shift columns for high/low price comparisons
    df['High_Prev'] = df['High'].shift(1)
    df['Low_Prev'] = df['Low'].shift(1)
    df['High_2Prev'] = df['High'].shift(2)
    df['Low_2Prev'] = df['Low'].shift(2)
    df['High_3Prev'] = df['High'].shift(3)
    df['Low_3Prev'] = df['Low'].shift(3)
    
    # 5) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    above_ma5 = df['Close'] > df['MA5']
    
    # Check if high and low are both above the previous day's
    day2_above_day3 = (df['High_2Prev'] > df['High_3Prev']) & (df['Low_2Prev'] > df['Low_3Prev'])
    day1_above_day2 = (df['High_Prev'] > df['High_2Prev']) & (df['Low_Prev'] > df['Low_2Prev'])
    day0_above_day1 = (df['High'] > df['High_Prev']) & (df['Low'] > df['Low_Prev'])
    
    # Combined entry condition
    entry_condition = below_ma200 & above_ma5 & day2_above_day3 & day1_above_day2 & day0_above_day1
    
    # Exit conditions
    exit_ma5 = df['Close'] < df['MA5']
    exit_ma200 = df['Close'] > df['MA200']  # Common exit condition
    
    # 6) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    df['EntryPrice'] = 0.0  # Track entry price for aggressive version
    
    in_position = False
    
    for i in range(3, len(df)):  # Start at index 3 due to the lookbacks
        # Default to previous values
        df['Units'].iat[i] = df['Units'].iat[i-1]
        df['EntryPrice'].iat[i] = df['EntryPrice'].iat[i-1]
        
        # Check exit conditions first
        if in_position and (exit_ma5.iloc[i] or exit_ma200.iloc[i]):
            # Exit signal (cover all units)
            df['Signal'].iat[i] = 1
            df['Units'].iat[i] = 0
            df['EntryPrice'].iat[i] = 0
            in_position = False
            continue
        
        # Initial entry condition
        if not in_position and entry_condition.iloc[i]:
            # Short entry
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = 1
            df['EntryPrice'].iat[i] = df['Close'].iloc[i]
            in_position = True
            continue
        
        # Aggressive version - add unit if price closes higher than initial entry
        if in_position and df['Close'].iloc[i] > df['EntryPrice'].iloc[i] and df['Units'].iat[i] == 1:
            # Short another unit
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = 2
    
    # 7) Calculate equity curve
    df['EquityCurve'] = 1.0
    in_position = False
    entry_prices = []  # List to track entry prices for multiple units
    running_equity = 1.0

    for i in range(1, len(df)):
        curr_signal = df['Signal'].iloc[i]
        curr_price = df['Close'].iloc[i]
        curr_units = df['Units'].iloc[i]
        prev_units = df['Units'].iloc[i-1]
        
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
            df.loc[df.index[i], 'EquityCurve'] = running_equity

    # 8) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']] 