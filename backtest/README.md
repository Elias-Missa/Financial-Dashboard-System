# Backtesting System

A comprehensive backtesting system for trading strategies, built in Python.

## Features

- Download and process historical stock data using yfinance
- Support for multiple trading strategies
- Comprehensive performance metrics:
  - Total Return
  - CAGR (Compound Annual Growth Rate)
  - Sharpe Ratio
  - Maximum Drawdown
  - Win Rate
  - Profit Factor
  - Average Trade
  - Average Win/Loss
  - Volatility
- Visual performance analysis with equity curve and drawdown plots
- Simple GUI interface for easy strategy testing
- Clean, modular code structure for easy expansion

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Interface

Run the GUI application for a user-friendly interface:

```bash
python run_backtest.py
```

This opens a window where you can:
- Enter a ticker symbol
- Select a strategy
- Set start and end dates (supports data beyond the default 20-year limit)
- Run the backtest
- View performance metrics and charts

### Command Line Interface

Run a backtest using the command line:

```bash
python backtest.py --ticker SPY --strategy strategy1 --start_date 1980-01-01 --end_date 2023-12-31
```

## Strategy Development

To create a new strategy:

1. Create a new Python file in the `strategies` directory
2. Implement the `generate_signals` function that returns a DataFrame with:
   - Date: Date of the data point
   - Close: Closing price
   - Signal: 1 (Buy), -1 (Sell), 0 (Hold)
   - EquityCurve: Cumulative equity curve

Example strategy structure:
```python
def generate_signals(df):
    """
    Generate trading signals based on your strategy logic.
    Returns DataFrame with Date, Close, Signal, and EquityCurve columns.
    """
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Calculate your indicators
    df["SMA_50"] = df["Close"].rolling(window=50).mean()
    df["SMA_200"] = df["Close"].rolling(window=200).mean()
    
    # Drop NaN values
    df = df.dropna()
    
    # Initialize Signal column
    df["Signal"] = 0
    
    # Generate buy signals
    df.loc[df["SMA_50"] > df["SMA_200"], "Signal"] = 1
    
    # Generate sell signals
    df.loc[df["SMA_50"] < df["SMA_200"], "Signal"] = -1
    
    # Calculate equity curve (starting with $1)
    df["EquityCurve"] = 1.0
    position = 0
    entry_price = 0
    
    for i in range(1, len(df)):
        if df["Signal"].iloc[i-1] == 1 and position == 0:  # Enter long
            position = 1
            entry_price = df["Close"].iloc[i-1]
            df.loc[df.index[i], "EquityCurve"] = df["EquityCurve"].iloc[i-1]
        elif df["Signal"].iloc[i-1] == -1 and position == 1:  # Exit long
            position = 0
            exit_price = df["Close"].iloc[i-1]
            df.loc[df.index[i], "EquityCurve"] = df["EquityCurve"].iloc[i-1] * (1 + (exit_price - entry_price) / entry_price)
        else:
            df.loc[df.index[i], "EquityCurve"] = df["EquityCurve"].iloc[i-1]
    
    # Ensure we have a Date column (from index)
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Date"}, inplace=True)
    
    # Return only required columns
    return df[["Date", "Close", "Signal", "EquityCurve"]]
```
### Stateful Signal Generation (ensuring clean plots)

> **Why?**  
> If you vector-ize sells on any up-bar, you'll get a flood of phantom sell signals whenever price keeps rising.  
> Borrow the same loop-with-state approach used in Strat 5 so that **sell** only fires if you're already **in** a position.

```python
# …after computing buy_cond & sell_cond…
df['Signal'] = 0
in_position = False

for i in range(len(df)):
    if not in_position and buy_cond.iloc[i]:
        df['Signal'].iat[i] = 1
        in_position = True
    elif in_position and sell_cond.iloc[i]:
        df['Signal'].iat[i] = -1
        in_position = False
    # else leave Signal = 0



## Project Structure

```
backtest_project/
├── backtest.py          # Main backtesting engine
├── run_backtest.py      # GUI interface
├── requirements.txt     # Project dependencies
├── strategies/          # Trading strategies
│   ├── strategy1.py     # Price action and volatility strategy
│   ├── strategy2.py     # Day of week and price action strategy
│   ├── strategy3.py     # 5-day low breakdown strategy
│   ├── strategy4.py     # Range contraction and 200-day SMA strategy
│   └── strategy5.py     # Breakout and IBS strategy
├── utils/               # Utility functions
│   └── get_data.py      # Data download and processing
└── data/                # Directory for storing data (optional)
```

## Contributing

Feel free to submit issues and enhancement requests! 