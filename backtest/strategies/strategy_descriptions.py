# strategies/strategy_descriptions.py

"""
This file contains descriptions of all strategies in the system.
It can be imported by a GUI to display strategy information to the user.
"""

strategy_descriptions = {
    "tps_short_strategy": {
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
    
    "rsi2_above_90_strategy": {
        "name": "2-Period RSI > 90 Short Strategy",
        "description": """
        The ETF closes under its 200-day MA.
        
        The 2-period RSI closes above 90. Short on the close.
        
        If at anytime the 2-period RSI closes above 94, short another unit.
        
        Exit when the ETF closes under its 5-period moving average or when price closes above the 200-day MA.
        """
    },
    
    "multiple_days_up_strategy": {
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
    
    "percent_b_short_strategy": {
        "name": "%b Short Strategy",
        "description": """
        The ETF closes below its 200-day MA.
        
        The %b closes above 0.80 for 3 days in a row. Short on the close.
        
        Aggressive Version – If the %b is above 0.80 any additional day you are in the position, 
        short another unit on the close.
        
        Cover your short when the %b closes under 0.20 or when price closes above the 200-day MA.
        """
    },
    
    "rsi2_period_ramp_strategy": {
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
    
    "rsi4_period_overbought_strategy": {
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
    
    "price_pattern_reversal_strategy": {
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