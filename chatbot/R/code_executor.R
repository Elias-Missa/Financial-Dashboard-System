# Code Executor
# Safely executes generated R and Python code and produces CSV output

#' Main dispatcher - routes to R or Python executor
#'
#' @param code Code string to execute (R or Python)
#' @param symbol Stock ticker symbol for Yahoo Finance (default: "SPY")
#' @param indicator_name Name of the indicator (optional)
#' @param language Language of the code ("r" or "python")
#' @param start_date Start date for data (optional)
#' @param end_date End date for data (optional)
#' @return List with success status, output path, and any errors
execute_indicator_code <- function(code, symbol = "SPY", indicator_name = "", language = "r", 
                                   start_date = NULL, end_date = NULL) {
  if (language == "python") {
    return(execute_python_code(code, symbol, indicator_name, start_date, end_date))
  } else {
    return(execute_r_code(code, symbol, indicator_name, start_date, end_date))
  }
}

#' Execute R code
#'
#' @param code R code string to execute
#' @param symbol Stock ticker symbol for Yahoo Finance
#' @param indicator_name Name of the indicator
#' @param start_date Start date for data
#' @param end_date End date for data
#' @return List with success status, output path, and any errors
execute_r_code <- function(code, symbol, indicator_name, start_date = NULL, end_date = NULL) {
  # Try to execute everything with error handling
  result <- tryCatch({
    
    # Create output directory if it doesn't exist
    if (!dir.exists("output")) {
      dir.create("output", recursive = TRUE)
      cat("Created output directory\n")
    }
    
    # Generate indicator name if not provided
    if (nchar(indicator_name) == 0 || is.null(indicator_name)) {
      indicator_name <- paste0("indicator_", format(Sys.time(), "%Y%m%d%H%M%S"))
    }
    
    # Clean indicator name (remove special characters)
    indicator_name <- gsub("[^A-Za-z0-9_-]", "_", indicator_name)
    indicator_name <- gsub("^_+|_+$", "", indicator_name)  # Remove leading/trailing underscores
    
    # Final validation
    if (nchar(indicator_name) == 0) {
      indicator_name <- "indicator"
    }
    
    cat("✓ Using indicator name:", indicator_name, "\n")
    
    # Save code file with name and timestamp
    timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
    code_file <- paste0("output/code/", indicator_name, "_", timestamp, ".R")
    writeLines(code, code_file)
    cat("✓ Code saved to:", code_file, "\n")
    
    # Create a safe execution environment
    exec_env <- new.env()
    
    # Make indicator name available to the code
    exec_env$INDICATOR_NAME <- indicator_name
    
    # Set default dates for signal generation
    exec_env$DEFAULT_START_DATE <- as.Date("2010-01-01")
    exec_env$DEFAULT_END_DATE <- Sys.Date()
    
    # Load data_loader functions into execution environment
    source("R/data_loader.R", local = TRUE)
    exec_env$load_market_data <- load_market_data
    exec_env$load_multiple_symbols <- load_multiple_symbols
    exec_env$get_sector_etf <- get_sector_etf
    
    # Execute the code in the isolated environment
    eval(parse(text = code), envir = exec_env)
    
    # Find the generated CSV file - try multiple patterns
    patterns <- c(
      paste0("^", indicator_name, "_.*\\.csv$"),  # With timestamp
      paste0("^", indicator_name, "\\.csv$"),      # Without timestamp  
      "^indicator_data\\.csv$",                     # Fallback old name
      ".*\\.csv$"                                   # Any CSV (last resort)
    )
    
    output_path <- NULL
    for (pattern in patterns) {
      csv_files <- list.files("output/csv", pattern = pattern, full.names = TRUE)
      if (length(csv_files) > 0) {
        csv_files <- csv_files[order(file.mtime(csv_files), decreasing = TRUE)]
        output_path <- csv_files[1]
        cat("✓ Found CSV using pattern:", pattern, "->", basename(output_path), "\n")
        break
      }
    }
    
    if (is.null(output_path)) {
      return(list(
        success = FALSE,
        output_path = NULL,
        error = "Code executed but did not generate any CSV file. Make sure to save output with write.csv()."
      ))
    }
    
    if (file.exists(output_path)) {
      # Read the CSV to validate Signal column (flexible validation)
      indicator_data <- read.csv(output_path)
      if ("Signal" %in% names(indicator_data)) {
        if (!is.numeric(indicator_data$Signal)) {
          return(list(
            success = FALSE,
            output_path = NULL,
            error = "Signal column must be numeric. Please use numeric values only."
          ))
        }
        # Log signal range for debugging
        cat("✓ Signal range:", min(indicator_data$Signal, na.rm=TRUE), "to", 
            max(indicator_data$Signal, na.rm=TRUE), "\n")
      }
      
      list(
        success = TRUE,
        output_path = output_path,
        error = NULL
      )
    } else {
      list(
        success = FALSE,
        output_path = NULL,
        error = "Code executed but did not generate the expected CSV file"
      )
    }
    
  }, error = function(e) {
    list(
      success = FALSE,
      output_path = NULL,
      error = as.character(e$message)
    )
  })
  
  return(result)
}

#' Execute Python code
#'
#' @param code Python code string to execute
#' @param symbol Stock ticker symbol for Yahoo Finance
#' @param indicator_name Name of the indicator
#' @param start_date Start date for data
#' @param end_date End date for data
#' @return List with success status, output path, and any errors
execute_python_code <- function(code, symbol, indicator_name, start_date = NULL, end_date = NULL) {
  tryCatch({
    # Setup
    timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
    if (nchar(indicator_name) == 0 || is.null(indicator_name)) {
      indicator_name <- paste0("indicator_", timestamp)
    }
    
    # Clean and validate indicator name
    indicator_name <- gsub("[^A-Za-z0-9_-]", "_", indicator_name)
    indicator_name <- gsub("^_+|_+$", "", indicator_name)
    if (nchar(indicator_name) == 0) {
      indicator_name <- "indicator"
    }
    
    cat("✓ Using indicator name:", indicator_name, "\n")
    
    # Create output directory if needed
    if (!dir.exists("output")) {
      dir.create("output", recursive = TRUE)
    }
    
    # Save Python script
    py_file <- paste0("output/code/", indicator_name, "_", timestamp, ".py")
    writeLines(code, py_file)
    cat("✓ Python code saved to:", py_file, "\n")
    
    # Expected output CSV
    output_csv <- paste0("output/csv/", indicator_name, "_", timestamp, ".csv")
    
    # Set environment variables for Python script
    Sys.setenv(
      OUTPUT_CSV = normalizePath(output_csv, mustWork = FALSE, winslash = "/"),
      INDICATOR_NAME = indicator_name
    )
    
    # Ensure yfinance is installed
    cat("Checking for yfinance package...\n")
    system2("python", args = c("-m", "pip", "install", "yfinance", "-q"), 
            stdout = FALSE, stderr = FALSE)
    
    # Execute Python script
    cat("Executing Python script...\n")
    result <- system2(
      "python",
      args = c(py_file),
      stdout = TRUE,
      stderr = TRUE
    )
    
    # Print Python output
    if (length(result) > 0) {
      cat("Python output:\n", paste(result, collapse = "\n"), "\n")
    }
    
    # Check if output was created
    if (file.exists(output_csv)) {
      # Validate output (flexible validation)
      indicator_data <- read.csv(output_csv)
      if ("Signal" %in% names(indicator_data)) {
        if (!is.numeric(indicator_data$Signal)) {
          return(list(success = FALSE, output_path = NULL,
                     error = "Signal column must be numeric"))
        }
        # Log signal range
        cat("✓ Signal range:", min(indicator_data$Signal, na.rm=TRUE), "to", 
            max(indicator_data$Signal, na.rm=TRUE), "\n")
      }
      
      return(list(success = TRUE, output_path = output_csv, error = NULL))
    } else {
      return(list(success = FALSE, output_path = NULL,
                 error = paste("Python script did not create output file. Output:", 
                              paste(result, collapse = "\n"))))
    }
  }, error = function(e) {
    return(list(success = FALSE, output_path = NULL, error = as.character(e$message)))
  })
}

#' Load market data from Yahoo Finance
#' @param symbol Stock ticker symbol (default: "SPY")
#' @param days Number of days of historical data (default: 500)
#' @return Dataframe with Date, Open, High, Low, Close, Volume
load_sample_data <- function(symbol = "SPY", days = 500) {
  library(quantmod)
  
  end_date <- Sys.Date()
  start_date <- end_date - days
  
  tryCatch({
    cat(sprintf("Downloading %s data from Yahoo Finance...\n", symbol))
    
    data <- getSymbols(symbol, 
                      src = "yahoo", 
                      from = start_date, 
                      to = end_date, 
                      auto.assign = FALSE)
    
    df <- data.frame(
      Date = index(data),
      Open = as.numeric(Op(data)),
      High = as.numeric(Hi(data)),
      Low = as.numeric(Lo(data)),
      Close = as.numeric(Cl(data)),
      Volume = as.numeric(Vo(data)),
      stringsAsFactors = FALSE
    )
    
    cat(sprintf("✓ Successfully loaded %d days of %s data\n", nrow(df), symbol))
    return(df)
    
  }, error = function(e) {
    cat(sprintf("⚠ Error loading data from Yahoo Finance: %s\n", e$message))
    cat("Falling back to sample data...\n")
    
    # Fallback to simulated data
    n_days <- days
    dates <- seq(end_date - n_days, end_date, by = "day")
    set.seed(123)
    close_prices <- cumsum(rnorm(length(dates), mean = 0.1, sd = 2)) + 100
    
    return(data.frame(
      Date = dates,
      Open = close_prices + rnorm(length(dates), 0, 0.5),
      High = close_prices + abs(rnorm(length(dates), 1, 0.5)),
      Low = close_prices - abs(rnorm(length(dates), 1, 0.5)),
      Close = close_prices,
      Volume = round(runif(length(dates), 1000000, 10000000)),
      stringsAsFactors = FALSE
    ))
  })
}
