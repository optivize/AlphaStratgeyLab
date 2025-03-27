"""
GPU-accelerated backtesting engine
"""
import os
import uuid
import logging
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, Column, String, Float, JSON, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# Set up logging
logger = logging.getLogger(__name__)

try:
    # Try to import CUDA libraries
    # These will be available on the GPU server but may not be during development
    import pycuda.driver as cuda
    import pycuda.autoinit
    import pycuda.gpuarray as gpuarray
    from pycuda.compiler import SourceModule
    CUDA_AVAILABLE = True
    logger.info("CUDA is available")
except ImportError:
    logger.warning("CUDA libraries not available, falling back to CPU mode")
    CUDA_AVAILABLE = False

try:
    # Try to import CuPy for additional GPU-accelerated operations
    import cupy as cp
    CUPY_AVAILABLE = True
    logger.info("CuPy is available")
except ImportError:
    logger.warning("CuPy not available, some operations will be slower")
    CUPY_AVAILABLE = False

# Import local modules
import config
from data_service.data_processor import DataProcessor
from models.job import (
    BacktestRequest, 
    BacktestResult, 
    JobStatus, 
    JobStatusResponse,
    Strategy,
    StrategyParameter,
    Metrics,
    SymbolMetrics,
    Trade
)
from gpu_engine.kernels import get_cuda_kernel
from gpu_engine.metrics import calculate_metrics

# Setup database 
Base = declarative_base()
engine = create_engine(config.DATABASE_URL)
Session = sessionmaker(bind=engine)

class BacktestRecord(Base):
    """Database model for backtest records"""
    __tablename__ = "backtest_records"
    
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    request = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    results = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

class GPUBacktestEngine:
    """
    GPU-accelerated backtesting engine
    """
    
    def __init__(self):
        """Initialize the GPU engine"""
        logger.info("Initializing GPU Backtesting Engine")
        
        # Initialize data processor
        self.data_processor = DataProcessor()
        
        # Create database tables if they don't exist
        Base.metadata.create_all(engine)
        
        # Initialize job queue
        self.job_queue = queue.PriorityQueue()
        self.active_jobs = {}
        self.job_results = {}
        
        # Set up a thread pool for job processing
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_JOBS)
        
        # Initialize CUDA context if available
        if CUDA_AVAILABLE:
            try:
                self._initialize_cuda()
            except Exception as e:
                logger.error(f"Failed to initialize CUDA: {str(e)}")
                logger.warning("Running in CPU-only mode")
                self.cuda_context = None
        else:
            self.cuda_context = None
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=self._process_jobs, daemon=True)
        self.worker_thread.start()
    
    def _initialize_cuda(self):
        """Initialize CUDA device and context"""
        self.cuda_device = cuda.Device(config.DEFAULT_GPU_DEVICE)
        self.cuda_context = self.cuda_device.make_context()
        
        # Get device properties
        self.device_props = cuda.Device.get_attributes(self.cuda_device)
        
        logger.info(f"Using GPU: {self.cuda_device.name()}")
        logger.info(f"CUDA Compute Capability: {self.cuda_device.compute_capability()}")
        logger.info(f"Total GPU Memory: {self.cuda_device.total_memory() / 1024**2} MB")
        
        # Initialize strategy kernels
        self._initialize_kernels()
    
    def _initialize_kernels(self):
        """Initialize CUDA kernels for strategies"""
        self.kernels = {}
        
        if not CUDA_AVAILABLE:
            return
        
        # Moving Average Crossover kernel
        self.kernels["MovingAverageCrossover"] = SourceModule(get_cuda_kernel("moving_average")).get_function("moving_avg_crossover")
        
        # Bollinger Bands kernel
        self.kernels["BollingerBands"] = SourceModule(get_cuda_kernel("bollinger_bands")).get_function("bollinger_bands")
        
        # Momentum kernel
        self.kernels["MomentumStrategy"] = SourceModule(get_cuda_kernel("momentum")).get_function("momentum_strategy")
        
        # Mean Reversion kernel
        self.kernels["MeanReversion"] = SourceModule(get_cuda_kernel("mean_reversion")).get_function("mean_reversion")
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'cuda_context') and self.cuda_context:
            self.cuda_context.pop()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get GPU status information
        
        Returns:
            Dictionary with GPU status information
        """
        status = {
            "cuda_available": CUDA_AVAILABLE,
            "cupy_available": CUPY_AVAILABLE,
            "active_jobs": len(self.active_jobs),
            "queued_jobs": self.job_queue.qsize()
        }
        
        if CUDA_AVAILABLE and hasattr(self, 'cuda_device'):
            # Add GPU-specific information
            free_mem, total_mem = cuda.mem_get_info()
            status.update({
                "device_name": self.cuda_device.name(),
                "compute_capability": self.cuda_device.compute_capability(),
                "total_memory_mb": total_mem / 1024**2,
                "free_memory_mb": free_mem / 1024**2,
                "memory_usage_percent": 100 * (1 - free_mem / total_mem)
            })
        
        return status
    
    def submit_job(self, request: BacktestRequest) -> str:
        """
        Submit a new backtest job
        
        Args:
            request: Backtest request object
            
        Returns:
            Job ID string
        """
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create database record
        session = Session()
        try:
            record = BacktestRecord(
                id=job_id,
                user_id=request.user_id,
                request=request.dict(),
                status=JobStatus.PENDING.value
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving job to database: {str(e)}")
            raise
        finally:
            session.close()
        
        # Add to job queue with priority
        logger.info(f"Adding job {job_id} to queue with priority {request.priority}")
        self.job_queue.put((request.priority, job_id, request))
        
        return job_id
    
    def get_job_status(self, job_id: str) -> JobStatusResponse:
        """
        Get status of a backtest job
        
        Args:
            job_id: Job ID string
            
        Returns:
            Job status response object
        """
        # Check if job is in memory
        if job_id in self.job_results:
            return self.job_results[job_id]
        
        # Query database
        session = Session()
        try:
            record = session.query(BacktestRecord).filter_by(id=job_id).first()
            
            if not record:
                raise ValueError(f"Job {job_id} not found")
            
            status = JobStatus(record.status)
            
            result = JobStatusResponse(
                job_id=job_id,
                status=status,
                created_at=record.created_at,
                execution_time=record.execution_time,
                error=record.error
            )
            
            if record.results:
                result.results = BacktestResult(**record.results)
                
            return result
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            raise
        finally:
            session.close()
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a backtest job
        
        Args:
            job_id: Job ID string
            
        Returns:
            True if job was cancelled, False otherwise
        """
        # Check if job is active
        if job_id in self.active_jobs:
            # Can't cancel currently running jobs
            return False
        
        # Update database
        session = Session()
        try:
            record = session.query(BacktestRecord).filter_by(id=job_id).first()
            
            if not record:
                raise ValueError(f"Job {job_id} not found")
            
            if record.status in [JobStatus.PENDING.value, JobStatus.RUNNING.value]:
                record.status = JobStatus.CANCELLED.value
                session.commit()
                return True
            else:
                return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error cancelling job: {str(e)}")
            raise
        finally:
            session.close()
    
    def list_strategies(self) -> List[Strategy]:
        """
        List available strategies
        
        Returns:
            List of strategy objects
        """
        strategies = []
        
        # Moving Average Crossover
        strategies.append(Strategy(
            id="MovingAverageCrossover",
            name="Moving Average Crossover",
            description="Trading based on short and long-term moving average signals",
            parameters={
                "short_window": StrategyParameter(
                    type="integer",
                    default=20,
                    description="Short moving average window"
                ),
                "long_window": StrategyParameter(
                    type="integer",
                    default=50,
                    description="Long moving average window"
                ),
                "signal_threshold": StrategyParameter(
                    type="float",
                    default=0.01,
                    description="Signal threshold to trigger trades"
                )
            }
        ))
        
        # Bollinger Bands
        strategies.append(Strategy(
            id="BollingerBands",
            name="Bollinger Bands",
            description="Trading based on price movements relative to volatility bands",
            parameters={
                "window": StrategyParameter(
                    type="integer",
                    default=20,
                    description="Window size for calculating moving average"
                ),
                "num_std": StrategyParameter(
                    type="float",
                    default=2.0,
                    description="Number of standard deviations for bands"
                )
            }
        ))
        
        # Momentum
        strategies.append(Strategy(
            id="MomentumStrategy",
            name="Momentum",
            description="Trading based on price momentum indicators",
            parameters={
                "window": StrategyParameter(
                    type="integer",
                    default=14,
                    description="Lookback window for momentum calculation"
                ),
                "threshold": StrategyParameter(
                    type="float",
                    default=0.0,
                    description="Momentum threshold for signals"
                )
            }
        ))
        
        # Mean Reversion
        strategies.append(Strategy(
            id="MeanReversion",
            name="Mean Reversion",
            description="Trading based on price deviation from historical means",
            parameters={
                "window": StrategyParameter(
                    type="integer",
                    default=20,
                    description="Window for calculating mean"
                ),
                "entry_threshold": StrategyParameter(
                    type="float",
                    default=1.5,
                    description="Standard deviation threshold for entry"
                ),
                "exit_threshold": StrategyParameter(
                    type="float",
                    default=0.5,
                    description="Standard deviation threshold for exit"
                )
            }
        ))
        
        return strategies
    
    def _process_jobs(self):
        """
        Worker thread for processing jobs from the queue
        """
        logger.info("Starting job processing thread")
        
        while True:
            try:
                # Get job from queue
                _, job_id, request = self.job_queue.get()
                
                # Skip cancelled jobs
                session = Session()
                try:
                    record = session.query(BacktestRecord).filter_by(id=job_id).first()
                    if record.status == JobStatus.CANCELLED.value:
                        logger.info(f"Skipping cancelled job {job_id}")
                        self.job_queue.task_done()
                        continue
                finally:
                    session.close()
                
                # Add to active jobs
                self.active_jobs[job_id] = request
                
                # Update status in database
                session = Session()
                try:
                    record = session.query(BacktestRecord).filter_by(id=job_id).first()
                    record.status = JobStatus.RUNNING.value
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error(f"Error updating job status: {str(e)}")
                finally:
                    session.close()
                
                # Process job
                logger.info(f"Processing job {job_id}")
                try:
                    start_time = time.time()
                    result = self._run_backtest(request)
                    execution_time = time.time() - start_time
                    
                    # Update database with result
                    session = Session()
                    try:
                        record = session.query(BacktestRecord).filter_by(id=job_id).first()
                        record.status = JobStatus.COMPLETED.value
                        record.execution_time = execution_time
                        record.results = result.dict()
                        session.commit()
                        
                        # Store result in memory
                        self.job_results[job_id] = JobStatusResponse(
                            job_id=job_id,
                            status=JobStatus.COMPLETED,
                            created_at=record.created_at,
                            execution_time=execution_time,
                            results=result
                        )
                        
                        logger.info(f"Job {job_id} completed in {execution_time:.2f} seconds")
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Error saving job result: {str(e)}")
                    finally:
                        session.close()
                except Exception as e:
                    logger.error(f"Error processing job {job_id}: {str(e)}", exc_info=True)
                    
                    # Update database with error
                    session = Session()
                    try:
                        record = session.query(BacktestRecord).filter_by(id=job_id).first()
                        record.status = JobStatus.FAILED.value
                        record.error = str(e)
                        session.commit()
                        
                        # Store error in memory
                        self.job_results[job_id] = JobStatusResponse(
                            job_id=job_id,
                            status=JobStatus.FAILED,
                            created_at=record.created_at,
                            error=str(e)
                        )
                    except Exception as e2:
                        session.rollback()
                        logger.error(f"Error saving job error: {str(e2)}")
                    finally:
                        session.close()
                
                # Remove from active jobs
                del self.active_jobs[job_id]
                
                # Mark task as done
                self.job_queue.task_done()
            except Exception as e:
                logger.error(f"Error in job processing thread: {str(e)}", exc_info=True)
                time.sleep(1)  # Prevent tight loop in case of persistent errors
    
    def _run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """
        Run a backtest with the given parameters
        
        Args:
            request: Backtest request object
            
        Returns:
            Backtest result object
        """
        logger.info(f"Running backtest for strategy {request.strategy.name}")
        
        # Load data
        data = self.data_processor.get_historical_data(
            symbols=request.data.symbols,
            start_date=request.data.start_date,
            end_date=request.data.end_date,
            timeframe=request.data.timeframe,
            data_source=request.data.data_source
        )
        
        if not data:
            raise ValueError("No data available for the specified symbols and date range")
        
        # Check if strategy is supported
        if request.strategy.name not in [s.id for s in self.list_strategies()]:
            raise ValueError(f"Strategy {request.strategy.name} not supported")
        
        # Prepare data for GPU processing
        gpu_data = {}
        for symbol, df in data.items():
            # Ensure required columns are present
            required_columns = ['open', 'high', 'low', 'close']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Missing columns for {symbol}: {missing_columns}")
                continue
            
            # Convert to numpy array
            if 'volume' in df.columns:
                gpu_data[symbol] = df[['open', 'high', 'low', 'close', 'volume']].values
            else:
                # Add volume column with zeros if not present
                ohlc = df[['open', 'high', 'low', 'close']].values
                volume = np.zeros((len(ohlc), 1))
                gpu_data[symbol] = np.hstack((ohlc, volume))
        
        # Run strategy on GPU
        position_arrays = {}
        equity_curves = {}
        trades_list = []
        
        for symbol, ohlcv in gpu_data.items():
            # Execute strategy on GPU
            signals, positions = self._execute_strategy(
                ohlcv, 
                request.strategy.name,
                request.strategy.parameters
            )
            
            # Store positions for metrics calculation
            position_arrays[symbol] = positions
            
            # Generate trades
            trades = self._generate_trades(
                symbol,
                data[symbol].index.values,
                ohlcv,
                positions,
                request.execution.initial_capital,
                request.execution.position_size,
                request.execution.commission,
                request.execution.slippage
            )
            
            trades_list.extend(trades)
            
            # Calculate equity curve
            prices = ohlcv[:, 3]  # close prices
            equity = self._calculate_equity_curve(
                positions,
                prices,
                request.execution.initial_capital / len(gpu_data),
                request.execution.commission,
                request.execution.slippage
            )
            equity_curves[symbol] = equity
        
        # Calculate metrics
        overall_metrics, symbol_metrics = calculate_metrics(
            trades_list,
            position_arrays,
            data,
            request.execution.initial_capital,
            request.output.metrics
        )
        
        # Combine equity curves
        combined_equity = None
        if equity_curves:
            # Use uniform length for all equity curves
            min_length = min(len(curve) for curve in equity_curves.values())
            
            # Sum up equity curves
            combined_equity = sum(curve[:min_length] for curve in equity_curves.values())
        
        # Prepare results
        result = BacktestResult(
            overall_metrics=overall_metrics,
            per_symbol_metrics=symbol_metrics
        )
        
        if request.output.include_equity_curve and combined_equity is not None:
            result.equity_curve = combined_equity.tolist()
        
        if request.output.include_trades:
            result.trades = trades_list
        
        return result
    
    def _execute_strategy(
        self,
        ohlcv: np.ndarray,
        strategy_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute strategy on GPU
        
        Args:
            ohlcv: OHLCV data as numpy array
            strategy_name: Strategy name
            parameters: Strategy parameters
            
        Returns:
            Tuple of (signals, positions) arrays
        """
        if CUDA_AVAILABLE and strategy_name in self.kernels:
            # Execute on GPU using PyCUDA
            return self._execute_on_gpu(ohlcv, strategy_name, parameters)
        elif CUPY_AVAILABLE:
            # Execute on GPU using CuPy
            return self._execute_on_cupy(ohlcv, strategy_name, parameters)
        else:
            # Fall back to CPU
            return self._execute_on_cpu(ohlcv, strategy_name, parameters)
    
    def _execute_on_gpu(
        self,
        ohlcv: np.ndarray,
        strategy_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute strategy on GPU using PyCUDA
        """
        n_bars = ohlcv.shape[0]
        
        # Allocate memory on GPU
        d_ohlcv = cuda.mem_alloc(ohlcv.nbytes)
        d_signals = cuda.mem_alloc(n_bars * 4)  # float32
        d_positions = cuda.mem_alloc(n_bars * 4)  # float32
        
        # Initialize output arrays
        h_signals = np.zeros(n_bars, dtype=np.float32)
        h_positions = np.zeros(n_bars, dtype=np.float32)
        
        # Copy data to GPU
        cuda.memcpy_htod(d_ohlcv, ohlcv.astype(np.float32))
        
        # Set up grid and block dimensions
        block_size = 256
        grid_size = (n_bars + block_size - 1) // block_size
        
        # Get kernel function
        kernel_func = self.kernels[strategy_name]
        
        # Call appropriate kernel with parameters
        if strategy_name == "MovingAverageCrossover":
            short_window = int(parameters.get("short_window", 20))
            long_window = int(parameters.get("long_window", 50))
            signal_threshold = float(parameters.get("signal_threshold", 0.01))
            
            kernel_func(
                d_ohlcv,
                np.int32(n_bars),
                np.int32(short_window),
                np.int32(long_window),
                np.float32(signal_threshold),
                d_signals,
                d_positions,
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )
        elif strategy_name == "BollingerBands":
            window = int(parameters.get("window", 20))
            num_std = float(parameters.get("num_std", 2.0))
            
            kernel_func(
                d_ohlcv,
                np.int32(n_bars),
                np.int32(window),
                np.float32(num_std),
                d_signals,
                d_positions,
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )
        elif strategy_name == "MomentumStrategy":
            window = int(parameters.get("window", 14))
            threshold = float(parameters.get("threshold", 0.0))
            
            kernel_func(
                d_ohlcv,
                np.int32(n_bars),
                np.int32(window),
                np.float32(threshold),
                d_signals,
                d_positions,
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )
        elif strategy_name == "MeanReversion":
            window = int(parameters.get("window", 20))
            entry_threshold = float(parameters.get("entry_threshold", 1.5))
            exit_threshold = float(parameters.get("exit_threshold", 0.5))
            
            kernel_func(
                d_ohlcv,
                np.int32(n_bars),
                np.int32(window),
                np.float32(entry_threshold),
                np.float32(exit_threshold),
                d_signals,
                d_positions,
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )
        
        # Copy results back from GPU
        cuda.memcpy_dtoh(h_signals, d_signals)
        cuda.memcpy_dtoh(h_positions, d_positions)
        
        return h_signals, h_positions
    
    def _execute_on_cupy(
        self,
        ohlcv: np.ndarray,
        strategy_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute strategy on GPU using CuPy
        """
        import cupy as cp
        
        # Transfer data to GPU
        d_ohlcv = cp.array(ohlcv, dtype=cp.float32)
        n_bars = len(d_ohlcv)
        
        # Initialize output arrays
        d_signals = cp.zeros(n_bars, dtype=cp.float32)
        d_positions = cp.zeros(n_bars, dtype=cp.float32)
        
        # Extract close prices
        close = d_ohlcv[:, 3]
        
        # Execute strategy logic
        if strategy_name == "MovingAverageCrossover":
            short_window = int(parameters.get("short_window", 20))
            long_window = int(parameters.get("long_window", 50))
            signal_threshold = float(parameters.get("signal_threshold", 0.01))
            
            # Calculate moving averages
            short_ma = cp.convolve(close, cp.ones(short_window)/short_window, mode='valid')
            long_ma = cp.convolve(close, cp.ones(long_window)/long_window, mode='valid')
            
            # Pad shorter array to match lengths
            pad_length = max(short_window, long_window) - 1
            short_ma = cp.pad(short_ma, (pad_length, 0), 'constant', constant_values=cp.nan)
            long_ma = cp.pad(long_ma, (pad_length, 0), 'constant', constant_values=cp.nan)
            
            # Generate signals when short MA crosses above/below long MA
            d_signals[long_window:] = cp.sign(short_ma[long_window:] - long_ma[long_window:])
            
            # Apply signal threshold
            d_signals = cp.where(cp.abs(short_ma - long_ma) < signal_threshold * close, 0, d_signals)
            
        elif strategy_name == "BollingerBands":
            window = int(parameters.get("window", 20))
            num_std = float(parameters.get("num_std", 2.0))
            
            # Calculate moving average and standard deviation
            ma = cp.convolve(close, cp.ones(window)/window, mode='valid')
            ma = cp.pad(ma, (window-1, 0), 'constant', constant_values=cp.nan)
            
            # Calculate rolling standard deviation
            rolled = cp.lib.stride_tricks.as_strided(
                close,
                shape=(len(close) - window + 1, window),
                strides=(close.itemsize, close.itemsize)
            )
            std = cp.std(rolled, axis=1)
            std = cp.pad(std, (window-1, 0), 'constant', constant_values=cp.nan)
            
            # Calculate Bollinger Bands
            upper_band = ma + num_std * std
            lower_band = ma - num_std * std
            
            # Generate signals
            d_signals = cp.zeros_like(close)
            d_signals[window:] = cp.where(
                close[window:] < lower_band[window:], 1,  # Buy signal
                cp.where(
                    close[window:] > upper_band[window:], -1,  # Sell signal
                    0
                )
            )
            
        elif strategy_name == "MomentumStrategy":
            window = int(parameters.get("window", 14))
            threshold = float(parameters.get("threshold", 0.0))
            
            # Calculate momentum (close price change over window)
            momentum = cp.zeros_like(close)
            momentum[window:] = close[window:] / close[:-window] - 1
            
            # Generate signals based on momentum and threshold
            d_signals = cp.where(
                momentum > threshold, 1,  # Buy signal
                cp.where(
                    momentum < -threshold, -1,  # Sell signal
                    0
                )
            )
            
        elif strategy_name == "MeanReversion":
            window = int(parameters.get("window", 20))
            entry_threshold = float(parameters.get("entry_threshold", 1.5))
            exit_threshold = float(parameters.get("exit_threshold", 0.5))
            
            # Calculate moving average and standard deviation
            ma = cp.convolve(close, cp.ones(window)/window, mode='valid')
            ma = cp.pad(ma, (window-1, 0), 'constant', constant_values=cp.nan)
            
            # Calculate rolling standard deviation
            rolled = cp.lib.stride_tricks.as_strided(
                close,
                shape=(len(close) - window + 1, window),
                strides=(close.itemsize, close.itemsize)
            )
            std = cp.std(rolled, axis=1)
            std = cp.pad(std, (window-1, 0), 'constant', constant_values=cp.nan)
            
            # Calculate z-score (deviation from mean in terms of standard deviations)
            z_score = (close - ma) / std
            
            # Generate signals
            d_signals = cp.zeros_like(close)
            d_signals[window:] = cp.where(
                z_score[window:] < -entry_threshold, 1,  # Buy when price is below mean
                cp.where(
                    z_score[window:] > entry_threshold, -1,  # Sell when price is above mean
                    cp.where(
                        cp.abs(z_score[window:]) < exit_threshold, 0,  # Exit when price returns near mean
                        cp.nan  # Maintain previous position
                    )
                )
            )
            
            # Forward fill NaN values
            mask = cp.isnan(d_signals)
            indices = cp.where(~mask, cp.arange(len(d_signals)), 0)
            cp.maximum.accumulate(indices, out=indices)
            d_signals = cp.where(mask, d_signals[indices], d_signals)
        
        # Convert signals to positions (cumulative signal)
        for i in range(1, n_bars):
            if d_signals[i] != 0:
                d_positions[i] = d_signals[i]
            else:
                d_positions[i] = d_positions[i-1]
        
        # Transfer results back to CPU
        h_signals = cp.asnumpy(d_signals)
        h_positions = cp.asnumpy(d_positions)
        
        return h_signals, h_positions
    
    def _execute_on_cpu(
        self,
        ohlcv: np.ndarray,
        strategy_name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute strategy on CPU (fallback)
        """
        # Convert to pandas DataFrame for easier calculations
        df = pd.DataFrame(
            ohlcv,
            columns=['open', 'high', 'low', 'close', 'volume']
        )
        
        n_bars = len(df)
        signals = np.zeros(n_bars)
        positions = np.zeros(n_bars)
        
        if strategy_name == "MovingAverageCrossover":
            short_window = int(parameters.get("short_window", 20))
            long_window = int(parameters.get("long_window", 50))
            signal_threshold = float(parameters.get("signal_threshold", 0.01))
            
            # Calculate moving averages
            df['short_ma'] = df['close'].rolling(window=short_window).mean()
            df['long_ma'] = df['close'].rolling(window=long_window).mean()
            
            # Generate signals
            previous_position = 0
            for i in range(long_window, n_bars):
                if df['short_ma'].iloc[i] > df['long_ma'].iloc[i] and \
                   abs(df['short_ma'].iloc[i] - df['long_ma'].iloc[i]) > signal_threshold * df['close'].iloc[i]:
                    signals[i] = 1  # Buy signal
                    positions[i] = 1
                elif df['short_ma'].iloc[i] < df['long_ma'].iloc[i] and \
                     abs(df['short_ma'].iloc[i] - df['long_ma'].iloc[i]) > signal_threshold * df['close'].iloc[i]:
                    signals[i] = -1  # Sell signal
                    positions[i] = -1
                else:
                    signals[i] = 0
                    positions[i] = previous_position
                previous_position = positions[i]
        
        elif strategy_name == "BollingerBands":
            window = int(parameters.get("window", 20))
            num_std = float(parameters.get("num_std", 2.0))
            
            # Calculate Bollinger Bands
            df['ma'] = df['close'].rolling(window=window).mean()
            df['std'] = df['close'].rolling(window=window).std()
            df['upper'] = df['ma'] + num_std * df['std']
            df['lower'] = df['ma'] - num_std * df['std']
            
            # Generate signals
            previous_position = 0
            for i in range(window, n_bars):
                if df['close'].iloc[i] < df['lower'].iloc[i]:
                    signals[i] = 1  # Buy signal
                    positions[i] = 1
                elif df['close'].iloc[i] > df['upper'].iloc[i]:
                    signals[i] = -1  # Sell signal
                    positions[i] = -1
                else:
                    signals[i] = 0
                    positions[i] = previous_position
                previous_position = positions[i]
        
        elif strategy_name == "MomentumStrategy":
            window = int(parameters.get("window", 14))
            threshold = float(parameters.get("threshold", 0.0))
            
            # Calculate momentum
            df['momentum'] = df['close'].pct_change(periods=window)
            
            # Generate signals
            previous_position = 0
            for i in range(window, n_bars):
                if df['momentum'].iloc[i] > threshold:
                    signals[i] = 1  # Buy signal
                    positions[i] = 1
                elif df['momentum'].iloc[i] < -threshold:
                    signals[i] = -1  # Sell signal
                    positions[i] = -1
                else:
                    signals[i] = 0
                    positions[i] = previous_position
                previous_position = positions[i]
        
        elif strategy_name == "MeanReversion":
            window = int(parameters.get("window", 20))
            entry_threshold = float(parameters.get("entry_threshold", 1.5))
            exit_threshold = float(parameters.get("exit_threshold", 0.5))
            
            # Calculate z-score
            df['ma'] = df['close'].rolling(window=window).mean()
            df['std'] = df['close'].rolling(window=window).std()
            df['z_score'] = (df['close'] - df['ma']) / df['std']
            
            # Generate signals
            previous_position = 0
            for i in range(window, n_bars):
                z = df['z_score'].iloc[i]
                if z < -entry_threshold:
                    signals[i] = 1  # Buy signal
                    positions[i] = 1
                elif z > entry_threshold:
                    signals[i] = -1  # Sell signal
                    positions[i] = -1
                elif abs(z) < exit_threshold:
                    signals[i] = 0  # Exit signal
                    positions[i] = 0
                else:
                    signals[i] = 0
                    positions[i] = previous_position
                previous_position = positions[i]
        
        return signals, positions
    
    def _generate_trades(
        self,
        symbol: str,
        dates: np.ndarray,
        ohlcv: np.ndarray,
        positions: np.ndarray,
        initial_capital: float,
        position_size_spec: str,
        commission: float,
        slippage: float
    ) -> List[Trade]:
        """
        Generate trade records from position signals
        """
        trades = []
        position_size = 0
        entry_price = 0
        entry_date = None
        current_position = 0
        
        # Determine position size
        if position_size_spec.endswith("%"):
            # Percentage of capital
            pct = float(position_size_spec.rstrip("%")) / 100.0
            position_size = initial_capital * pct
        else:
            # Fixed dollar amount
            position_size = float(position_size_spec)
        
        for i in range(1, len(positions)):
            if positions[i] != positions[i-1]:
                # Position changed
                new_position = positions[i]
                
                # Close existing position if any
                if current_position != 0:
                    # Calculate exit price with slippage
                    exit_price = ohlcv[i, 3]  # close price
                    if current_position > 0:
                        exit_price = exit_price * (1 - slippage)  # selling, so lower price
                    else:
                        exit_price = exit_price * (1 + slippage)  # buying to cover, so higher price
                    
                    # Calculate shares and P&L
                    shares = position_size / abs(entry_price)
                    pnl = shares * (exit_price - entry_price) * np.sign(current_position)
                    
                    # Subtract commission
                    pnl -= commission * position_size
                    
                    # Create trade record
                    trade = Trade(
                        symbol=symbol,
                        entry_date=entry_date.astype('datetime64[D]').astype(str),
                        exit_date=dates[i].astype('datetime64[D]').astype(str),
                        entry_price=float(entry_price),
                        exit_price=float(exit_price),
                        position_size=float(position_size * np.sign(current_position)),
                        pnl=float(pnl)
                    )
                    trades.append(trade)
                
                # Enter new position if not zero
                if new_position != 0:
                    # Calculate entry price with slippage
                    entry_price = ohlcv[i, 3]  # close price
                    if new_position > 0:
                        entry_price = entry_price * (1 + slippage)  # buying, so higher price
                    else:
                        entry_price = entry_price * (1 - slippage)  # selling short, so lower price
                    
                    entry_date = dates[i]
                    current_position = new_position
                else:
                    current_position = 0
        
        # Close any open position at the end
        if current_position != 0:
            # Use last price as exit
            exit_price = ohlcv[-1, 3]
            if current_position > 0:
                exit_price = exit_price * (1 - slippage)
            else:
                exit_price = exit_price * (1 + slippage)
            
            shares = position_size / abs(entry_price)
            pnl = shares * (exit_price - entry_price) * np.sign(current_position)
            pnl -= commission * position_size
            
            trade = Trade(
                symbol=symbol,
                entry_date=entry_date.astype('datetime64[D]').astype(str),
                exit_date=dates[-1].astype('datetime64[D]').astype(str),
                entry_price=float(entry_price),
                exit_price=float(exit_price),
                position_size=float(position_size * np.sign(current_position)),
                pnl=float(pnl)
            )
            trades.append(trade)
        
        return trades
    
    def _calculate_equity_curve(
        self,
        positions: np.ndarray,
        prices: np.ndarray,
        initial_capital: float,
        commission: float,
        slippage: float
    ) -> np.ndarray:
        """
        Calculate equity curve from positions and prices
        """
        equity = np.zeros(len(positions))
        equity[0] = initial_capital
        position = 0
        entry_price = 0
        shares = 0
        
        for i in range(1, len(positions)):
            # Check if position changed
            if positions[i] != positions[i-1]:
                # Calculate exit price for old position
                if position != 0:
                    exit_price = prices[i]
                    if position > 0:
                        exit_price = exit_price * (1 - slippage)  # selling, so lower price
                    else:
                        exit_price = exit_price * (1 + slippage)  # buying to cover, so higher price
                    
                    # Calculate P&L
                    pnl = shares * (exit_price - entry_price) * np.sign(position)
                    
                    # Subtract commission
                    pnl -= commission * (shares * abs(entry_price))
                    
                    # Update equity
                    equity[i] = equity[i-1] + pnl
                else:
                    equity[i] = equity[i-1]
                
                # Enter new position
                position = positions[i]
                if position != 0:
                    # Calculate entry price
                    entry_price = prices[i]
                    if position > 0:
                        entry_price = entry_price * (1 + slippage)  # buying, so higher price
                    else:
                        entry_price = entry_price * (1 - slippage)  # selling short, so lower price
                    
                    # Calculate shares (use fixed percentage of capital)
                    position_size = 0.1 * equity[i]  # 10% of capital
                    shares = position_size / abs(entry_price)
                    
                    # Subtract commission
                    equity[i] -= commission * position_size
            else:
                # Position unchanged, calculate unrealized P&L
                if position != 0:
                    current_price = prices[i]
                    unrealized_pnl = shares * (current_price - entry_price) * np.sign(position)
                    equity[i] = equity[i-1] + (unrealized_pnl - equity[i-1] * (position != 0))
                else:
                    equity[i] = equity[i-1]
        
        return equity