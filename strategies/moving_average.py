import numpy as np
import pandas as pd
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
from typing import Dict, Tuple, Any
from strategies.base import BaseStrategy
from engine.cuda_kernels import moving_average_kernel
import logging

logger = logging.getLogger(__name__)

class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy implementation
    
    Generates buy signals when short-term MA crosses above long-term MA,
    and sell signals when short-term MA crosses below long-term MA.
    """
    
    def __init__(self):
        """
        Initialize the strategy
        """
        super().__init__("MovingAverageCrossover")
        self.kernel_func = moving_average_kernel.get_function("moving_average_crossover")
    
    def execute_on_gpu(
        self, 
        ohlcv: np.ndarray, 
        parameters: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Execute the strategy on GPU
        
        Args:
            ohlcv: OHLCV data as numpy array [n_bars, 5]
            parameters: Strategy parameters dictionary
            
        Returns:
            Tuple of (signals, positions) as numpy arrays
        """
        # Extract parameters with defaults
        short_window = int(parameters.get('short_window', 20))
        long_window = int(parameters.get('long_window', 50))
        signal_threshold = float(parameters.get('signal_threshold', 0.01))
        
        # Validate parameters
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        if short_window < 2:
            raise ValueError("short_window must be at least 2")
        
        # Prepare data for GPU
        n_bars = ohlcv.shape[0]
        close_prices = ohlcv[:, 3].astype(np.float32)  # Use close prices
        
        # Allocate GPU arrays
        d_ohlcv = gpuarray.to_gpu(close_prices)
        d_signals = gpuarray.zeros(n_bars, dtype=np.float32)
        d_positions = gpuarray.zeros(n_bars, dtype=np.float32)
        
        # Set up grid and block dimensions
        block_size = 256
        grid_size = (n_bars + block_size - 1) // block_size
        
        # Execute kernel
        try:
            self.kernel_func(
                d_ohlcv.gpudata,
                np.int32(n_bars),
                np.int32(short_window),
                np.int32(long_window),
                np.float32(signal_threshold),
                d_signals.gpudata,
                d_positions.gpudata,
                block=(block_size, 1, 1),
                grid=(grid_size, 1)
            )
            
            # Transfer results back to CPU
            signals = d_signals.get()
            positions = d_positions.get()
            
            return signals, positions
            
        except Exception as e:
            logger.error(f"Error executing MovingAverageCrossover strategy on GPU: {str(e)}")
            raise RuntimeError(f"GPU execution failed: {str(e)}")
