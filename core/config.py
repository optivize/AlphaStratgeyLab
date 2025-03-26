import os

# Simple configuration class to replace Pydantic
class Settings:
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "StockTester API"
    
    # Database connection
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/backtest")
    
    # Data settings
    DEFAULT_DATA_SOURCE: str = "default"
    DATA_CACHE_SIZE: int = 100  # Number of datasets to cache
    
    # Backtest settings
    MAX_SYMBOLS_PER_BACKTEST: int = 5000
    MAX_CONCURRENT_BACKTESTS: int = 10

settings = Settings()
