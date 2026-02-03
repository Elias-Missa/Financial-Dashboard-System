import os
import sys
import pandas as pd
import importlib

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import strategy modules
import backtest

def check_signal_integrity(strategy_df):
    """
    Check if there are any sequential buy signals without sell signals in between
    or sequential sell signals without buy signals in between.
    
    Returns a tuple of (integrity_result, issues_list)
    """
    issues = []
    
    # Get signal values
    signals = strategy_df['Signal'].values
    dates = strategy_df['Date'].values
    
    # Check for consecutive buy signals (1)
    last_signal = 0
    for i in range(len(signals)):
        if signals[i] == 1:  # Buy signal
            if last_signal == 1:
                issues.append(f"Consecutive buy signals at {dates[i]}")
            last_signal = 1
        elif signals[i] == -1:  # Sell signal
            if last_signal == -1:
                issues.append(f"Consecutive sell signals at {dates[i]}")
            last_signal = -1
    
    # Count total buy and sell signals
    buy_count = sum(signals == 1)
    sell_count = sum(signals == -1)
    
    if buy_count != sell_count and buy_count != sell_count + 1:
        issues.append(f"Unbalanced signals: {buy_count} buys, {sell_count} sells")
    
    return len(issues) == 0, issues

def debug_strategy(ticker, strategy_name):
    """Run backtest and debug signal integrity"""
    result = backtest.main(ticker, strategy_name)
    
    if result is None or len(result) < 3:
        print(f"No valid results for {ticker} using {strategy_name}")
        return
    
    _, trades_df, strategy_df = result
    
    print(f"Debugging {ticker} with {strategy_name}")
    print(f"Total rows in strategy dataframe: {len(strategy_df)}")
    print(f"Total buy signals: {sum(strategy_df['Signal'] == 1)}")
    print(f"Total sell signals: {sum(strategy_df['Signal'] == -1)}")
    
    integrity_ok, issues = check_signal_integrity(strategy_df)
    
    if integrity_ok:
        print("Signal integrity check: PASSED")
    else:
        print("Signal integrity check: FAILED")
        for issue in issues:
            print(f"  - {issue}")
    
    return strategy_df

if __name__ == "__main__":
    # Test all strategies with SPY
    ticker = "SPY"
    for i in range(1, 6):
        strategy_name = f"strategy{i}"
        print(f"\n{'='*50}")
        df = debug_strategy(ticker, strategy_name)
        print(f"{'='*50}\n") 