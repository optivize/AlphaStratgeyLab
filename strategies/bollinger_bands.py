import numpy as np
import pandas as pd
import pycuda.driver as cuda
import pycuda.gpuarray as gpuarray
from typing import Dict, Tuple, Any
from strategies.base import BaseStrategy
from engine.cuda_kernels import bollinger_bands_kernel
import logging

logger = logging.getLogger(__name__)

class BollingerBands(BaseStrategy):
    """
    Bollinger Bands strategy implementation
    
    Generates buy signals when price crosses below the lower band,
    and sell signals when price crosses above the upper band.
    """
    
    def __init__(self):
        """
        Initialize the strategy
        """
        super().__init__("BollingerBands")
        self.kernel_func = bollinger_bands_kernel.get_function("bollinger_bands")
    
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
        window = int(parameters.get('window', 20))
        num_std = float(parameters.get('num_std', 2.0))
        
        # Validate parameters
        if window < 2:
            raise ValueError("window must be at least 2")
        if num_std <= 0:
            raise ValueError("num_std must be positive")
        
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
                np.float32(num_std),
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
            logger.error(f"Error executing BollingerBands strategy on GPU: {str(e)}")
            raise RuntimeError(f"GPU execution failed: {str(e)}")
