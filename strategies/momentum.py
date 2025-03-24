import numpy as np
import pandas as pd
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
from typing import Dict, Tuple, Any
from strategies.base import BaseStrategy
from engine.cuda_kernels import momentum_kernel
import logging

logger = logging.getLogger(__name__)

class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy implementation
    
    Generates buy signals when momentum is above threshold,
    and sell signals when momentum is below negative threshold.
    """
    
    def __init__(self):
        """
        Initialize the strategy
        """
        super().__init__("MomentumStrategy")
        self.kernel_func = momentum_kernel.get_function("momentum_strategy")
    
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
        momentum_window = int(parameters.get('momentum_window', 14))
        threshold = float(parameters.get('threshold', 0.05))
        
        # Validate parameters
        if momentum_window < 2:
            raise ValueError("momentum_window must be at least 2")
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        
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
                np.int32(momentum_window),
                np.float32(threshold),
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
            logger.error(f"Error executing Momentum strategy on GPU: {str(e)}")
            raise RuntimeError(f"GPU execution failed: {str(e)}")
