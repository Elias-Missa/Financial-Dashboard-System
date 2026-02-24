"""
MongoDB connection for the machine learning / market data pipeline.
Uses MONGODB_URI from environment (set in .env or your shell).
"""

import os
from pathlib import Path

# Load .env from project root when running from machine_learning/ or from root
_root = Path(__file__).resolve().parent.parent
_env_path = _root / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)

# Also try .env in the machine_learning/ directory itself (for standalone usage)
_local_env = Path(__file__).resolve().parent / ".env"
if _local_env.exists():
    from dotenv import load_dotenv
    load_dotenv(_local_env)

# Default database name for market data
DEFAULT_DB_NAME = "market_data"


def get_uri():
    """MongoDB connection URI from environment."""
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise ValueError(
            "MONGODB_URI is not set. Add it to a .env file in the project root "
            "or set the environment variable. See .env.example for format."
        )
    return uri


def get_client():
    """Return a MongoDB client (single shared client is fine for most use)."""
    import pymongo
    return pymongo.MongoClient(get_uri())


def get_database(name: str = DEFAULT_DB_NAME):
    """Return the database to use for market data."""
    return get_client()[name]


def get_collection(collection_name: str, db_name: str = DEFAULT_DB_NAME):
    """Return a collection from the market data database."""
    return get_database(db_name)[collection_name]


def get_market_data_collection(collection_name: str = "ohlcv"):
    """Convenience alias: return the collection for storing OHLCV / market data."""
    return get_collection(collection_name)
