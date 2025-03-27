"""
CUDA kernel functions for GPU-accelerated strategy execution
"""
import logging

logger = logging.getLogger(__name__)

def get_cuda_kernel(strategy_name: str) -> str:
    """
    Get CUDA kernel code for a specific strategy
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        CUDA C code as string
    """
    if strategy_name == "moving_average":
        return _get_moving_average_kernel()
    elif strategy_name == "bollinger_bands":
        return _get_bollinger_bands_kernel()
    elif strategy_name == "momentum":
        return _get_momentum_kernel()
    elif strategy_name == "mean_reversion":
        return _get_mean_reversion_kernel()
    else:
        raise ValueError(f"No CUDA kernel available for strategy: {strategy_name}")

def _get_moving_average_kernel() -> str:
    """
    CUDA kernel for Moving Average Crossover strategy
    """
    return '''
    #include <stdio.h>
    
    __global__ void moving_avg_crossover(
        float *ohlcv,
        int n_bars,
        int short_window,
        int long_window,
        float signal_threshold,
        float *signals,
        float *positions
    ) {
        // Calculate thread index
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        // Check if thread is within data range
        if (idx >= n_bars) {
            return;
        }
        
        // Initialize signals and positions to zero
        signals[idx] = 0.0f;
        
        // We need at least long_window bars for the strategy
        if (idx < long_window) {
            positions[idx] = 0.0f;
            return;
        }
        
        // Calculate short-term moving average
        float short_ma = 0.0f;
        for (int i = 0; i < short_window; i++) {
            short_ma += ohlcv[(idx - short_window + 1 + i) * 5 + 3]; // Close price at index 3
        }
        short_ma /= short_window;
        
        // Calculate long-term moving average
        float long_ma = 0.0f;
        for (int i = 0; i < long_window; i++) {
            long_ma += ohlcv[(idx - long_window + 1 + i) * 5 + 3]; // Close price at index 3
        }
        long_ma /= long_window;
        
        // Current close price
        float close = ohlcv[idx * 5 + 3];
        
        // Generate signal based on moving average crossover
        if (short_ma > long_ma && fabsf(short_ma - long_ma) > signal_threshold * close) {
            signals[idx] = 1.0f; // Buy signal
        } else if (short_ma < long_ma && fabsf(short_ma - long_ma) > signal_threshold * close) {
            signals[idx] = -1.0f; // Sell signal
        }
        
        // Calculate position (1 for long, -1 for short, 0 for no position)
        if (signals[idx] != 0.0f) {
            positions[idx] = signals[idx];
        } else if (idx > 0) {
            positions[idx] = positions[idx - 1];
        } else {
            positions[idx] = 0.0f;
        }
    }
    '''

def _get_bollinger_bands_kernel() -> str:
    """
    CUDA kernel for Bollinger Bands strategy
    """
    return '''
    #include <stdio.h>
    #include <math.h>
    
    __global__ void bollinger_bands(
        float *ohlcv,
        int n_bars,
        int window,
        float num_std,
        float *signals,
        float *positions
    ) {
        // Calculate thread index
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        // Check if thread is within data range
        if (idx >= n_bars) {
            return;
        }
        
        // Initialize signals and positions to zero
        signals[idx] = 0.0f;
        
        // We need at least window bars for the strategy
        if (idx < window) {
            positions[idx] = 0.0f;
            return;
        }
        
        // Calculate moving average
        float ma = 0.0f;
        for (int i = 0; i < window; i++) {
            ma += ohlcv[(idx - window + 1 + i) * 5 + 3]; // Close price at index 3
        }
        ma /= window;
        
        // Calculate standard deviation
        float variance = 0.0f;
        for (int i = 0; i < window; i++) {
            float diff = ohlcv[(idx - window + 1 + i) * 5 + 3] - ma;
            variance += diff * diff;
        }
        variance /= window;
        float std_dev = sqrtf(variance);
        
        // Calculate Bollinger Bands
        float upper_band = ma + num_std * std_dev;
        float lower_band = ma - num_std * std_dev;
        
        // Current close price
        float close = ohlcv[idx * 5 + 3];
        
        // Generate signal based on price crossing Bollinger Bands
        if (close < lower_band) {
            signals[idx] = 1.0f; // Buy signal when price crosses below lower band
        } else if (close > upper_band) {
            signals[idx] = -1.0f; // Sell signal when price crosses above upper band
        }
        
        // Calculate position
        if (signals[idx] != 0.0f) {
            positions[idx] = signals[idx];
        } else if (idx > 0) {
            positions[idx] = positions[idx - 1];
        } else {
            positions[idx] = 0.0f;
        }
    }
    '''

def _get_momentum_kernel() -> str:
    """
    CUDA kernel for Momentum strategy
    """
    return '''
    #include <stdio.h>
    
    __global__ void momentum_strategy(
        float *ohlcv,
        int n_bars,
        int window,
        float threshold,
        float *signals,
        float *positions
    ) {
        // Calculate thread index
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        // Check if thread is within data range
        if (idx >= n_bars) {
            return;
        }
        
        // Initialize signals and positions to zero
        signals[idx] = 0.0f;
        
        // We need at least window bars for the strategy
        if (idx < window) {
            positions[idx] = 0.0f;
            return;
        }
        
        // Calculate momentum (percent change over window)
        float past_price = ohlcv[(idx - window) * 5 + 3]; // Close price at index 3
        float current_price = ohlcv[idx * 5 + 3];
        float momentum = (current_price / past_price) - 1.0f;
        
        // Generate signal based on momentum
        if (momentum > threshold) {
            signals[idx] = 1.0f; // Buy signal
        } else if (momentum < -threshold) {
            signals[idx] = -1.0f; // Sell signal
        }
        
        // Calculate position
        if (signals[idx] != 0.0f) {
            positions[idx] = signals[idx];
        } else if (idx > 0) {
            positions[idx] = positions[idx - 1];
        } else {
            positions[idx] = 0.0f;
        }
    }
    '''

def _get_mean_reversion_kernel() -> str:
    """
    CUDA kernel for Mean Reversion strategy
    """
    return '''
    #include <stdio.h>
    #include <math.h>
    
    __global__ void mean_reversion(
        float *ohlcv,
        int n_bars,
        int window,
        float entry_threshold,
        float exit_threshold,
        float *signals,
        float *positions
    ) {
        // Calculate thread index
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        // Check if thread is within data range
        if (idx >= n_bars) {
            return;
        }
        
        // Initialize signals and positions to zero
        signals[idx] = 0.0f;
        
        // We need at least window bars for the strategy
        if (idx < window) {
            positions[idx] = 0.0f;
            return;
        }
        
        // Calculate moving average
        float ma = 0.0f;
        for (int i = 0; i < window; i++) {
            ma += ohlcv[(idx - window + 1 + i) * 5 + 3]; // Close price at index 3
        }
        ma /= window;
        
        // Calculate standard deviation
        float variance = 0.0f;
        for (int i = 0; i < window; i++) {
            float diff = ohlcv[(idx - window + 1 + i) * 5 + 3] - ma;
            variance += diff * diff;
        }
        variance /= window;
        float std_dev = sqrtf(variance);
        
        // Current close price
        float close = ohlcv[idx * 5 + 3];
        
        // Calculate z-score (deviation from mean in terms of standard deviations)
        float z_score = (close - ma) / std_dev;
        
        // Generate signal based on z-score
        if (z_score < -entry_threshold) {
            signals[idx] = 1.0f; // Buy signal when price is significantly below mean
        } else if (z_score > entry_threshold) {
            signals[idx] = -1.0f; // Sell signal when price is significantly above mean
        } else if (fabsf(z_score) < exit_threshold) {
            signals[idx] = 0.0f; // Exit signal when price returns close to mean
        }
        
        // Calculate position
        if (signals[idx] != 0.0f) {
            positions[idx] = signals[idx];
        } else if (idx > 0 && fabsf(z_score) >= exit_threshold) {
            positions[idx] = positions[idx - 1]; // Maintain position
        } else {
            positions[idx] = 0.0f; // No position
        }
    }
    '''