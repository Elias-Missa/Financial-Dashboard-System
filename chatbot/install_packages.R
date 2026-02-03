# Install Required Packages for Market Cipher AI Chatbot
# Run this script once before running the app

cat("Installing required packages for Market Cipher AI Chatbot...\n\n")

# List of required packages
required_packages <- c(
  "shiny",
  "bslib",
  "httr2",
  "jsonlite",
  "shinycssloaders",
  "shinyjs",
  "quantmod"  # For Yahoo Finance data
)

# Function to install if not already installed
install_if_missing <- function(package) {
  if (!require(package, character.only = TRUE, quietly = TRUE)) {
    cat(paste("Installing", package, "...\n"))
    install.packages(package, dependencies = TRUE)
  } else {
    cat(paste("✓", package, "already installed\n"))
  }
}

# Install all required packages
for (pkg in required_packages) {
  install_if_missing(pkg)
}

cat("\n✓ All packages installed successfully!\n")
cat("\nNext steps:\n")
cat("1. Open R/api_client.R and add your OpenAI API key\n")
cat("2. Run the app with: shiny::runApp('app.R')\n")

