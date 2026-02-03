# strategies/tps_short_strategy.py

import pandas as pd
import numpy as np

def generate_signals(df) -> pd.DataFrame:
    """
    TPS Short Strategy:
      1) ETF below the 200-day MA
      2) 2-period RSI above 75% for two days in a row -> Short 10% of position
      3) If prices higher than previous entry, short additional 20%, 30%, 40% 
         (scaling in approach)
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
    
    # 3) Drop rows with NaNs so everything lines up
    df.dropna(inplace=True)

    # 4) Build indicator lookbacks
    rsi_today = df['RSI2']
    rsi_yesterday = df['RSI2'].shift(1)
    
    # 5) Define entry and exit conditions
    below_ma200 = df['Close'] < df['MA200']
    rsi_signal = (rsi_today > 75) & (rsi_yesterday > 75)
    exit_rsi = df['RSI2'] < 30
    exit_ma_cross = df['Close'] > df['MA200']  # Common exit condition
    
    # 6) Stateful signal generation
    df['Signal'] = 0
    df['Position'] = 0  # Track position size as percentage
    df['EntryPrice'] = 0.0  # Track entry prices for scale-in logic
    
    in_position = False
    last_entry_price = 0
    
    for i in range(1, len(df)):
        # Set default values based on previous position
        df['Position'].iat[i] = df['Position'].iat[i-1]
        df['EntryPrice'].iat[i] = df['EntryPrice'].iat[i-1]
        
        # Check exit conditions first
        if (exit_rsi.iloc[i] or exit_ma_cross.iloc[i]) and df['Position'].iat[i] > 0:
            # Exit signal (cover)
            df['Signal'].iat[i] = 1
            df['Position'].iat[i] = 0
            df['EntryPrice'].iat[i] = 0
            in_position = False
            last_entry_price = 0
            continue
        
        # Initial entry condition
        if not in_position and below_ma200.iloc[i] and rsi_signal.iloc[i]:
            # Initial short entry (10%)
            df['Signal'].iat[i] = -1
            df['Position'].iat[i] = 0.1  # 10% position
            df['EntryPrice'].iat[i] = df['Close'].iloc[i]
            in_position = True
            last_entry_price = df['Close'].iloc[i]
        
        # Scale-in conditions
        elif in_position and df['Close'].iloc[i] > last_entry_price:
            # Determine the right scaling increment based on current position
            if df['Position'].iat[i] == 0.1:
                # Add 20% more
                df['Signal'].iat[i] = -1
                df['Position'].iat[i] = 0.3  # 10% + 20%
                df['EntryPrice'].iat[i] = df['Close'].iloc[i]
                last_entry_price = df['Close'].iloc[i]
            elif df['Position'].iat[i] == 0.3:
                # Add 30% more
                df['Signal'].iat[i] = -1
                df['Position'].iat[i] = 0.6  # 10% + 20% + 30%
                df['EntryPrice'].iat[i] = df['Close'].iloc[i]
                last_entry_price = df['Close'].iloc[i]
            elif df['Position'].iat[i] == 0.6:
                # Add 40% more
                df['Signal'].iat[i] = -1
                df['Position'].iat[i] = 1.0  # 10% + 20% + 30% + 40% = 100%
                df['EntryPrice'].iat[i] = df['Close'].iloc[i]
                last_entry_price = df['Close'].iloc[i]
    
    # 7) Calculate equity curve
    df['EquityCurve'] = 1.0
    in_position = False
    entry_price = 0.0
    position_size = 0.0
    running_equity = 1.0

    for i in range(1, len(df)):
        curr_signal = df['Signal'].iloc[i]
        curr_price = df['Close'].iloc[i]
        
        df.loc[df.index[i], 'EquityCurve'] = running_equity
        
        if curr_signal == -1:
            # Enter or add to short position
            position_pct = df['Position'].iloc[i] - position_size
            position_size = df['Position'].iloc[i]
            in_position = True
            # For scaling in, we track weighted average entry price
            if entry_price == 0:
                entry_price = curr_price
            else:
                # Update the weighted average entry price
                prev_weight = (position_size - position_pct) / position_size
                new_weight = position_pct / position_size
                entry_price = (entry_price * prev_weight) + (curr_price * new_weight)
                
        elif curr_signal == 1 and in_position:
            # Exit short position
            in_position = False
            # Calculate return on the entire position
            ret = (entry_price - curr_price) / entry_price * position_size
            running_equity = running_equity * (1 + ret)
            df.loc[df.index[i], 'EquityCurve'] = running_equity
            entry_price = 0.0
            position_size = 0.0

    # 8) Final formatting for return
    df = df.reset_index().rename(columns={'index': 'Date'})
    return df[['Date', 'Close', 'Signal', 'EquityCurve']] 