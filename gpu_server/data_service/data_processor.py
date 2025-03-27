"""
Data processing module for the GPU server
"""
import os
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, date
import requests
from io import BytesIO
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import config
from models.job import DataSource

# Set up logging
logger = logging.getLogger(__name__)

# Set up database connection
Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
Session = sessionmaker(bind=engine)

class CustomDataSource(Base):
    """Custom data source database model"""
    __tablename__ = 'custom_data_sources'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    symbols_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataProcessor:
    """
    Data processing and management for backtesting
    """
    
    def __init__(self):
        """Initialize the data processor"""
        logger.info("Initializing Data Processor")
        
        # Create data cache directory if it doesn't exist
        os.makedirs(config.DATA_CACHE_DIR, exist_ok=True)
        
        # Initialize in-memory cache
        self.data_cache = {}
        
        # Create database tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Initialize Tiingo client if API key is provided
        self.tiingo_api_key = config.TIINGO_API_KEY
        if self.tiingo_api_key:
            logger.info("Tiingo API key provided, external data access enabled")
    
    def get_historical_data(
        self,
        symbols: List[str],
        start_date: Union[str, date],
        end_date: Union[str, date],
        timeframe: str = "1d",
        data_source: str = "default"
    ) -> Dict[str, pd.DataFrame]:
        """
        Get historical OHLCV data for the specified symbols
        
        Args:
            symbols: List of symbol strings
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Data timeframe (e.g., "1d", "1h", "5m")
            data_source: Data source to use
            
        Returns:
            Dictionary of DataFrames with historical data for each symbol
        """
        logger.info(f"Loading historical data for {len(symbols)} symbols from {start_date} to {end_date}")
        
        # Convert string dates to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Check if this is a custom data source
        if data_source != "default" and data_source != "tiingo":
            return self._load_custom_data(symbols, start_date, end_date, timeframe, data_source)
        
        result = {}
        missing_symbols = []
        
        # First try to load from cache
        for symbol in symbols:
            cache_key = f"{symbol}_{timeframe}_{data_source}"
            if cache_key in self.data_cache:
                # Filter cached data to requested date range
                df = self.data_cache[cache_key]
                mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
                filtered_df = df.loc[mask]
                
                if not filtered_df.empty:
                    result[symbol] = filtered_df
                else:
                    missing_symbols.append(symbol)
            else:
                missing_symbols.append(symbol)
        
        # Try to load missing data from external sources
        if missing_symbols:
            if data_source == "default" or data_source == "tiingo":
                # Use Tiingo if API key is available
                if self.tiingo_api_key:
                    external_data = self._load_tiingo_data(missing_symbols, start_date, end_date, timeframe)
                    result.update(external_data)
                else:
                    # Generate synthetic data if no API key
                    logger.warning("No Tiingo API key provided. Using synthetic data for testing.")
                    for symbol in missing_symbols:
                        result[symbol] = self._generate_synthetic_data(
                            symbol, start_date, end_date, timeframe
                        )
            else:
                logger.warning(f"Unknown data source: {data_source}")
        
        # Cache any new data
        for symbol, df in result.items():
            if symbol not in self.data_cache:
                cache_key = f"{symbol}_{timeframe}_{data_source}"
                self.data_cache[cache_key] = df
                
                # Save to disk cache
                cache_file = config.DATA_CACHE_DIR / f"{cache_key}.parquet"
                df.to_parquet(cache_file)
        
        if len(result) < len(symbols):
            missing = set(symbols) - set(result.keys())
            logger.warning(f"Could not load data for symbols: {missing}")
        
        return result
    
    def store_custom_data(self, file, source_name: str) -> List[str]:
        """
        Store custom data uploaded by the user
        
        Args:
            file: Uploaded file object
            source_name: Name for the custom data source
            
        Returns:
            List of symbols in the custom data
        """
        logger.info(f"Storing custom data for source: {source_name}")
        
        # Read file into DataFrame
        if hasattr(file, 'filename'):
            # This is a Flask FileStorage object
            filename = file.filename
            file_content = file.read()
            file_obj = BytesIO(file_content)
        else:
            # This might be a path or file-like object
            filename = str(file)
            file_obj = file
        
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file_obj, parse_dates=['date'])
            elif filename.endswith('.parquet'):
                df = pd.read_parquet(file_obj)
            elif filename.endswith('.json'):
                df = pd.read_json(file_obj)
            else:
                raise ValueError(f"Unsupported file format: {filename}")
        except Exception as e:
            logger.error(f"Error reading data file: {str(e)}")
            raise ValueError(f"Failed to parse data file: {str(e)}")
        
        # Validate dataframe structure
        required_columns = ['date', 'symbol', 'open', 'high', 'low', 'close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Set date as index
        if 'date' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df.set_index('date', inplace=True)
        
        # Get list of symbols
        symbols = df['symbol'].unique().tolist()
        
        # Create directory for source if it doesn't exist
        source_dir = config.DATA_CACHE_DIR / source_name
        os.makedirs(source_dir, exist_ok=True)
        
        # Split data by symbol and store
        for symbol in symbols:
            symbol_data = df[df['symbol'] == symbol].copy()
            
            # Remove symbol column since it's redundant now
            if 'symbol' in symbol_data.columns:
                symbol_data.drop('symbol', axis=1, inplace=True)
            
            # Save to cache
            cache_key = f"{symbol}_1d_{source_name}"
            self.data_cache[cache_key] = symbol_data
            
            # Save to disk
            cache_file = source_dir / f"{symbol}.parquet"
            symbol_data.to_parquet(cache_file)
        
        # Record in database
        session = Session()
        try:
            existing = session.query(CustomDataSource).filter_by(name=source_name).first()
            
            if existing:
                existing.symbols_count = len(symbols)
                existing.created_at = datetime.utcnow()
            else:
                source = CustomDataSource(
                    name=source_name,
                    description=f"Custom data source uploaded on {datetime.now().strftime('%Y-%m-%d')}",
                    symbols_count=len(symbols)
                )
                session.add(source)
                
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {str(e)}")
            raise
        finally:
            session.close()
        
        return symbols
    
    def list_data_sources(self) -> List[DataSource]:
        """
        List available data sources
        
        Returns:
            List of data source information
        """
        logger.info("Listing available data sources")
        
        sources = []
        
        # Add default source
        sources.append(DataSource(
            id="default",
            name="Default Data",
            description="Default market data source",
            symbols_count=5000,  # Approximate
            created_at=datetime.utcnow()
        ))
        
        # Add Tiingo if available
        if self.tiingo_api_key:
            sources.append(DataSource(
                id="tiingo",
                name="Tiingo",
                description="Tiingo market data API",
                symbols_count=10000,  # Approximate
                created_at=datetime.utcnow()
            ))
        
        # Add custom sources from database
        session = Session()
        try:
            custom_sources = session.query(CustomDataSource).all()
            
            for source in custom_sources:
                sources.append(DataSource(
                    id=source.name,
                    name=source.name,
                    description=source.description,
                    symbols_count=source.symbols_count,
                    created_at=source.created_at
                ))
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
        finally:
            session.close()
        
        return sources
    
    def list_symbols(self, source: Optional[str] = None) -> List[str]:
        """
        List available symbols, optionally filtered by data source
        
        Args:
            source: Data source name
            
        Returns:
            List of symbol strings
        """
        logger.info(f"Listing symbols for source: {source}")
        
        if source is None or source == "default":
            # Return some default symbols
            return ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA"]
        elif source == "tiingo" and self.tiingo_api_key:
            # Query Tiingo for supported symbols
            return self._get_tiingo_symbols()
        else:
            # Check if it's a custom source
            # Look for parquet files in the source directory
            source_dir = config.DATA_CACHE_DIR / source
            if os.path.exists(source_dir) and os.path.isdir(source_dir):
                symbols = []
                for file in os.listdir(source_dir):
                    if file.endswith('.parquet'):
                        symbol = file.replace('.parquet', '')
                        symbols.append(symbol)
                return symbols
            else:
                logger.warning(f"Unknown data source: {source}")
                return []
    
    def _load_tiingo_data(
        self, 
        symbols: List[str],
        start_date: date,
        end_date: date,
        timeframe: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data from Tiingo API
        """
        if not self.tiingo_api_key:
            logger.warning("No Tiingo API key provided")
            return {}
        
        result = {}
        
        # Convert timeframe to Tiingo format
        tiingo_timeframe = "daily"
        if timeframe in ["1h", "60m"]:
            tiingo_timeframe = "hourly"
        
        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.tiingo_api_key}'
        }
        
        for symbol in symbols:
            try:
                url = f"https://api.tiingo.com/tiingo/{tiingo_timeframe}/{symbol}/prices"
                params = {
                    'startDate': start_str,
                    'endDate': end_str,
                    'format': 'json'
                }
                
                response = requests.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(data)
                    
                    # Rename columns to match expected format
                    column_map = {
                        'date': 'date',
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'volume': 'volume'
                    }
                    
                    df = df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})
                    
                    # Set date as index
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                    
                    result[symbol] = df
                else:
                    logger.warning(f"Failed to fetch Tiingo data for {symbol}: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error fetching Tiingo data for {symbol}: {str(e)}")
        
        return result
    
    def _get_tiingo_symbols(self) -> List[str]:
        """
        Get list of supported symbols from Tiingo
        """
        if not self.tiingo_api_key:
            return []
        
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Token {self.tiingo_api_key}'
            }
            
            response = requests.get(
                "https://api.tiingo.com/tiingo/utilities/supported-tickers",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return [item["ticker"] for item in data]
            else:
                logger.warning(f"Failed to fetch Tiingo symbols: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching Tiingo symbols: {str(e)}")
            return []
    
    def _load_custom_data(
        self,
        symbols: List[str],
        start_date: date,
        end_date: date,
        timeframe: str,
        source_name: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Load data from custom source
        """
        result = {}
        source_dir = config.DATA_CACHE_DIR / source_name
        
        if not os.path.exists(source_dir):
            logger.warning(f"Custom data source not found: {source_name}")
            return result
        
        for symbol in symbols:
            try:
                file_path = source_dir / f"{symbol}.parquet"
                
                if os.path.exists(file_path):
                    df = pd.read_parquet(file_path)
                    
                    # Filter to requested date range
                    if isinstance(df.index, pd.DatetimeIndex):
                        mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
                        df = df.loc[mask]
                    
                    result[symbol] = df
                else:
                    logger.warning(f"No data file found for symbol {symbol} in source {source_name}")
            except Exception as e:
                logger.error(f"Error loading custom data for {symbol}: {str(e)}")
        
        return result
    
    def _generate_synthetic_data(
        self, 
        symbol: str, 
        start_date: date, 
        end_date: date, 
        timeframe: str
    ) -> pd.DataFrame:
        """
        Generate synthetic price data for testing purposes
        """
        logger.warning(f"Generating synthetic data for {symbol} from {start_date} to {end_date}")
        
        # Create date range
        if timeframe == "1d":
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')
        elif timeframe in ["1h", "60m"]:
            date_range = pd.date_range(start=start_date, end=end_date, freq='H')
        elif timeframe in ["5m"]:
            date_range = pd.date_range(start=start_date, end=end_date, freq='5min')
        else:
            date_range = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # Set random seed based on symbol for consistency
        seed = sum(ord(c) for c in symbol)
        np.random.seed(seed)
        
        # Generate prices
        n = len(date_range)
        close = 100 + np.cumsum(np.random.normal(0, 1, n))
        daily_volatility = np.random.uniform(0.005, 0.02, n)
        
        # Ensure prices are positive
        close = np.maximum(close, 1)
        
        # Generate OHLCV data
        high = close + close * daily_volatility
        low = close - close * daily_volatility
        open_price = low + (high - low) * np.random.random(n)
        volume = np.random.randint(100000, 1000000, n)
        
        # Create DataFrame
        df = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=date_range)
        
        return df