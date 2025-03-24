import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "GPU-Powered Stock Backtesting Engine API"
    
    # Database connection
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/backtest")
    
    # CUDA settings
    MAX_GPU_MEMORY: int = 8 * 1024 * 1024 * 1024  # 8 GB
    DEFAULT_BLOCK_SIZE: int = 256
    
    # Data settings
    DEFAULT_DATA_SOURCE: str = "default"
    DATA_CACHE_SIZE: int = 100  # Number of datasets to cache
    
    # Backtest settings
    MAX_SYMBOLS_PER_BACKTEST: int = 5000
    MAX_CONCURRENT_BACKTESTS: int = 10

    class Config:
        case_sensitive = True

settings = Settings()
