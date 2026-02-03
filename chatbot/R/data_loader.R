# Data Loader Module
# Centralized Yahoo Finance data loading with caching

#' Load market data with date range and caching
#' 
#' @param symbol Stock ticker symbol (e.g., "SPY", "AAPL")
#' @param start_date Start date (default: 500 days ago)
#' @param end_date End date (default: today)
#' @param use_cache Whether to use cached data (default: TRUE)
#' @return Dataframe with Date, Open, High, Low, Close, Volume columns
#' @export
load_market_data <- function(symbol = "SPY", 
                             start_date = NULL, 
                             end_date = NULL,
                             use_cache = TRUE) {
  library(quantmod)
  
  # Set default dates
  if (is.null(end_date)) end_date <- Sys.Date()
  if (is.null(start_date)) start_date <- end_date - 500
  
  # Ensure start_date and end_date are Date objects
  if (!inherits(start_date, "Date")) start_date <- as.Date(start_date)
  if (!inherits(end_date, "Date")) end_date <- as.Date(end_date)
  
  # Create cache directory if it doesn't exist
  if (!dir.exists("data")) {
    dir.create("data", recursive = TRUE)
  }
  
  # Check cache
  cache_key <- paste0(symbol, "_", start_date, "_", end_date)
  cache_file <- file.path("data", paste0("cache_", cache_key, ".rds"))
  
  if (use_cache && file.exists(cache_file)) {
    age_hours <- as.numeric(difftime(Sys.time(), file.mtime(cache_file), units = "hours"))
    if (age_hours < 24) {  # Cache valid for 24 hours
      cat("ℹ Using cached data for", symbol, "(age:", round(age_hours, 1), "hours)\n")
      return(readRDS(cache_file))
    } else {
      cat("ℹ Cache expired, downloading fresh data...\n")
    }
  }
  
  # Download fresh data from Yahoo Finance
  tryCatch({
    cat(sprintf("Downloading %s data from %s to %s...\n", symbol, start_date, end_date))
    
    data <- getSymbols(symbol, 
                      src = "yahoo", 
                      from = start_date, 
                      to = end_date, 
                      auto.assign = FALSE)
    
    if (is.null(data) || nrow(data) == 0) {
      stop("No data returned from Yahoo Finance")
    }
    
    # Convert to dataframe
    df <- data.frame(
      Date = index(data),
      Open = as.numeric(Op(data)),
      High = as.numeric(Hi(data)),
      Low = as.numeric(Lo(data)),
      Close = as.numeric(Cl(data)),
      Volume = as.numeric(Vo(data)),
      stringsAsFactors = FALSE
    )
    
    # Cache the data
    saveRDS(df, cache_file)
    
    cat(sprintf("✓ Successfully loaded %d days of %s data\n", nrow(df), symbol))
    return(df)
    
  }, error = function(e) {
    cat(sprintf("✗ Error loading data from Yahoo Finance: %s\n", e$message))
    cat("ℹ Falling back to sample data...\n")
    
    # Fallback to simulated data
    n_days <- as.numeric(difftime(end_date, start_date, units = "days"))
    dates <- seq(start_date, end_date, by = "day")
    set.seed(123)
    close_prices <- cumsum(rnorm(length(dates), mean = 0.1, sd = 2)) + 100
    
    df <- data.frame(
      Date = dates,
      Open = close_prices + rnorm(length(dates), 0, 0.5),
      High = close_prices + abs(rnorm(length(dates), 1, 0.5)),
      Low = close_prices - abs(rnorm(length(dates), 1, 0.5)),
      Close = close_prices,
      Volume = round(runif(length(dates), 1000000, 10000000)),
      stringsAsFactors = FALSE
    )
    
    return(df)
  })
}

#' Clear data cache
#' 
#' @param symbol Optional: specific symbol to clear. If NULL, clears all cache
#' @export
clear_data_cache <- function(symbol = NULL) {
  if (!dir.exists("data")) {
    cat("No cache directory found\n")
    return(invisible(NULL))
  }
  
  if (is.null(symbol)) {
    # Clear all cache
    cache_files <- list.files("data", pattern = "^cache_.*\\.rds$", full.names = TRUE)
    if (length(cache_files) > 0) {
      file.remove(cache_files)
      cat("✓ Cleared", length(cache_files), "cached files\n")
    } else {
      cat("No cached files to clear\n")
    }
  } else {
    # Clear specific symbol cache
    pattern <- paste0("^cache_", symbol, "_.*\\.rds$")
    cache_files <- list.files("data", pattern = pattern, full.names = TRUE)
    if (length(cache_files) > 0) {
      file.remove(cache_files)
      cat("✓ Cleared", length(cache_files), "cached files for", symbol, "\n")
    } else {
      cat("No cached files found for", symbol, "\n")
    }
  }
  
  invisible(NULL)
}

#' Load multiple symbols at once
#' 
#' @param symbols Character vector of symbols to load
#' @param start_date Start date (default: 2010-01-01)
#' @param end_date End date (default: today)
#' @param use_cache Whether to use cached data (default: TRUE)
#' @return Named list of dataframes, one per symbol
#' @export
load_multiple_symbols <- function(symbols, start_date = NULL, end_date = NULL, use_cache = TRUE) {
  result <- list()
  for (symbol in symbols) {
    cat("Loading", symbol, "...\n")
    result[[symbol]] <- load_market_data(symbol, start_date, end_date, use_cache)
  }
  return(result)
}

#' Get sector ETF symbol from sector name
#' 
#' @param sector_name Name of the sector (e.g., "Utilities", "Technology")
#' @return ETF ticker symbol for that sector
#' @export
get_sector_etf <- function(sector_name) {
  sector_map <- list(
    "Utilities" = "XLU", 
    "Financials" = "XLF", 
    "Technology" = "XLK",
    "Healthcare" = "XLV", 
    "Energy" = "XLE", 
    "Consumer Discretionary" = "XLY",
    "Consumer Staples" = "XLP", 
    "Industrials" = "XLI", 
    "Materials" = "XLB",
    "Real Estate" = "XLRE", 
    "Communication" = "XLC"
  )
  
  result <- sector_map[[sector_name]]
  if (is.null(result)) {
    stop("Unknown sector: ", sector_name, ". Available sectors: ", 
         paste(names(sector_map), collapse = ", "))
  }
  return(result)
}


