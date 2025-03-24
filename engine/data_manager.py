import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
import os
from core.models import DataSource

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages data loading, caching and processing
    """
    
    def __init__(self):
        """
        Initialize the data manager
        """
        self.data_cache = {}
        self.custom_data_sources = {}
        
        # Default data source - should be populated with real data in production
        self.default_symbols = [
            "AAPL", "MSFT", "GOOG", "AMZN", "META", 
            "TSLA", "NVDA", "BRK.A", "JPM", "JNJ"
        ]
        
        # Register default data source
        self.custom_data_sources["default"] = {
            "name": "default",
            "description": "Default stock market data",
            "symbols_count": len(self.default_symbols),
            "start_date": date(2010, 1, 1),
            "end_date": date(2023, 12, 31),
            "timeframes": ["1d", "1h"]
        }
    
    def get_historical_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        timeframe: str = "1d",
        data_source: str = "default"
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical OHLCV data for the specified symbols
        """
        logger.info(f"Loading data for {len(symbols)} symbols from {start_date} to {end_date}")
        
        result = {}
        
        for symbol in symbols:
            # Check cache first
            cache_key = f"{symbol}_{data_source}_{timeframe}_{start_date}_{end_date}"
            
            if cache_key in self.data_cache:
                logger.debug(f"Using cached data for {symbol}")
                result[symbol] = self.data_cache[cache_key]
                continue
            
            # Generate synthetic data for demo purposes
            # In production, this would be replaced with real data fetching logic
            df = self._generate_synthetic_data(symbol, start_date, end_date, timeframe)
            
            # Cache the data
            self.data_cache[cache_key] = df
            
            result[symbol] = df
        
        return result
    
    def store_custom_data(self, df: pd.DataFrame, source_name: str) -> List[str]:
        """
        Store custom data uploaded by the user
        """
        # Get unique symbols in the data
        symbols = df['symbol'].unique().tolist()
        
        # Register the data source
        self.custom_data_sources[source_name] = {
            "name": source_name,
            "description": f"Custom data uploaded by user",
            "symbols_count": len(symbols),
            "start_date": df['date'].min(),
            "end_date": df['date'].max(),
            "timeframes": ["1d"] # Assume daily data for simplicity
        }
        
        # Store data for each symbol
        for symbol in symbols:
            symbol_df = df[df['symbol'] == symbol].copy()
            
            # Ensure date is properly formatted
            symbol_df['date'] = pd.to_datetime(symbol_df['date'])
            
            # Set date as index
            symbol_df.set_index('date', inplace=True)
            symbol_df.sort_index(inplace=True)
            
            # Store in cache
            cache_key = f"{symbol}_{source_name}_1d_{symbol_df.index.min().date()}_{symbol_df.index.max().date()}"
            self.data_cache[cache_key] = symbol_df
        
        return symbols
    
    def list_data_sources(self) -> List[DataSource]:
        """
        List available data sources
        """
        sources = []
        
        for source_id, source_data in self.custom_data_sources.items():
            source = DataSource(
                name=source_data["name"],
                description=source_data["description"],
                symbols_count=source_data["symbols_count"],
                start_date=source_data.get("start_date"),
                end_date=source_data.get("end_date"),
                timeframes=source_data["timeframes"]
            )
            sources.append(source)
        
        return sources
    
    def list_symbols(self, source: Optional[str] = None) -> List[str]:
        """
        List available symbols, optionally filtered by data source
        """
        if source and source not in self.custom_data_sources:
            return []
        
        if source is None or source == "default":
            return self.default_symbols
        
        # Extract symbols from cache keys
        symbols = set()
        source_prefix = f"_{source}_"
        
        for cache_key in self.data_cache.keys():
            if source_prefix in cache_key:
                symbol = cache_key.split('_')[0]
                symbols.add(symbol)
        
        return list(symbols)
    
    def _generate_synthetic_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        timeframe: str
    ) -> pd.DataFrame:
        """
        Generate synthetic price data for demo purposes
        """
        # Convert dates to pandas datetime
        start_pd = pd.Timestamp(start_date)
        end_pd = pd.Timestamp(end_date)
        
        # Generate date range based on timeframe
        if timeframe == "1d":
            date_range = pd.date_range(start=start_pd, end=end_pd, freq='B')
        elif timeframe == "1h":
            date_range = pd.date_range(start=start_pd, end=end_pd, freq='H')
        elif timeframe == "1m":
            date_range = pd.date_range(start=start_pd, end=end_pd, freq='T')
        else:
            date_range = pd.date_range(start=start_pd, end=end_pd, freq='B')
        
        n_periods = len(date_range)
        
        # Generate random price data
        # Use symbol hash for reproducible randomness
        symbol_seed = sum(ord(c) for c in symbol)
        np.random.seed(symbol_seed)
        
        # Start with a base price specific to the symbol
        base_price = (symbol_seed % 90) + 10  # Price between 10 and 100
        
        # Generate price movements with some trend and volatility
        daily_returns = np.random.normal(0.0002, 0.015, n_periods)
        price_movements = np.cumprod(1 + daily_returns)
        
        # Create price series
        close_prices = base_price * price_movements
        
        # Generate other OHLCV data
        volatility = np.random.uniform(0.01, 0.03)
        high_prices = close_prices * (1 + np.random.uniform(0, volatility, n_periods))
        low_prices = close_prices * (1 - np.random.uniform(0, volatility, n_periods))
        open_prices = low_prices + np.random.uniform(0, 1, n_periods) * (high_prices - low_prices)
        
        # Volume with some randomness and correlation to price changes
        base_volume = np.random.uniform(50000, 1000000)
        volume = base_volume * (1 + np.abs(daily_returns) * 10) * np.random.uniform(0.5, 1.5, n_periods)
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volume,
            'symbol': symbol
        }, index=date_range)
        
        return df
