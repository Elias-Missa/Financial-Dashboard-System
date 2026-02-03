# Integration Guide: Adding AI Signal Generator to Your Existing R Shiny Project

This guide shows how to integrate the Market Cipher AI Signal Generator into your existing R Shiny dashboard.

## Option 1: As a Separate Tab (Recommended)

### Step 1: Copy Files

Copy these files to your existing project:
```
your-project/
├── modules/
│   ├── signal_generator_module.R  # (create this - see below)
│   └── ...
├── R/
│   ├── api_client.R              # Copy from this project
│   ├── code_executor.R           # Copy from this project
│   └── data_loader.R             # Copy from this project
├── output/
│   ├── code/                     # Create this folder
│   └── csv/                      # Create this folder
```

### Step 2: Create Signal Generator Module

Create `modules/signal_generator_module.R`:

```r
# Signal Generator UI Module
signal_generator_ui <- function(id) {
  ns <- NS(id)
  
  tagList(
    # ... copy UI elements from app.R ...
    # Focus on signal input and results display
  )
}

# Signal Generator Server Module
signal_generator_server <- function(id) {
  moduleServer(id, function(input, output, session) {
    # ... copy server logic from app.R ...
    # Include signal generation and CSV output
  })
}
```

### Step 3: Add to Your Main App

In your existing `app.R` or `ui.R`:

```r
# Add to UI
tabPanel("AI Signal Generator",
  signal_generator_ui("signals")
)

# Add to server
signal_generator_server("signals")
```

## Option 2: As a Standalone Component

Keep the signal generator as a separate app and:

1. **Run both apps** on different ports:
   ```r
   # Main app on port 3838
   shiny::runApp("main-app/", port = 3838)
   
   # Signal generator on port 3839
   shiny::runApp("signal-generator/", port = 3839)
   ```

2. **Link between apps** using navigation buttons or iframes
3. **Share output folder** - point both apps to same `output/csv/` directory

## Option 3: Use Generated Signals in Your Analysis

### Reading Generated Signal CSVs

All signals are saved to `output/csv/` with standardized format:

```r
# In your analysis code
read_signal <- function(signal_name) {
  # Find most recent signal CSV
  files <- list.files("output/csv", 
                     pattern = paste0(signal_name, "_.*\\.csv$"), 
                     full.names = TRUE)
  
  if (length(files) == 0) {
    stop("Signal not found")
  }
  
  # Get most recent
  latest <- files[which.max(file.mtime(files))]
  signal_data <- read.csv(latest)
  
  return(signal_data)
}

# Use in your strategy
spy_ma_signal <- read_signal("spy_30day_ma")
```

### Signal CSV Format

All generated CSVs have consistent structure:
- **Date**: Trading date (Date type)
- **Signal**: Numeric value (continuous) or binary (0/1)
- No NA values (cleaned automatically)
- Date range: 2010-01-01 to present

### Integrating with Your Trading System

```r
# Example: Use signal for position sizing
signal_data <- read_signal("market_regime")

# Merge with your positions
positions <- merge(your_positions, signal_data, by = "Date")

# Apply signal to sizing
positions$final_size <- positions$base_size * positions$Signal

# Execute trades
execute_trades(positions)
```

## Sharing State Between Components

If you need to share signal data between the generator and your main dashboard:

```r
# In your main server function
shared_data <- reactiveValues(
  signal_csv_path = NULL,
  signal_data = NULL,
  last_generated = NULL
)

# Pass to signal generator module
signal_generator_server("signals", shared_data)

# Access in other modules
observeEvent(shared_data$signal_csv_path, {
  # React to new signal generation
  new_signal <- read.csv(shared_data$signal_csv_path)
  # Update your analysis
})
```

## Dependencies

Add these to your existing package requirements:

```r
required_packages <- c(
  # Your existing packages
  "shiny", "shinydashboard", ...,
  
  # Add these for chatbot
  "bslib",
  "httr2",
  "jsonlite",
  "shinyjs",
  "shinycssloaders"
)
```

## API Key Management

For production, use environment variables instead of hardcoding:

```r
# In R/api_client.R
OPENAI_API_KEY <- Sys.getenv("OPENAI_API_KEY")

if (OPENAI_API_KEY == "") {
  stop("Please set OPENAI_API_KEY environment variable")
}
```

Then set the environment variable:
```r
# In .Renviron file
OPENAI_API_KEY=sk-your-actual-key-here
```

## Styling Consistency

To match your existing dashboard theme:

1. Copy your current theme settings to the chatbot
2. Or modify the chatbot theme in `app.R`:
   ```r
   theme = bs_theme(
     version = 5,
     bootswatch = "your-current-theme",
     primary = "your-primary-color",
     ...
   )
   ```

## Performance Considerations

- **Async Processing**: For complex multi-symbol signals, consider using `future` and `promises` packages
- **Caching**: Data loader automatically caches Yahoo Finance data for 24 hours
- **Rate Limiting**: Implement request throttling for OpenAI API if generating many signals
- **Data Downloads**: First signal generation may be slow while fetching historical data

## Example: Minimal Integration

Here's a minimal example to add signal generator to existing app:

```r
# In your existing UI
navbarPage("Your Dashboard",
  tabPanel("Overview", ...),
  tabPanel("Signals", ...),
  tabPanel("AI Signal Generator",  # NEW TAB
    source("app.R", local = TRUE)$value
  )
)
```

## Testing Integration

1. Start with the standalone signal generator
2. Test simple signals first (single symbol, basic calculations)
3. Verify CSV output format matches your needs
4. Test multi-symbol signals (ratios, sector comparisons)
5. Test binary rule-based signals
6. Integrate one component at a time
7. Test thoroughly before deploying

## CSV Output Examples

### Continuous Signal
```csv
Date,Signal
2023-01-01,0.452
2023-01-02,0.458
2023-01-03,0.461
```

### Binary Signal
```csv
Date,Signal
2023-01-01,0
2023-01-02,0
2023-01-03,1
```

## Using Signals in Backtesting

If you have your own backtesting system:

```r
# Read signal
signal_data <- read.csv("output/csv/your_signal_20241027_123456.csv")

# Convert to xts or your format
library(xts)
signal_xts <- xts(signal_data$Signal, order.by = as.Date(signal_data$Date))

# Use in your backtest
backtest_results <- your_backtest_function(
  signals = signal_xts,
  prices = your_price_data,
  ...
)
```

## Need Custom Features?

Common customizations:
- Multiple signal outputs in one request
- Custom date ranges
- Different output formats (JSON, Parquet, database)
- Integration with databases
- Real-time data feeds
- Custom data sources beyond Yahoo Finance

Modify the relevant R files to suit your specific needs:
- `R/api_client.R`: Modify system prompts for different signal types
- `R/data_loader.R`: Add custom data sources
- `R/code_executor.R`: Change output formats or validation

## Troubleshooting

**Issue**: Signal CSV not found  
**Solution**: Check `output/csv/` directory exists and code executed successfully

**Issue**: Data download fails  
**Solution**: Yahoo Finance may be down; check internet connection or use cached data

**Issue**: Multi-symbol signal errors  
**Solution**: Ensure all requested symbols are available on Yahoo Finance

**Issue**: Date ranges don't match  
**Solution**: Different symbols may have different trading calendars; AI will handle merging


