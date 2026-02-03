# Quick launcher for Market Cipher AI Chatbot
# Run this file to start the application

# Check if packages are installed
required_packages <- c("shiny", "bslib", "httr2", "jsonlite", "shinycssloaders", "shinyjs", "quantmod")

missing_packages <- required_packages[!sapply(required_packages, requireNamespace, quietly = TRUE)]

if (length(missing_packages) > 0) {
  cat("Missing required packages:", paste(missing_packages, collapse = ", "), "\n")
  cat("Please run install_packages.R first:\n")
  cat("  source('install_packages.R')\n")
  stop("Missing required packages")
}

# Check if API key is configured
if (!file.exists("R/api_client.R")) {
  stop("R/api_client.R not found. Please ensure the file exists.")
}

# Launch the app
cat("Starting Market Cipher AI Chatbot...\n")
cat("The app will open in your default web browser.\n")
cat("Press Ctrl+C to stop the server.\n\n")

shiny::runApp(launch.browser = TRUE)


