# Machine learning / market data pipeline (MongoDB-backed)
#
# S&P 500 prediction pipeline migrated from S-P-500-Prediction repo.
#
# Structure:
#   db.py           - MongoDB connection (shared with dashboard)
#   db_helpers.py   - Collection read/write helpers (ohlcv, features, predictions, run_metadata)
#   data_loader.py  - Fetches raw data from Yahoo Finance + FRED
#   pipeline.py     - Feature engineering entry point (was main.py in original repo)
#   refresh_data.py - Weekly refresh script (scheduler entry point)
#   features/       - Feature engineering modules (trend, volatility, breadth, etc.)
#   ML/             - Model training, evaluation, and backtesting
#   Output/         - Generated CSV files (gitignored)
