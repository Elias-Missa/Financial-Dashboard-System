# Quick Start Guide

Get up and running with Market Cipher AI Chatbot in 5 minutes.

## Step 1: Install R Packages (2 minutes)

Open R or RStudio and run:

```r
source("install_packages.R")
```

This will install all required dependencies.

## Step 2: Configure OpenAI API Key (1 minute)

1. Open the file `R/api_client.R`
2. Find line 4:
   ```r
   OPENAI_API_KEY <- "sk-your-api-key-here"
   ```
3. Replace `"sk-your-api-key-here"` with your actual OpenAI API key
4. Save the file

⚠️ **Security Note**: Never commit your API key to version control!

## Step 3: Run the App (30 seconds)

In R or RStudio, run:

```r
source("run_app.R")
```

Or simply:

```r
shiny::runApp("app.R")
```

The app will open in your default web browser.

## Step 4: Choose Your Signal Type (30 seconds)

Understanding signal types:
- **Continuous Signals**: Numeric values like ratios, moving averages, VIX levels
- **Binary Signals**: Rule-based 0/1 values for specific conditions

## Step 5: Test It Out (1 minute)

Try one of these example prompts:

**Continuous Signal Example:**
```
Calculate the ratio of Nasdaq to S&P 500
```

**Binary Signal Example:**
```
Binary signal when RSI > 80 AND SPX is at a 255-day high
```

**Moving Average Example:**
```
Generate a 30-day simple moving average of SPY
```

## What to Expect

1. **Chat**: Type your request and click "Send"
2. **AI Response**: The AI will determine what data is needed and generate R or Python code
3. **Code Preview**: Review the code in the right panel
4. **Confirm**: Click "Confirm & Execute" to run the code
5. **Results**: View success message with CSV and code file paths

## Troubleshooting

**"Package not found" error:**
```r
install.packages("package_name")
```

**API call fails:**
- Check your API key in `R/api_client.R`
- Verify your OpenAI account has API access
- Check your internet connection

**Code execution fails:**
- The AI might need more specific instructions
- Click "Reject & Revise" and provide more details

## Next Steps

- See `example_prompts.md` for more prompt ideas
- Read `README.md` for full documentation
- Customize styling in `app.R` CSS section
- Integrate with your existing R Shiny project

## Need Help?

- Review the code comments in each file
- Check the system prompt in `R/api_client.R`
- Modify the backtesting logic in `R/backtester.R` to match your needs

Happy backtesting! 📈


