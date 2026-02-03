# Configuration Template
# 
# SETUP INSTRUCTIONS:
# 1. Copy this file to config.R (in the project root)
# 2. Replace "sk-your-api-key-here" with your actual OpenAI API key
# 3. DO NOT commit config.R to git (it's already in .gitignore)

# OpenAI API Configuration
OPENAI_API_KEY <- "sk-your-api-key-here"
OPENAI_MODEL <- "gpt-4-turbo"  # Options: "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"

# Application Settings
MAX_CONVERSATION_HISTORY <- 10  # Number of messages to keep in context
API_TIMEOUT <- 60  # Seconds

# Backtesting Settings
ANNUAL_TRADING_DAYS <- 252
RISK_FREE_RATE <- 0.02  # 2% annual risk-free rate


