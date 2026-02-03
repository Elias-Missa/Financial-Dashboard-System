# utils/strategy_descriptions.py

"""
This file contains descriptions of all strategies in the system.
It can be imported by a GUI to display strategy information to the user.
"""

strategy_descriptions = {
    "short_tps_strategy": {
        "name": "TPS Short Strategy",
        "description": """
        The ETF is below the 200-day MA.
        
        The 2-period RSI is above 75% for two (2) days in a row. Short 10% of your position on the close.
        
        If prices are higher on the close than your previous entry price, any day you're in the position, 
        short 20% more of your position (again you're averaging in).
        
        If prices are higher on the close than your previous entry price, any day you're in the position, 
        short 30% more of your position on the close.
        
        If prices are higher on the close than your previous entry price, any day you're in the position, 
        short 40% more of your position on the close.
        
        Using this 10%, 20%, 30%, 40% scaling-in approach you now have a full position in a very overbought ETF.
        
        Exit on the close when the 2-period RSI closes below 30 or when price closes above the 200-day MA.
        """
    },
    
    "short_rsi2_above_90_strategy": {
        "name": "2-Period RSI > 90 Short Strategy",
        "description": """
        The ETF closes under its 200-day MA.
        
        The 2-period RSI closes above 90. Short on the close.
        
        If at anytime the 2-period RSI closes above 94, short another unit.
        
        Exit when the ETF closes under its 5-period moving average or when price closes above the 200-day MA.
        """
    },
    
    "short_multiple_days_up_strategy": {
        "name": "Multiple Days Up (MDU) Short Strategy",
        "description": """
        The ETF closes under its 200-day moving average.
        
        The ETF closes higher four out of the past five days.
        
        The ETF closes above its 5-period moving average.
        
        Aggressive Version – Short a second unit if prices close higher than your initial entry price 
        anytime you're in the position.
        
        Exit when ETF closes under its 5-period MA or when price closes above the 200-day MA.
        """
    },
    
    "short_percent_b_short_strategy": {
        "name": "%b Short Strategy",
        "description": """
        The ETF closes below its 200-day MA.
        
        The %b closes above 0.80 for 3 days in a row. Short on the close.
        
        Aggressive Version – If the %b is above 0.80 any additional day you are in the position, 
        short another unit on the close.
        
        Exit when ETF closes under its 5-period MA or above 200-day MA.
        """
    },
    
    "short_rsi2_period_ramp_strategy": {
        "name": "RSI 2-Period Ramp Short Strategy",
        "description": """
        The ETF is below the 200-day MA.
        
        The 2-period RSI rises three days in a row and the first day's rise is from above 40.
        
        The 2-period RSI closes above 90 today. Sell Short.
        
        Aggressive Version – Short a second unit if prices close higher than your initial entry 
        price anytime you're in the position.
        
        Exit when the 2-period RSI closes below 30 or when price closes above the 200-day MA.
        """
    },
    
    "short_rsi4_period_overbought_strategy": {
        "name": "RSI 4-Period Overbought Short Strategy",
        "description": """
        The ETF is trading under its 200-day moving average.
        
        The 4-period RSI is above 75, sell short on the close.
        
        Aggressive Version – Sell short another unit if the ETF has a closing 4-period RSI above 80 
        (we're shorting into a further overbought condition).
        
        Exit the position on the close when the 4-period RSI closes under 45 or when price closes 
        above the 200-day MA.
        """
    },
    
    "short_price_pattern_reversal_strategy": {
        "name": "Price Pattern Reversal Short Strategy",
        "description": """
        The ETF is below the 200-day moving average.
        
        Today the ETF closes above its 5-day moving average.
        
        Two days ago the high and low price of the day is above the previous day's.
        
        Yesterday the high and low price of the day was above the previous day's.
        
        Today's high and low price was above yesterday's.
        
        Sell short on the close today.
        
        Aggressive Version – Short a second unit if prices close higher than your initial entry price 
        anytime you're in the position.
        
        Exit on the close when the ETF closes below its 5-day simple moving average or when price closes 
        above the 200-day MA.
        """
    },
    
    "short_lp_bundle3_ibs_rsi_short_strategy": {
        "name": "Bundle3 IBS RSI Short Strategy",
        "description": """
        Entry Conditions:
        1) The ETF closes below its 200-day moving average
        2) The Internal Bar Strength (IBS) is above 0.8
        3) The 2-period RSI is above 80
        4) Short on the close
        
        Exit Conditions:
        1) Exit when the 2-period RSI falls below 30
        2) Exit when price closes above the 200-day moving average
        """
    },
    
    "short_spy_bundle3_mom_short_200_6_strategy": {
        "name": "Momentum Short 200/6 Strategy",
        "description": """
        Entry Conditions:
        1) The ETF closes below its 200-day moving average
        2) The ETF is in a downtrend (6-period price < 200-day MA)
        3) Momentum indicators show continued bearish movement
        4) Short on the close
        
        Exit Conditions:
        1) Exit when price returns to the 6-day moving average
        2) Exit when price closes above the 200-day moving average
        """
    },
    
    "short_smh_bundle3_strategy3": {
        "name": "SMH Bundle3 Strategy",
        "description": """
        Entry Conditions:
        1) The SMH ETF closes below its 200-day moving average
        2) Multiple technical indicators confirm bearish conditions
        3) Short on the close
        
        Exit Conditions:
        1) Exit when technical conditions reverse
        2) Exit when price closes above the 200-day moving average
        """
    },
    
    "volatility_two_day_fall_mean_reversion_strategy": {
        "name": "Volatility Two-Day Fall Mean Reversion",
        "description": """
        Entry Conditions:
        1) Today's fall (yesterday's close – today's close) > 0.75 * 25-day MA of absolute close-to-close change
        2) Yesterday's fall (close[1] – close[2]) > 0.75 * 25-day MA of absolute close-to-close change
        3) Buy on the close when both conditions are met
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        """
    },
    
    "volatility_breakout_ibs_adx_strategy": {
        "name": "Volatility Breakout IBS ADX Strategy",
        "description": """
        Entry Conditions:
        1) Close < 10-day MA of typical price ((H+L+C)/3) - 1.5 * ATR(10)
        2) IBS < 0.6 (oversold condition)
        3) ADX(10) > 20 (trending market)
        4) Buy on the close
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        """
    },
    
    "vol_ibs_adx_strategy": {
        "name": "Volatility IBS ADX Strategy",
        "description": """
        Entry Conditions:
        1) Today's range is the lowest of the last 7 days
        2) IBS < 0.5 (oversold condition)
        3) ADX(5) > 45 (strongly trending market)
        4) Close < yesterday's high
        5) Buy on the close
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        """
    },
    
    "rsi_ibs_mean_reversion": {
        "name": "RSI IBS Mean Reversion Strategy",
        "description": """
        Entry Conditions:
        1) 3-period RSI < 20 (oversold)
        2) IBS < 0.2 (internal price structure is oversold)
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        """
    },
    
    "open_breakout_ibs_strategy": {
        "name": "Open Breakout IBS Strategy",
        "description": """
        Entry Conditions:
        1) Today's open is above yesterday's high (gapping up)
        2) IBS < 0.2 (internal price structure is oversold)
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        2) Optional time stop after a specified number of days
        """
    },
    
    "bear_engulf_ibs_strategy": {
        "name": "Bearish Engulfing IBS Strategy",
        "description": """
        Entry Conditions:
        1) Bearish engulfing pattern:
           - Yesterday was bullish (close > open)
           - Today is bearish (close < open)
           - Today's open > yesterday's close
           - Today's close < yesterday's open
        2) IBS < 0.3 (oversold condition)
        3) Buy on the close (mean reversion trade)
        
        Exit Conditions:
        1) Exit when close is higher than yesterday's high
        """
    },
    
    "strategy1": {
        "name": "Price Breakdown Strategy with IBS Filter",
        "description": """
        Entry Conditions:
        1) The closing price falls below a dynamic threshold: 10-day high minus 2.5x the 25-day average range
        2) Internal Bar Strength (IBS) is below 0.3 (indicates oversold condition)
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when the close is higher than the previous day's high
        """
    },
    
    "strategy2": {
        "name": "Turnaround Tuesday Strategy",
        "description": """
        Entry Conditions:
        1) It's Monday (day of week = 0) 
        2) Price has closed down for two consecutive days
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when the close is higher than the previous day's high
        """
    },
    
    "strategy3": {
        "name": "5-Day Low Breakdown Strategy",
        "description": """
        Entry Conditions:
        1) Price closes below the 5-day low (using the previous 5 days)
        2) Buy on the close
        
        Exit Conditions:
        1) Exit when the close is higher than the previous day's high
        """
    },
    
    "strategy4": {
        "name": "Range Contraction Strategy",
        "description": """
        Entry Conditions:
        1) Today's range (High-Low) is less than the minimum range of the previous 6 days
        2) Price is above the 200-day moving average
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when the close is higher than the previous day's high
        """
    },
    
    "strategy5": {
        "name": "Breakout with IBS Filter Strategy",
        "description": """
        Entry Conditions:
        1) Price makes a new 10-day high
        2) IBS < 0.15 (extremely oversold closing position within the daily range)
        3) Buy on the close
        
        Exit Conditions:
        1) Exit when the close is higher than the previous day's high
        """
    }
}

def get_strategy_description(strategy_name):
    """
    Returns the description of a strategy by name.
    If the strategy name isn't found, returns a generic message.
    """
    # Remove the .py extension if it's included
    if strategy_name.endswith('.py'):
        strategy_name = strategy_name[:-3]
        
    # Return the description if found
    if strategy_name in strategy_descriptions:
        return strategy_descriptions[strategy_name]
    else:
        return {
            "name": "Unknown Strategy",
            "description": "No description available for this strategy."
        }

def get_all_strategy_names():
    """
    Returns a list of all strategy names.
    """
    return list(strategy_descriptions.keys()) 