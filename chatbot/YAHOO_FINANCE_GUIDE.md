# Yahoo Finance Integration Guide

The Market Cipher AI Chatbot now pulls real market data from Yahoo Finance for backtesting.

## How It Works

### Data Source
- **Provider**: Yahoo Finance (via `quantmod` R package)
- **Default Ticker**: SPY (S&P 500 ETF)
- **History**: Last 500 trading days
- **Frequency**: Daily data
- **Fields**: Date, Open, High, Low, Close, Volume

### Changing the Ticker Symbol

You can test indicators on any stock or ETF available on Yahoo Finance:

1. **In the App UI**: 
   - Look for the "Stock Ticker" input at the top
   - Enter any valid ticker symbol (e.g., AAPL, MSFT, TSLA, QQQ)
   - The data will automatically update when you execute code

2. **Programmatically**:
   ```r
   # In R/code_executor.R
   market_data <- load_sample_data(symbol = "AAPL", days = 500)
   ```

### Popular Tickers to Try

**Major Indices:**
- SPY - S&P 500 ETF
- QQQ - Nasdaq 100 ETF
- DIA - Dow Jones ETF
- IWM - Russell 2000 ETF

**Individual Stocks:**
- AAPL - Apple
- MSFT - Microsoft
- GOOGL - Google
- AMZN - Amazon
- TSLA - Tesla
- NVDA - Nvidia

**Crypto (via ETFs):**
- BITO - Bitcoin Strategy ETF

**Commodities:**
- GLD - Gold ETF
- SLV - Silver ETF
- USO - Oil ETF

**International:**
- EWJ - Japan ETF
- EWZ - Brazil ETF
- FXI - China ETF

### Fallback Behavior

If Yahoo Finance is unavailable or the ticker is invalid:
- The app will display a warning message
- It will fall back to simulated sample data
- Your indicator testing will still work

### Data Quality

**What You Get:**
- ✅ Real historical prices
- ✅ Actual trading volumes
- ✅ Adjusted for splits and dividends
- ✅ Up-to-date data (refreshes on each run)

**Limitations:**
- Daily data only (no intraday)
- Subject to Yahoo Finance API availability
- Free tier has rate limits
- Some international tickers may not be available

### Customization

#### Change Default Ticker

In `R/code_executor.R`, modify:
```r
load_sample_data <- function(symbol = "YOUR_TICKER", days = 500) {
  # ...
}
```

#### Change History Length

```r
# Get 1 year of data
market_data <- load_sample_data(symbol = "SPY", days = 252)

# Get 2 years of data
market_data <- load_sample_data(symbol = "SPY", days = 504)

# Get 5 years of data
market_data <- load_sample_data(symbol = "SPY", days = 1260)
```

#### Use Multiple Tickers

To test on multiple stocks, modify the execution function:

```r
tickers <- c("AAPL", "MSFT", "GOOGL")
results <- lapply(tickers, function(ticker) {
  execute_indicator_code(code, symbol = ticker)
})
```

### Troubleshooting

**"Error loading data from Yahoo Finance"**
- Check your internet connection
- Verify the ticker symbol is correct
- Try a common ticker like "SPY" to test
- The app will use simulated data as fallback

**Data looks wrong**
- Yahoo Finance adjusts for splits/dividends
- Make sure you're looking at adjusted close prices
- Check the date range is correct

**Missing data for recent days**
- Market holidays won't have data
- Weekends are excluded
- Some international markets have different hours

**Rate limiting**
- Yahoo Finance may rate limit excessive requests
- Wait a few minutes between large data downloads
- Consider caching data if testing repeatedly

### Advanced: Caching Data

To avoid repeated downloads:

```r
# Create a simple cache
cache_data <- list()

load_sample_data <- function(symbol = "SPY", days = 500) {
  cache_key <- paste(symbol, days, sep = "_")
  
  if (!is.null(cache_data[[cache_key]])) {
    cat("Using cached data\n")
    return(cache_data[[cache_key]])
  }
  
  # Download and cache
  data <- # ... download logic ...
  cache_data[[cache_key]] <<- data
  return(data)
}
```

### Using Your Own Data Source

If you prefer a different data source:

1. Replace `load_sample_data()` in `R/code_executor.R`
2. Maintain the same output format:
   - Date (Date object)
   - Open (numeric)
   - High (numeric)
   - Low (numeric)
   - Close (numeric)
   - Volume (numeric)

Example with CSV:
```r
load_sample_data <- function(symbol = "SPY", days = 500) {
  df <- read.csv("data/my_data.csv")
  df$Date <- as.Date(df$Date)
  tail(df, days)  # Get last N days
}
```

Example with database:
```r
load_sample_data <- function(symbol = "SPY", days = 500) {
  library(DBI)
  con <- dbConnect(...)
  df <- dbGetQuery(con, sprintf(
    "SELECT * FROM prices WHERE ticker='%s' ORDER BY date DESC LIMIT %d",
    symbol, days
  ))
  dbDisconnect(con)
  return(df)
}
```

## Installation Note

The `quantmod` package is now included in `install_packages.R`. If you already ran the installation, add it manually:

```r
install.packages("quantmod")
```

## Testing

To verify Yahoo Finance integration:

```r
# Test manually
library(quantmod)
data <- getSymbols("SPY", src = "yahoo", auto.assign = FALSE)
head(data)

# Or run the test suite
source("tests/test_indicator.R")
```

The app will show download messages in the R console when fetching data.

Enjoy backtesting with real market data! 📈



