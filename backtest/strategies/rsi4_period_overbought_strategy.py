# strategies/rsi4_period_overbought_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    RSI 4-Period Overbought Strategy:
      1) ETF is trading under its 200-day moving average
      2) 4-period RSI is above 75 -> Sell short on close
      3) Aggressive Version - Sell short another unit if 4-period RSI above 80
      4) Exit when 4-period RSI closes under 45 or price crosses above 200-day MA

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
    
    # Calculate 4-period RSI
    delta = df['Close'].diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=4).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=4).mean()
    rs = gain / loss
    df['RSI4'] = 100 - (100 / (1 + rs))
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)
    
    # 4) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    rsi4_above_75 = df['RSI4'] > 75
    rsi4_above_80 = df['RSI4'] > 80
    
    # Exit conditions
    exit_rsi4_below_45 = df['RSI4'] < 45
    exit_ma200 = df['Close'] > df['MA200']  # Common exit condition
    
    # 5) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    
    in_position = False
    
    for i in range(1, len(df)):
        # Default to previous units
        df['Units'].iat[i] = df['Units'].iat[i-1]
        
        # Check exit conditions first
        if in_position and (exit_rsi4_below_45.iloc[i] or exit_ma200.iloc[i]):
            # Exit signal (cover all units)
            df['Signal'].iat[i] = 1
            df['Units'].iat[i] = 0
            in_position = False
            continue
        
        # Initial entry condition
        if not in_position and below_ma200.iloc[i] and rsi4_above_75.iloc[i]:
            # Short entry
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = 1
            in_position = True
            continue
        
        # Aggressive version - add unit if RSI4 is above 80
        if in_position and rsi4_above_80.iloc[i] and df['Units'].iat[i] == 1:
            # Short another unit
            df['Signal'].iat[i] = -1
            df['Units'].iat[i] = 2
    
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

    # 7) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']] 