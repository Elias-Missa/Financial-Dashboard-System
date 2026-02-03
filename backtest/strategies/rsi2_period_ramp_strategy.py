# strategies/rsi2_period_ramp_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    RSI 2-Period Ramp Strategy:
      1) ETF is below the 200-day MA
      2) 2-period RSI rises three days in a row and the first day's rise is from above 40
      3) 2-period RSI closes above 90 today -> Sell Short
      4) Aggressive Version - Short a second unit if prices close higher than initial entry
      5) Exit when the 2-period RSI closes below 30 or price crosses above 200-day MA

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
    
    # Calculate 2-period RSI
    delta = df['Close'].diff().dropna()
    gain = (delta.where(delta > 0, 0)).rolling(window=2).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=2).mean()
    rs = gain / loss
    df['RSI2'] = 100 - (100 / (1 + rs))
    
    # Calculate daily RSI change
    df['RSI2_Change'] = df['RSI2'].diff()
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)
    
    # 4) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    
    # Calculate RSI rising for 3 days and first rise from above 40
    rsi_change_today = df['RSI2_Change']
    rsi_change_yesterday = df['RSI2_Change'].shift(1)
    rsi_change_two_days_ago = df['RSI2_Change'].shift(2)
    rsi_two_days_ago = df['RSI2'].shift(2)
    
    rsi_rising_3_days = (rsi_change_today > 0) & (rsi_change_yesterday > 0) & (rsi_change_two_days_ago > 0)
    first_rise_above_40 = rsi_two_days_ago > 40
    rsi_above_90 = df['RSI2'] > 90
    
    # Combined entry condition
    entry_condition = below_ma200 & rsi_rising_3_days & first_rise_above_40 & rsi_above_90
    
    # Exit conditions
    exit_rsi_below_30 = df['RSI2'] < 30
    exit_ma200 = df['Close'] > df['MA200']  # Common exit condition
    
    # 5) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    df['EntryPrice'] = 0.0  # Track entry price for aggressive version
    
    in_position = False
    
    for i in range(3, len(df)):  # Start at index 3 due to the lookbacks
        # Default to previous values
        df['Units'].iat[i] = df['Units'].iat[i-1]
        df['EntryPrice'].iat[i] = df['EntryPrice'].iat[i-1]
        
        # Check exit conditions first
        if in_position and (exit_rsi_below_30.iloc[i] or exit_ma200.iloc[i]):
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