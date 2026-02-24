# MongoDB Atlas – Integration Guide (Machine Learning / Market Data)

This document explains how the MongoDB Atlas database is set up in this project so you can read/write market data from the machine learning pipeline. **The database is used only by the ML component;** it is not connected to the backtest or chatbot.

---

## 1. Overview

- **Provider:** MongoDB Atlas (cloud).
- **Purpose:** Store and retrieve market data (e.g. OHLCV, features) for the machine learning pipeline.
- **Location in repo:** Connection logic lives under `machine_learning/`. Credentials are loaded from a `.env` file at the **project root** (parent of `machine_learning/`).

---

## 2. Project layout (relevant parts)

```
Financial-Dashboard-System/
├── .env                    # Real credentials (gitignored – do not commit)
├── .env.example            # Template only (safe to commit)
├── machine_learning/
│   ├── __init__.py         # Package init
│   ├── db.py               # MongoDB connection helpers
│   ├── db_helpers.py       # Collection read/write (ohlcv, features, predictions, run_metadata)
│   ├── data_loader.py      # Fetches data from Yahoo Finance + FRED
│   ├── pipeline.py         # Feature engineering entry point
│   ├── refresh_data.py     # Weekly data refresh scheduler script
│   ├── requirements.txt    # All Python dependencies
│   ├── MONGODB_INTEGRATION_GUIDE.md  # This file
│   ├── features/           # Feature engineering modules
│   │   ├── trend.py, volatility.py, breadth.py, cross_asset.py, macro.py, sentiment.py
│   ├── ML/                 # Model training and evaluation
│   │   ├── config.py, train.py, train_walkforward.py, models.py, metrics.py, ...
│   └── Output/             # Generated CSV files (gitignored)
├── backtest/               # Not using this DB
└── chatbot/                # Not using this DB
```

- **`.env`** must exist at the project root and contain `MONGODB_URI`. The code in `machine_learning/db.py` loads it from there (whether you run scripts from the repo root or from `machine_learning/`).
- **`.env.example`** shows the expected variable name and format (no real secrets).

---

## 3. Environment variable

| Variable      | Required | Description |
|---------------|----------|-------------|
| `MONGODB_URI` | Yes      | Full MongoDB Atlas connection string (SRV). Example format: `mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?appName=...` |

- Set in **project root** `.env` (one line, no quotes needed):
  ```env
  MONGODB_URI=mongodb+srv://USER:PASSWORD@HOST.mongodb.net/?appName=...
  ```
- If `MONGODB_URI` is missing, `db.py` raises a clear `ValueError` telling you to add it to `.env` or the environment.

---

## 4. Dependencies

Install the ML dependencies (from repo root or from `machine_learning/`):

```bash
pip install -r machine_learning/requirements.txt
```

Or explicitly:

```bash
pip install "pymongo[srv]==3.12" python-dotenv
```

- **pymongo[srv]** – MongoDB driver with SRV support for Atlas.
- **python-dotenv** – Loads `MONGODB_URI` from the project root `.env` when you use `machine_learning.db`.

---

## 5. Connection API (`db.py`)

All low-level DB access goes through this module. Credentials are loaded from `.env` at the **project root** or from `machine_learning/.env` if present.

| Function / constant            | Purpose |
|--------------------------------|--------|
| `get_uri()`                    | Returns `MONGODB_URI` from env (raises if missing). |
| `get_client()`                 | Returns a `pymongo.MongoClient` instance. |
| `get_database(name)`           | Returns a database. Default `name` is `"market_data"`. |
| `get_collection(collection_name, db_name)` | Returns a collection. Default DB is `"market_data"`. |
| `get_market_data_collection(collection_name)` | Convenience: same as `get_collection(collection_name)` (default collection `"ohlcv"`). |
| `DEFAULT_DB_NAME`              | `"market_data"`. |

- Default database: **`market_data`**. Collections used by the pipeline: **`ohlcv`**, **`features`**, **`predictions`**, **`run_metadata`** (see §6).

---

## 5b. Collection helpers (`db_helpers.py`)

For the S&P 500 prediction pipeline, **prefer `db_helpers`** over raw `db` for reading/writing. It handles indexes, pandas ↔ BSON conversion, and idempotent upserts.

| Collection      | Purpose |
|-----------------|--------|
| **ohlcv**       | Raw daily prices and macro data (one doc per symbol per date, `value` field). |
| **features**    | Engineered daily features (one doc per date). |
| **predictions** | Model predictions per run (keyed by `run_id` + date). |
| **run_metadata**| One doc per training run (run_id, created_at, config snapshot, metrics). |

**OHLCV:** `upsert_ohlcv(df)`, `load_ohlcv_df(symbols=..., since_date=...)`, `get_last_ohlcv_date()`  
**Features:** `upsert_features(df)`, `load_features_df(since_date=...)`, `get_last_feature_date()`  
**Predictions / runs:** `save_predictions(run_id, df, metadata=...)`, `load_predictions(run_id)`, `load_latest_predictions()`, `load_run_metadata(run_id)`

Indexes are created automatically on first write. Run from **`machine_learning/`** so `from db import get_collection` works in `db_helpers.py`.

---

## 6. How to run the pipeline (from `machine_learning/`)

Scripts are intended to be run with **`machine_learning/`** as the current working directory so that `from db import ...` and `from db_helpers import ...` work.

```bash
cd "Financial-Dashboard-System/machine_learning"
pip install -r requirements.txt
python refresh_data.py              # weekly data refresh
python refresh_data.py --retrain     # refresh + retrain model
```

- **`pipeline.py`** – feature engineering entry point (ingests data, builds features, writes to MongoDB).
- **`refresh_data.py`** – orchestrates data refresh and optional retrain; supports `--force` and `--retrain`.

---

## 7. Usage examples (for ML code)

**Using `db_helpers` (recommended for pipeline code):**

```python
# Run from machine_learning/ so these imports work
from db_helpers import (
    upsert_ohlcv, load_ohlcv_df, get_last_ohlcv_date,
    upsert_features, load_features_df, get_last_feature_date,
    save_predictions, load_predictions, load_latest_predictions, load_run_metadata,
)

# After fetching data into a DataFrame with DatetimeIndex and symbol columns:
upsert_ohlcv(df_raw)
df = load_ohlcv_df(symbols=["SPY", "^VIX"], since_date="2020-01-01")

# After building features:
upsert_features(df_features)
df_f = load_features_df(since_date="2020-01-01")

# After training (predictions DataFrame with DatetimeIndex and y_pred, etc.):
save_predictions("run_20250217", df_pred, metadata={"model": "transformer", "metrics": {...}})
df_pred, meta = load_latest_predictions()
```

**Low-level access via `db.py` (when you need a raw collection):**

```python
from db import get_collection, get_database, get_market_data_collection

# Default database "market_data"
ohlcv = get_market_data_collection("ohlcv")   # or get_collection("ohlcv")
features = get_collection("features")
predictions = get_collection("predictions")
run_metadata = get_collection("run_metadata")
```

**When running from project root** (e.g. tests or one-off scripts), use the package form so `machine_learning` is on `PYTHONPATH`:

```bash
# From Financial-Dashboard-System/
python -c "from machine_learning.db import get_database; print(get_database().name)"
```

---

## 8. Security

- **Do not commit `.env`.** It is in `.gitignore`. Only `.env.example` (with placeholders) should be committed.
- Do not hardcode `MONGODB_URI` (or any password) in source code or in this guide.
- If credentials were ever committed or shared, rotate the MongoDB user password in Atlas and update only the local `.env`.

---

## 9. Quick reference for an AI assistant

- **Database:** MongoDB Atlas; used only for ML/market data. DB name: `market_data`. Collections: `ohlcv`, `features`, `predictions`, `run_metadata`.
- **Config:** `MONGODB_URI` in project root `.env` (or `machine_learning/.env`); loaded by `db.py`.
- **Run directory:** Use `machine_learning/` as cwd so `from db import ...` and `from db_helpers import ...` work.
- **Entry points:** Prefer `db_helpers` for pipeline I/O (upsert_ohlcv, load_ohlcv_df, upsert_features, load_features_df, save_predictions, load_predictions, load_latest_predictions). Use `db.get_collection()` for low-level access.
- **Install:** `pip install -r machine_learning/requirements.txt`. Run: `python refresh_data.py` or `python refresh_data.py --retrain`.

Use this guide when implementing or refactoring code that reads or writes market data in this project.
