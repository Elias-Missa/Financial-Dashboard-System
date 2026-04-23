# Financial Dashboard System

A full-stack financial analytics platform that unifies **machine learning predictions**, **trading-strategy backtesting**, and an **AI signal-generation chatbot** behind a single modern web dashboard.

The system tracks the S&P 500, generates ML-driven price forecasts, lets users run 30+ backtested trading strategies, and provides an OpenAI-powered chat assistant for ad-hoc financial analysis and signal creation.

---

## Table of Contents

1. [System Description](#system-description)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Project Structure](#project-structure)
5. [Required Dependencies](#required-dependencies)
6. [Installation & Setup](#installation--setup)
7. [Running the System](#running-the-system)
8. [Deployment Instructions](#deployment-instructions)
9. [API Reference](#api-reference)
10. [Configuration](#configuration)
11. [Troubleshooting](#troubleshooting)

---

## System Description

The Financial Dashboard System is composed of four cooperating sub-systems:

| Component | Tech Stack | Purpose |
|-----------|-----------|---------|
| **Frontend** | React 18, Vite, TailwindCSS, Recharts | Dark-themed dashboard with four tabs (Dashboard / Backtest / ML Config / Chatbot) |
| **API Backend** | FastAPI, Uvicorn | REST API that glues all components together (port 8000) |
| **ML Pipeline** | scikit-learn, PyTorch, pandas, MongoDB Atlas | Feature engineering, training, walk-forward evaluation, and Ridge-regression prediction generation |
| **Backtest Engine** | Python, pandas, matplotlib, Tkinter | 30+ long/short trading strategies with full performance metrics |
| **AI Signal Chatbot** | R Shiny, OpenAI GPT-4o, quantmod | Standalone R Shiny app for natural-language signal/indicator generation |

The web dashboard is the primary entry point. The R Shiny chatbot is a standalone tool that generates R/Python signal code on demand and persists it to disk for use in the backtester or other workflows.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      React Frontend (Vite)                     │
│                     http://localhost:5173                      │
│                                                                │
│   ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐     │
│   │Dashboard │  │ Backtest │  │ ML Config  │  │ Chatbot  │     │
│   └────┬─────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘     │
└────────┼─────────────┼──────────────┼──────────────┼───────────┘
         │             │              │              │
         ▼             ▼              ▼              ▼
┌────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                 │
│                                                                │
│   /api/market/*    → yfinance + cache + MongoDB                │
│   /api/ml/*        → Ridge regression / training pipeline      │
│   /api/backtest/*  → 30+ strategies in backtest/strategies/    │
│   /api/chatbot/*   → OpenAI GPT-4o                             │
│   /api/health      → Health check                              │
└────────┬─────────────┬──────────────┬──────────────┬───────────┘
         │             │              │              │
         ▼             ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐
   │ yfinance │  │ backtest │  │  ML / DL   │  │  OpenAI  │
   │ + FRED   │  │ engine   │  │  models    │  │   API    │
   └──────────┘  └──────────┘  └─────┬──────┘  └──────────┘
                                     ▼
                              ┌──────────────┐
                              │ MongoDB Atlas│
                              │ (OHLCV /     │
                              │  features /  │
                              │  predictions)│
                              └──────────────┘

         ┌────────────────────────────────────────────┐
         │   Standalone R Shiny App (chatbot/app.R)   │
         │   Generates signal code via GPT-4o         │
         │   Outputs CSV + R/Python files to disk     │
         └────────────────────────────────────────────┘
```

---

## Features

### Web Dashboard (`frontend/`)

- **Dashboard tab** — Live SPY price chart with overlaid ML predictions (gray = historical, green = predicted), six market stat cards (SPY price, daily change, VIX, 200-day MA distance, YTD return, 52-week range, ML 21-day forecast), and a one-click "Generate Predictions" button.
- **Backtest tab** — Strategy selector (30+ long/short strategies), date range, initial capital, and slippage controls. Returns full performance metrics (CAGR, Sharpe, Max Drawdown, Win Rate, Profit Factor, Volatility), an equity curve chart, and monthly-returns table.
- **ML Config tab** — Edit hyperparameters and feature flags for the ML training pipeline directly from the UI; persisted to `machine_learning/ML/config_overrides.json`.
- **Chatbot tab** — GPT-4o powered chat assistant with full markdown rendering for financial Q&A.
- **Dark theme** built with Tailwind's slate palette, Inter font, sidebar navigation, loading skeletons, and inline error banners.

### ML Pipeline (`machine_learning/`)

- 16 engineered features: multi-horizon returns (1d / 5d / 21d / 63d), 50/200-day MA distance & slope, 20/60-day volatility & ratio, RSI-14 / RSI-5, normalized ATR-14, volume ratio, distance from 52-week high, month seasonality.
- Ridge regression (default), with additional model implementations: LSTM, TFT (Temporal Fusion Transformer), classifiers, and ensembles.
- **Walk-forward training and evaluation** with hyperparameter tuning (`tuning.py`), feature selection (`feature_selection.py`), and a sanity-check suite (`sanity_suite.py`).
- **MongoDB Atlas** persistence for OHLCV, engineered features, predictions, and run metadata.
- Yahoo Finance + FRED data ingestion, weekly refresh script (`refresh_data.py`).

### Backtest Engine (`backtest/`)

- 30+ pre-built long and short strategies including RSI variants, IBS mean reversion, momentum, breakout, volatility, and pattern-reversal strategies.
- Full performance reporting: Total Return, CAGR, Sharpe Ratio, Max Drawdown, Win Rate, Profit Factor, Average Trade, Average Win/Loss, Volatility.
- Equity curve and drawdown plots (matplotlib).
- Tkinter GUI (`run_backtest.py`) and command-line interface (`backtest.py`).
- Easily extensible — drop a new file into `backtest/strategies/` implementing `generate_signals(df)`.

### AI Signal Chatbot (`chatbot/`) — R Shiny

- Natural-language signal description → generated R or Python code.
- Automatic Yahoo Finance data fetching for stocks, ETFs, indices (`^GSPC`, `^IXIC`, `^VIX`), and sector ETFs (`XLU`, `XLF`, `XLK`, ...).
- Code preview & confirmation step before execution.
- Continuous and binary signal generation.
- Output saved to `chatbot/output/csv/` and `chatbot/output/code/`.
- Built-in prompt-injection protection, code validation, sandboxed execution, and 24-hour data caching.

---

## Project Structure

```
Financial-Dashboard-System/
├── api/                          # FastAPI backend
│   ├── main.py                   # All routes + ML prediction generator
│   └── requirements.txt
│
├── frontend/                     # React + Vite + Tailwind dashboard
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx               # Tab router & sidebar
│       ├── api.js                # Axios client
│       ├── modelEvents.js
│       └── components/
│           ├── Dashboard.jsx
│           ├── PriceChart.jsx
│           ├── MarketStats.jsx
│           ├── Backtest.jsx
│           ├── MLConfig.jsx
│           ├── ModelResults.jsx
│           └── Chatbot.jsx
│
├── machine_learning/             # ML pipeline + MongoDB integration
│   ├── db.py                     # MongoDB Atlas connection
│   ├── db_helpers.py             # Read/write OHLCV, features, predictions
│   ├── data_loader.py            # yfinance + FRED data ingestion
│   ├── pipeline.py               # Feature engineering entry point
│   ├── refresh_data.py           # Weekly data refresh
│   ├── requirements.txt
│   ├── MONGODB_INTEGRATION_GUIDE.md
│   ├── features/                 # trend, volatility, breadth, cross_asset, macro, sentiment
│   ├── ML/                       # Training & evaluation
│   │   ├── config.py
│   │   ├── train.py
│   │   ├── train_walkforward.py
│   │   ├── models.py
│   │   ├── ensemble.py
│   │   ├── tuning.py
│   │   ├── metrics.py
│   │   ├── sanity_suite.py
│   │   └── transformer/          # TFT model
│   └── Output/                   # Generated CSVs (gitignored)
│
├── backtest/                     # Standalone backtesting engine
│   ├── backtest.py               # CLI engine
│   ├── run_backtest.py           # Tkinter GUI
│   ├── debug_backtest.py
│   ├── requirements.txt
│   ├── README.md
│   ├── strategies/               # 30+ long & short strategies
│   └── utils/
│
├── chatbot/                      # R Shiny AI signal generator
│   ├── app.R
│   ├── run_app.R
│   ├── LAUNCH_APP.R
│   ├── config.example.R
│   ├── install_packages.R
│   ├── R/                        # api_client.R, code_executor.R, data_loader.R
│   ├── output/                   # csv/ and code/
│   └── README.md
│
├── .env                          # MONGODB_URI + OPENAI_API_KEY (gitignored)
├── .env.example                  # Template
├── .gitignore
├── DASHBOARD_CHANGES.md
├── RUN_GUIDE.md
└── README.md                     # This file
```

---

## Required Dependencies

### System

- **Python 3.10+**
- **Node.js 18+** (with npm)
- **R 4.0+** (R 4.5.1 recommended) — only required for the standalone R Shiny chatbot
- **MongoDB Atlas account** *(optional but recommended)* — for persistent ML data storage
- **OpenAI API key** *(optional)* — required only for the chatbot tab and the R Shiny signal generator

### Python (backend + ML + backtest)

Combined from `api/requirements.txt`, `machine_learning/requirements.txt`, and `backtest/requirements.txt`:

```
fastapi
uvicorn[standard]
python-dotenv>=1.0.0
pymongo[srv]
yfinance
pandas
numpy
pandas_datareader
scipy
arch
ta
scikit-learn
torch
matplotlib
openpyxl
openai
```

### Node (frontend)

From `frontend/package.json`:

- **Runtime:** `react@^18.3.1`, `react-dom`, `axios`, `recharts`, `lucide-react`, `react-markdown`
- **Dev:** `vite@^6`, `@vitejs/plugin-react`, `tailwindcss@^3.4`, `postcss`, `autoprefixer`

### R (chatbot only)

```r
install.packages(c(
  "shiny", "bslib", "httr2", "jsonlite",
  "shinycssloaders", "shinyjs", "quantmod"
))
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Financial-Dashboard-System
```

### 2. Configure Environment Variables

Copy the template and fill in your secrets:

```bash
cp .env.example .env
```

Edit `.env`:

```
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority&appName=FinancialDashboard
OPENAI_API_KEY=sk-...
```

> The `.env` file is gitignored. Both variables are optional — the dashboard runs without them, but the chatbot tab and MongoDB persistence will be disabled.

### 3. Set Up the Python Backend

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r api/requirements.txt
pip install -r machine_learning/requirements.txt
pip install -r backtest/requirements.txt
```

### 4. Set Up the Frontend

```bash
cd frontend
npm install
cd ..
```

### 5. (Optional) Set Up the R Shiny Chatbot

```bash
cd chatbot
Rscript install_packages.R
cp config.example.R config.R
# Edit config.R and add your OPENAI_API_KEY
cd ..
```

---

## Running the System

### Start the Backend (FastAPI)

```bash
cd api
python -m uvicorn main:app --port 8000 --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `http://localhost:8000/docs`.

### Start the Frontend (Vite Dev Server)

In a second terminal:

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173** and click **Generate Predictions** on the Dashboard tab to populate the chart.

### Run the Standalone Backtester (CLI)

```bash
cd backtest
python backtest.py --ticker SPY --strategy strategy1 --start_date 2020-01-01 --end_date 2023-12-31
```

Add `--no-plot` to skip the chart window.

### Run the Standalone Backtester (GUI)

```bash
cd backtest
python run_backtest.py
```

### Run the Standalone R Shiny Chatbot

```powershell
cd chatbot
& "C:\Program Files\R\R-4.5.1\bin\Rscript.exe" run_app.R
```

Or from R / RStudio:

```r
setwd("chatbot")
source("run_app.R")
```

### Refresh ML Data Manually

```bash
python machine_learning/refresh_data.py
```

---

## Deployment Instructions

The system is designed for both local development and production deployment.

### Build the Frontend for Production

```bash
cd frontend
npm run build
```

This outputs static assets to `frontend/dist/`. Serve them with any static host (nginx, Caddy, Vercel, Netlify, S3 + CloudFront, etc.).

### Run the Backend in Production

Use a production ASGI server such as `uvicorn` with multiple workers, behind a reverse proxy (nginx / Caddy / Traefik):

```bash
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Suggested Deployment Topologies

| Component | Recommended Host |
|-----------|------------------|
| Frontend (`frontend/dist/`) | Static host (Netlify / Vercel / S3+CloudFront / nginx) |
| Backend (`api/`) | Container on AWS ECS / Fly.io / Railway / Render / a Linux VM with systemd + nginx |
| MongoDB | MongoDB Atlas (managed, free tier available) |
| R Shiny chatbot | shinyapps.io, RStudio Connect, or `Dockerfile` based deployment |

### Example `Dockerfile` for the Backend

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY api/requirements.txt api/requirements.txt
COPY machine_learning/requirements.txt machine_learning/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt -r machine_learning/requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Reverse-Proxy Notes

- The Vite dev server proxies `/api/*` to `http://localhost:8000`. In production, configure your reverse proxy (nginx) with the same rule so the React bundle and the FastAPI service share an origin and CORS is unnecessary.
- Set `MONGODB_URI` and `OPENAI_API_KEY` as environment variables in your deployment platform (do **not** commit `.env`).

---

## API Reference

Base URL: `http://localhost:8000`

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/market/historical?years=5` | Historical SPY OHLCV from yfinance (5-min cache) |
| `GET`  | `/api/market/predictions`        | Stored ML predictions with predicted close prices |
| `GET`  | `/api/market/stats`              | Live SPY price, change, VIX, 200-MA distance, YTD return, 52W range, ML forecast |

### ML Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ml/generate-predictions` | Trains Ridge model, generates 773+ historical predictions and a live forward forecast |

### Backtesting

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/backtest/strategies` | Lists all available strategies |
| `POST` | `/api/backtest/run`        | Runs a backtest; returns metrics, equity curve, monthly returns |

### Chatbot

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chatbot/message` | Sends user message + history to GPT-4o |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/health` | Health check |

Interactive Swagger docs are available at `http://localhost:8000/docs`.

---

## Configuration

### ML Model Configuration

Edit hyperparameters and feature flags from the **ML Config** tab in the UI, or directly in:

- `machine_learning/ML/config.py` — base config
- `machine_learning/ML/config_overrides.json` — runtime overrides written by the UI
- `machine_learning/ML/config_presets.json` — saved presets

### Adding a New Backtest Strategy

Create `backtest/strategies/my_strategy.py` exporting a `generate_signals(df)` function that returns a DataFrame with columns `[Date, Close, Signal, EquityCurve]` (Signal: 1 = Buy, -1 = Sell, 0 = Hold). See `backtest/README.md` for a full example and the recommended stateful pattern for clean signals.

### MongoDB Setup

Detailed instructions live in `machine_learning/MONGODB_INTEGRATION_GUIDE.md`. The connection logic loads `MONGODB_URI` from the project-root `.env`, regardless of whether scripts are run from the repo root or the `machine_learning/` directory.

---

## Troubleshooting

| Issue | Resolution |
|-------|-----------|
| Frontend cannot reach backend | Ensure FastAPI is running on port 8000. The Vite dev server proxies `/api/*` automatically. |
| `MONGODB_URI` errors | The dashboard works without MongoDB — predictions just won't be persisted. To enable, fill in `.env` and confirm your IP is allow-listed in MongoDB Atlas. |
| Chatbot tab returns 401 / no response | Make sure `OPENAI_API_KEY` is set in `.env` and the backend was restarted after editing it. |
| `Generate Predictions` is slow on first run | The endpoint downloads ~5 years of SPY data and trains the model. Subsequent runs use cached data (5-min TTL). |
| R Shiny chatbot styling broken | Run `update.packages("bslib")`. |
| `pip install torch` fails on Windows | Use the official PyTorch installer command from https://pytorch.org for the matching CUDA / CPU build. |

---

## Additional Documentation

- [`DASHBOARD_CHANGES.md`](DASHBOARD_CHANGES.md) — Full implementation summary of the unified dashboard
- [`RUN_GUIDE.md`](RUN_GUIDE.md) — Quick-start commands
- [`backtest/README.md`](backtest/README.md) — Backtest engine internals & strategy authoring
- [`chatbot/README.md`](chatbot/README.md) — R Shiny signal generator full guide
- [`chatbot/QUICKSTART.md`](chatbot/QUICKSTART.md), [`chatbot/INTEGRATION_GUIDE.md`](chatbot/INTEGRATION_GUIDE.md), [`chatbot/SIGNAL_TYPES_GUIDE.md`](chatbot/SIGNAL_TYPES_GUIDE.md)
- [`machine_learning/MONGODB_INTEGRATION_GUIDE.md`](machine_learning/MONGODB_INTEGRATION_GUIDE.md) — MongoDB Atlas setup and schema

---

## License

Internal project — see individual subdirectory READMEs for component-level licensing notes (the chatbot README declares MIT).
