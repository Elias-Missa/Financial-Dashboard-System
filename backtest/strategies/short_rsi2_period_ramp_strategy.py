# strategies/short_rsi2_period_ramp_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    RSI 2-Period Ramp Short Strategy:
      1) ETF is below the 200-day MA
      2) 2-period RSI rises three days in a row and first day's rise is from above 40
      3) 2-period RSI closes above 90 today -> Sell Short
      4) Exit when 2-period RSI closes below 30 or price closes above 200-day MA

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
    
    # Calculate RSI day-to-day changes
    df['RSI2_Prev'] = df['RSI2'].shift(1)
    df['RSI2_Prev2'] = df['RSI2'].shift(2)
    df['RSI2_Prev3'] = df['RSI2'].shift(3)
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)
    
    # 4) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    
    # RSI rising three days in a row with first rise from above 40
    rsi_rise_day1 = (df['RSI2_Prev2'] > df['RSI2_Prev3']) & (df['RSI2_Prev3'] > 40)
    rsi_rise_day2 = df['RSI2_Prev'] > df['RSI2_Prev2']
    rsi_rise_day3 = df['RSI2'] > df['RSI2_Prev']
    rsi_above_90 = df['RSI2'] > 90
    
    # Combine all entry conditions
    entry_condition = below_ma200 & rsi_rise_day1 & rsi_rise_day2 & rsi_rise_day3 & rsi_above_90
    
    # Exit conditions
    exit_rsi_below_30 = df['RSI2'] < 30
    exit_ma200 = df['Close'] > df['MA200']  # Common exit condition
    
    # 5) Stateful signal generation
    df['Signal'] = 0
    df['Units'] = 0  # Track number of units in position
    
    in_position = False
    
    for i in range(3, len(df)):  # Start at index 3 due to the lookbacks
        # Default to previous values
        df['Units'].iat[i] = df['Units'].iat[i-1]
        
        # Check exit conditions first
        if in_position and (exit_rsi_below_30.iloc[i] or exit_ma200.iloc[i]):
            # Exit signal (cover all units)
            df['Signal'].iat[i] = 1
            df['Units'].iat[i] = 0
            in_position = False
            continue
        
        # Initial entry condition
        if not in_position and entry_condition.iloc[i]:
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