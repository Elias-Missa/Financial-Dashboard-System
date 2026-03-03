# Financial Dashboard — Implementation Summary

## Overview

Unified the existing ML pipeline, backtesting engine, and chatbot into a single web-based Financial Dashboard. The system now exposes a **FastAPI backend** that serves data to a **React frontend**, providing a real-time view of S&P 500 prices, ML-powered predictions, strategy backtesting, and an AI chat assistant — all in one place.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                   React Frontend                     │
│              (Vite + TailwindCSS)                    │
│                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────────┐      │
│   │Dashboard │  │ Backtest │  │   Chatbot    │      │
│   │  Tab     │  │   Tab    │  │    Tab       │      │
│   └────┬─────┘  └────┬─────┘  └──────┬───────┘      │
│        │              │               │              │
└────────┼──────────────┼───────────────┼──────────────┘
         │              │               │
         ▼              ▼               ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI Backend                      │
│                  (Port 8000)                          │
│                                                      │
│   /api/market/*     → yfinance + MongoDB             │
│   /api/backtest/*   → existing backtest engine       │
│   /api/chatbot/*    → OpenAI GPT-4o                  │
│   /api/ml/*         → Ridge regression pipeline      │
└──────────────────────────────────────────────────────┘
         │              │               │
         ▼              ▼               ▼
   ┌──────────┐  ┌──────────┐  ┌──────────────┐
   │ yfinance │  │ backtest/│  │   OpenAI     │
   │  + MongoDB│  │strategies│  │    API       │
   └──────────┘  └──────────┘  └──────────────┘
```

---

## New Files Created

### Backend — `api/`

| File | Purpose |
|------|---------|
| `api/main.py` | FastAPI server with all API routes, ML prediction generation, caching layer |
| `api/requirements.txt` | Python dependencies (fastapi, uvicorn, yfinance, openai, scikit-learn, etc.) |

### Frontend — `frontend/`

| File | Purpose |
|------|---------|
| `frontend/package.json` | Node dependencies and scripts |
| `frontend/vite.config.js` | Vite config with API proxy to backend |
| `frontend/tailwind.config.js` | Tailwind CSS configuration |
| `frontend/postcss.config.js` | PostCSS plugin setup |
| `frontend/index.html` | HTML entry point with Inter font |
| `frontend/src/main.jsx` | React entry point |
| `frontend/src/App.jsx` | Root component with sidebar navigation |
| `frontend/src/index.css` | Global styles and Tailwind directives |
| `frontend/src/api.js` | Axios API client for all endpoints |
| `frontend/src/components/Dashboard.jsx` | Dashboard tab — chart + stats + prediction controls |
| `frontend/src/components/PriceChart.jsx` | Recharts composed chart (gray historical + green predictions) |
| `frontend/src/components/MarketStats.jsx` | Six stat cards (SPY price, VIX, 200MA, YTD, 52W range, ML prediction) |
| `frontend/src/components/Backtest.jsx` | Backtest tab — strategy selector, metrics table, equity curve chart |
| `frontend/src/components/Chatbot.jsx` | Chat tab — GPT-4o financial assistant with markdown rendering |

### Modified Files

| File | Change |
|------|--------|
| `.env` | Added `OPENAI_API_KEY=` placeholder for chatbot functionality |

---

## API Endpoints

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/historical?years=5` | Historical SPY OHLCV from yfinance (cached 5 min) |
| `GET` | `/api/market/predictions` | ML predictions with predicted close prices |
| `GET` | `/api/market/stats` | Live market stats — price, change, VIX, 200MA, YTD return, 52W range, ML forecast |

### ML Predictions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/ml/generate-predictions` | Trains Ridge model on 16 technical features, generates 773+ predictions for 2023–present and a live forward forecast |

### Backtesting

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/backtest/strategies` | Lists all 30 available strategies with display names and type (Long/Short) |
| `POST` | `/api/backtest/run` | Runs a full backtest — returns metrics, equity curve, and monthly returns |

### Chatbot

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chatbot/message` | Sends user message + history to GPT-4o, returns financial analysis response |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |

---

## ML Prediction Pipeline

The `/api/ml/generate-predictions` endpoint builds a self-contained prediction pipeline using only yfinance data:

**Features engineered (16 total):**
- Price returns: 1-day, 5-day, 21-day, 63-day
- Moving average signals: 50MA distance, 200MA distance, 50MA slope, 200MA slope
- Volatility: 20-day vol, 60-day vol, vol ratio
- Momentum: RSI-14, RSI-5
- Risk: 14-day ATR (normalized)
- Volume: volume ratio vs 50-day average
- Trend: distance from 52-week high
- Seasonality: month of year

**Model:** Ridge regression (alpha=100) trained on pre-2023 data.

**Output:** Predicted 21-trading-day forward return for every date from Jan 2023 onward, plus a live forecast from the latest available data.

When MongoDB is reachable, predictions are also persisted to the `predictions` collection for use by the existing ML infrastructure.

---

## Frontend Design

- **Dark theme** using Tailwind's slate palette (`slate-950` background, `slate-900` cards)
- **Inter font** for clean, professional typography
- **Sidebar navigation** with three tabs: Dashboard, Backtest, Chatbot
- **Chart**: Recharts `ComposedChart` with gray area fill for historical prices and green line for ML predictions, with a blue dashed "Today" reference line
- **Responsive** grid layouts for stats cards and metrics
- **Loading states** with skeleton placeholders and spinners
- **Error handling** with inline error banners

---

## How to Run

### Prerequisites
- Python 3.10+
- Node.js 18+
- (Optional) `OPENAI_API_KEY` in `.env` for chatbot
- (Optional) MongoDB Atlas connection for persistent predictions

### Start the Backend
```bash
cd api
pip install -r requirements.txt
python -m uvicorn main:app --port 8000
```

### Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

### Open the Dashboard
Navigate to **http://localhost:5173** and click **Generate Predictions** to populate the chart.

---

## What Was Not Changed

All existing code in `machine_learning/`, `backtest/`, and `chatbot/` remains untouched. The new `api/` layer imports from these modules without modifying them. The existing CLI and GUI tools continue to work independently.
