import numpy as np
import pandas as pd
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
from typing import Dict, Tuple, Any
from strategies.base import BaseStrategy
from engine.cuda_kernels import mean_reversion_kernel
import logging

logger = logging.getLogger(__name__)

class MeanReversion(BaseStrategy):
    """
    Mean Reversion strategy implementation
    
    Generates buy signals when price is significantly below the mean,
    and sell signals when price is significantly above the mean.
    """
    
    def __init__(self):
        """
        Initialize the strategy
        """
        super().__init__("MeanReversion")
        self.kernel_func = mean_reversion_kernel.get_function("mean_reversion")
    
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
        window = int(parameters.get('window', 30))
        z_threshold = float(parameters.get('z_threshold', 1.5))
        
        # Validate parameters
        if window < 5:
            raise ValueError("window must be at least 5")
        if z_threshold <= 0:
            raise ValueError("z_threshold must be positive")
        
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
                np.int32(window),
                np.float32(z_threshold),
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
            logger.error(f"Error executing MeanReversion strategy on GPU: {str(e)}")
            raise RuntimeError(f"GPU execution failed: {str(e)}")
