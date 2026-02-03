# Run Guide

## Backtest (Python)

**GUI:**
```powershell
cd backtest
python run_backtest.py
```

**CLI:**
```powershell
cd backtest
python backtest.py --ticker SPY --strategy strategy1 --start_date 2020-01-01 --end_date 2023-12-31
```

Add `--no-plot` to run without opening the chart window.

---

## Chatbot (R Shiny)

```powershell
cd chatbot
& "C:\Program Files\R\R-4.5.1\bin\Rscript.exe" run_app.R
```

Or in R/RStudio:
```r
setwd("chatbot")
source("run_app.R")
```

**Note:** Requires `config.R` with your OpenAI API key (copy from `config.example.R`).
