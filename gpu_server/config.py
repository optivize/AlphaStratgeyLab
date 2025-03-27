"""
Configuration settings for the GPU server
"""
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Server configuration
HOST = os.environ.get("GPU_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("GPU_SERVER_PORT", 5050))
DEBUG = os.environ.get("GPU_SERVER_DEBUG", "True").lower() in ("true", "1", "t", "yes")

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/backtest")

# GPU configuration
DEFAULT_GPU_DEVICE = int(os.environ.get("GPU_DEVICE", 0))
MAX_CONCURRENT_JOBS = int(os.environ.get("MAX_CONCURRENT_JOBS", 10))
GPU_MEMORY_LIMIT = float(os.environ.get("GPU_MEMORY_LIMIT", 0.9))  # 90% of GPU memory

# Data configuration
DATA_CACHE_DIR = Path(os.environ.get("DATA_CACHE_DIR", "/tmp/backtest_data"))
DATA_CACHE_SIZE = int(os.environ.get("DATA_CACHE_SIZE", 100))  # Number of datasets to cache
TIINGO_API_KEY = os.environ.get("TIINGO_API_KEY", "")

# Result storage configuration
RESULT_RETENTION_DAYS = int(os.environ.get("RESULT_RETENTION_DAYS", 30))

# Authentication
API_KEY_REQUIRED = os.environ.get("API_KEY_REQUIRED", "False").lower() in ("true", "1", "t", "yes")
API_KEY = os.environ.get("GPU_SERVER_API_KEY", "")

# Make sure data cache directory exists
DATA_CACHE_DIR.mkdir(parents=True, exist_ok=True)