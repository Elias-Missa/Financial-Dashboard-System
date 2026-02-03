#!/usr/bin/env Rscript
# Market Cipher AI Chatbot Launcher
# Open this file in RStudio and click "Source" or run line-by-line

cat("\n")
cat("========================================\n")
cat("  Market Cipher AI Chatbot Launcher    \n")
cat("========================================\n\n")

# Step 1: Install packages if needed
cat("Step 1: Checking required packages...\n")
required_packages <- c("shiny", "bslib", "httr2", "jsonlite", "shinycssloaders", "shinyjs", "quantmod")

for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    cat(paste("  Installing", pkg, "...\n"))
    install.packages(pkg, dependencies = TRUE, repos = "https://cran.rstudio.com/")
  } else {
    cat(paste("  ✓", pkg, "\n"))
  }
}

cat("\n")

# Step 2: Check API key
cat("Step 2: Checking OpenAI API key...\n")
source("R/api_client.R")
if (OPENAI_API_KEY == "sk-your-api-key-here") {
  cat("  ⚠ WARNING: Please add your OpenAI API key to R/api_client.R\n")
  cat("  The app will not work without a valid API key.\n\n")
} else if (nchar(OPENAI_API_KEY) > 20) {
  cat("  ✓ API key found\n\n")
} else {
  cat("  ⚠ WARNING: API key looks invalid\n\n")
}

# Step 3: Launch app
cat("Step 3: Launching Market Cipher AI Chatbot...\n")
cat("  The app will open in your default web browser.\n")
cat("  Press Ctrl+C or click the STOP button to close the app.\n\n")

Sys.sleep(2)

# Launch!
shiny::runApp(launch.browser = TRUE)












