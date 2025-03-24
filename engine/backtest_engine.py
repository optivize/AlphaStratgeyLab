import logging
import pandas as pd
import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
from typing import Dict, List, Any
from datetime import datetime
from core.models import (
    BacktestResult,
    BacktestMetrics,
    SymbolMetrics,
    TradeRecord,
    StrategyDefinition,
    ExecutionParams
)
from engine.cuda_kernels import (
    moving_average_kernel,
    bollinger_bands_kernel,
    momentum_kernel,
    mean_reversion_kernel
)
from utils.metrics import calculate_metrics
from strategies.base import get_strategy_instance

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    GPU-accelerated backtesting engine
    """
    
    def __init__(self):
        """
        Initialize the backtest engine with CUDA context
        """
        logger.info("Initializing GPU Backtesting Engine")
        
        # Set up CUDA device and context
        try:
            self.cuda_device = cuda.Device(0)  # Use the first available GPU
            self.cuda_context = self.cuda_device.make_context()
            self.device_props = cuda.Device.get_attributes(self.cuda_device)
            
            logger.info(f"Using GPU: {self.cuda_device.name()}")
            logger.info(f"CUDA Compute Capability: {self.cuda_device.compute_capability()}")
            logger.info(f"Total GPU Memory: {self.cuda_device.total_memory() / 1024**2} MB")
            
        except Exception as e:
            logger.error(f"Error initializing CUDA: {str(e)}")
            raise RuntimeError(f"Failed to initialize CUDA: {str(e)}")
    
    def __del__(self):
        """
        Clean up CUDA resources
        """
        if hasattr(self, 'cuda_context'):
            self.cuda_context.pop()
    
    def run_backtest(
        self, 
        data: Dict[str, pd.DataFrame],
        strategy: StrategyDefinition,
        execution_params: ExecutionParams,
        output_metrics: List[str]
    ) -> BacktestResult:
        """
        Run a backtest with the given parameters
        
        Args:
            data: Dictionary of DataFrames with historical price data for each symbol
            strategy: Strategy definition with parameters
            execution_params: Execution parameters for the backtest
            output_metrics: List of metrics to calculate
            
        Returns:
            BacktestResult object with metrics and trade data
        """
        logger.info(f"Starting backtest with strategy: {strategy.name}")
        start_time = datetime.now()
        
        try:
            # Get the strategy implementation
            strategy_instance = get_strategy_instance(strategy.name)
            
            # Initialize results containers
            all_positions = {}
            all_trades = []
            equity_curve = [execution_params.initial_capital]
            current_equity = execution_params.initial_capital
            
            # Process each symbol with GPU acceleration
            for symbol, df in data.items():
                logger.debug(f"Processing symbol: {symbol}")
                
                # Prepare data for GPU processing
                dates = df.index.values
                ohlcv = np.vstack([
                    df['open'].values,
                    df['high'].values,
                    df['low'].values,
                    df['close'].values,
                    df['volume'].values
                ]).T.astype(np.float32)
                
                # Run the strategy on GPU
                signals, positions = strategy_instance.execute_on_gpu(
                    ohlcv, 
                    strategy.parameters
                )
                
                # Track positions
                all_positions[symbol] = positions
                
                # Generate trades from positions
                trades = self._generate_trades(symbol, dates, ohlcv, positions)
                all_trades.extend(trades)
                
                # Update equity curve (simplified)
                for trade in trades:
                    if trade.pnl is not None:
                        current_equity += trade.pnl
                        equity_curve.append(float(current_equity))
            
            # Calculate performance metrics
            overall_metrics, symbol_metrics = calculate_metrics(
                all_trades, 
                all_positions, 
                data, 
                execution_params.initial_capital,
                output_metrics
            )
            
            # Create and return results
            result = BacktestResult(
                overall_metrics=overall_metrics,
                per_symbol_metrics=symbol_metrics,
                equity_curve=equity_curve if len(equity_curve) > 1 else None,
                trades=all_trades
            )
            
            logger.info(f"Backtest completed in {(datetime.now() - start_time).total_seconds()} seconds")
            return result
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            raise RuntimeError(f"Backtest execution failed: {str(e)}")
    
    def _generate_trades(
        self, 
        symbol: str, 
        dates: np.ndarray, 
        ohlcv: np.ndarray, 
        positions: np.ndarray
    ) -> List[TradeRecord]:
        """
        Generate trade records from position signals
        """
        trades = []
        in_position = False
        entry_date = None
        entry_price = None
        entry_idx = None
        position_size = 100  # Simplified for this example
        
        for i in range(1, len(positions)):
            # New position
            if not in_position and positions[i] != 0:
                in_position = True
                entry_idx = i
                entry_date = str(dates[i])
                entry_price = float(ohlcv[i, 3])  # Close price
            
            # Exit position
            elif in_position and (positions[i] == 0 or i == len(positions) - 1):
                in_position = False
                exit_date = str(dates[i])
                exit_price = float(ohlcv[i, 3])  # Close price
                
                # Calculate P&L
                pnl = (exit_price - entry_price) * position_size
                if positions[entry_idx] < 0:  # Short position
                    pnl = -pnl
                
                # Create trade record
                trade = TradeRecord(
                    symbol=symbol,
                    entry_date=entry_date,
                    exit_date=exit_date,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    position_size=position_size,
                    pnl=float(pnl)
                )
                trades.append(trade)
        
        return trades
