import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule
import logging

logger = logging.getLogger(__name__)

# CUDA kernel for Moving Average Crossover strategy
moving_average_kernel = SourceModule("""
    __global__ void moving_average_crossover(
        float *ohlcv,        // Input OHLCV data [n_bars, 5]
        int n_bars,          // Number of bars
        int short_window,    // Short moving average window
        int long_window,     // Long moving average window
        float signal_threshold, // Signal threshold
        float *signals,      // Output signals [-1, 0, 1]
        float *positions     // Output positions [-1, 0, 1]
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        if (idx >= n_bars) return;
        
        // Initialize signals and positions
        signals[idx] = 0.0f;
        positions[idx] = 0.0f;
        
        // Need at least long_window bars to calculate signals
        if (idx < long_window) return;
        
        // Calculate short moving average
        float short_ma = 0.0f;
        for (int i = 0; i < short_window; i++) {
            short_ma += ohlcv[idx - i];
        }
        short_ma /= short_window;
        
        // Calculate long moving average
        float long_ma = 0.0f;
        for (int i = 0; i < long_window; i++) {
            long_ma += ohlcv[idx - i];
        }
        long_ma /= long_window;
        
        // Generate signal based on crossover
        float diff = short_ma - long_ma;
        
        if (diff > signal_threshold) {
            signals[idx] = 1.0f;  // Buy signal
        } else if (diff < -signal_threshold) {
            signals[idx] = -1.0f; // Sell signal
        }
        
        // Set position based on signal
        if (idx > 0) {
            if (signals[idx] != 0.0f) {
                positions[idx] = signals[idx];
            } else {
                positions[idx] = positions[idx - 1];
            }
        }
    }
""")

# CUDA kernel for Bollinger Bands strategy
bollinger_bands_kernel = SourceModule("""
    __global__ void bollinger_bands(
        float *ohlcv,       // Input OHLCV data [n_bars, 5]
        int n_bars,         // Number of bars
        int window,         // Window size for moving average
        float num_std,      // Number of standard deviations
        float *signals,     // Output signals
        float *positions    // Output positions
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        if (idx >= n_bars) return;
        
        // Initialize
        signals[idx] = 0.0f;
        positions[idx] = 0.0f;
        
        // Need at least window bars to calculate
        if (idx < window) return;
        
        // Calculate moving average
        float ma = 0.0f;
        for (int i = 0; i < window; i++) {
            ma += ohlcv[idx - i];
        }
        ma /= window;
        
        // Calculate standard deviation
        float variance = 0.0f;
        for (int i = 0; i < window; i++) {
            float diff = ohlcv[idx - i] - ma;
            variance += diff * diff;
        }
        variance /= window;
        float std_dev = sqrt(variance);
        
        // Calculate Bollinger Bands
        float upper_band = ma + num_std * std_dev;
        float lower_band = ma - num_std * std_dev;
        
        // Generate signals
        float current_price = ohlcv[idx];
        
        if (current_price > upper_band) {
            signals[idx] = -1.0f;  // Sell signal (overbought)
        } else if (current_price < lower_band) {
            signals[idx] = 1.0f;   // Buy signal (oversold)
        }
        
        // Set position based on signal
        if (idx > 0) {
            if (signals[idx] != 0.0f) {
                positions[idx] = signals[idx];
            } else {
                positions[idx] = positions[idx - 1];
            }
        }
    }
""")

# CUDA kernel for Momentum strategy
momentum_kernel = SourceModule("""
    __global__ void momentum_strategy(
        float *ohlcv,           // Input OHLCV data [n_bars, 5]
        int n_bars,             // Number of bars
        int momentum_window,    // Window for momentum calculation
        float threshold,        // Signal threshold
        float *signals,         // Output signals
        float *positions        // Output positions
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        if (idx >= n_bars) return;
        
        // Initialize
        signals[idx] = 0.0f;
        positions[idx] = 0.0f;
        
        // Need at least momentum_window bars
        if (idx < momentum_window) return;
        
        // Calculate momentum (price change over window)
        float current_price = ohlcv[idx];
        float past_price = ohlcv[idx - momentum_window];
        
        float momentum = (current_price - past_price) / past_price;
        
        // Generate signal based on momentum
        if (momentum > threshold) {
            signals[idx] = 1.0f;  // Buy signal
        } else if (momentum < -threshold) {
            signals[idx] = -1.0f; // Sell signal
        }
        
        // Set position based on signal
        if (idx > 0) {
            if (signals[idx] != 0.0f) {
                positions[idx] = signals[idx];
            } else {
                positions[idx] = positions[idx - 1];
            }
        }
    }
""")

# CUDA kernel for Mean Reversion strategy
mean_reversion_kernel = SourceModule("""
    __global__ void mean_reversion(
        float *ohlcv,        // Input OHLCV data [n_bars, 5]
        int n_bars,          // Number of bars
        int window,          // Window for mean calculation
        float z_threshold,   // Z-score threshold for signals
        float *signals,      // Output signals
        float *positions     // Output positions
    ) {
        int idx = blockIdx.x * blockDim.x + threadIdx.x;
        
        if (idx >= n_bars) return;
        
        // Initialize
        signals[idx] = 0.0f;
        positions[idx] = 0.0f;
        
        // Need at least window bars
        if (idx < window) return;
        
        // Calculate mean
        float mean = 0.0f;
        for (int i = 0; i < window; i++) {
            mean += ohlcv[idx - i];
        }
        mean /= window;
        
        // Calculate standard deviation
        float variance = 0.0f;
        for (int i = 0; i < window; i++) {
            float diff = ohlcv[idx - i] - mean;
            variance += diff * diff;
        }
        variance /= window;
        float std_dev = sqrt(variance);
        
        if (std_dev == 0.0f) return;  // Avoid division by zero
        
        // Calculate z-score
        float current_price = ohlcv[idx];
        float z_score = (current_price - mean) / std_dev;
        
        // Generate signals based on z-score
        if (z_score > z_threshold) {
            signals[idx] = -1.0f;  // Sell signal (price above mean)
        } else if (z_score < -z_threshold) {
            signals[idx] = 1.0f;   // Buy signal (price below mean)
        }
        
        // Set position based on signal
        if (idx > 0) {
            if (signals[idx] != 0.0f) {
                positions[idx] = signals[idx];
            } else {
                positions[idx] = positions[idx - 1];
            }
        }
    }
""")

def get_kernel_function(strategy_name):
    """
    Get the appropriate CUDA kernel function for a strategy
    """
    if strategy_name == "MovingAverageCrossover":
        return moving_average_kernel.get_function("moving_average_crossover")
    elif strategy_name == "BollingerBands":
        return bollinger_bands_kernel.get_function("bollinger_bands")
    elif strategy_name == "MomentumStrategy":
        return momentum_kernel.get_function("momentum_strategy")
    elif strategy_name == "MeanReversion":
        return mean_reversion_kernel.get_function("mean_reversion")
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")
