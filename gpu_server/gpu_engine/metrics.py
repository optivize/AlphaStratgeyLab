"""
Performance metrics calculation for backtests
"""
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from models.job import Trade, Metrics, SymbolMetrics

logger = logging.getLogger(__name__)

try:
    # Try to import CUDA libraries
    import cupy as cp
    CUPY_AVAILABLE = True
    logger.info("CuPy is available for metrics calculation")
except ImportError:
    logger.warning("CuPy not available, using NumPy for metrics calculation")
    CUPY_AVAILABLE = False

def calculate_metrics(
    trades: List[Trade],
    positions: Dict[str, np.ndarray],
    price_data: Dict[str, pd.DataFrame],
    initial_capital: float,
    metrics_to_calculate: List[str]
) -> Tuple[Metrics, Dict[str, SymbolMetrics]]:
    """
    Calculate performance metrics for a backtest
    
    Args:
        trades: List of trade records
        positions: Dictionary of position arrays by symbol
        price_data: Dictionary of price DataFrames by symbol
        initial_capital: Initial capital amount
        metrics_to_calculate: List of metrics to calculate
    
    Returns:
        Tuple of (overall_metrics, per_symbol_metrics)
    """
    logger.info(f"Calculating {len(metrics_to_calculate)} metrics for {len(trades)} trades")
    
    # Group trades by symbol
    trades_by_symbol = {}
    for trade in trades:
        if trade.symbol not in trades_by_symbol:
            trades_by_symbol[trade.symbol] = []
        trades_by_symbol[trade.symbol].append(trade)
    
    # Calculate per-symbol metrics
    symbol_metrics = {}
    all_returns = []
    all_drawdowns = []
    
    for symbol, symbol_trades in trades_by_symbol.items():
        # Calculate metrics for this symbol
        symbol_result = _calculate_symbol_metrics(
            symbol_trades,
            positions.get(symbol, np.array([])),
            price_data.get(symbol, pd.DataFrame()),
            initial_capital / len(trades_by_symbol)
        )
        symbol_metrics[symbol] = symbol_result
        
        # Collect data for overall metrics
        if hasattr(symbol_result, 'returns'):
            all_returns.extend(symbol_result.returns)
        if hasattr(symbol_result, 'drawdowns'):
            all_drawdowns.append(symbol_result.drawdowns)
    
    # Calculate overall metrics
    overall_metrics = _calculate_overall_metrics(
        trades,
        all_returns,
        all_drawdowns,
        initial_capital,
        metrics_to_calculate
    )
    
    return overall_metrics, symbol_metrics

def _calculate_symbol_metrics(
    trades: List[Trade],
    positions: np.ndarray,
    price_data: pd.DataFrame,
    initial_capital: float
) -> SymbolMetrics:
    """
    Calculate metrics for a single symbol
    
    Returns:
        Symbol metrics object
    """
    # Extract trade data
    returns = [trade.pnl / initial_capital if trade.pnl else 0 for trade in trades]
    
    # Calculate total return
    total_return = sum(returns)
    
    # Calculate win rate
    winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
    win_rate = len(winning_trades) / len(trades) if trades else 0
    
    # Calculate average gain and loss
    gains = [t.pnl for t in trades if t.pnl and t.pnl > 0]
    losses = [t.pnl for t in trades if t.pnl and t.pnl < 0]
    
    avg_gain = sum(gains) / len(gains) if gains else None
    avg_loss = sum(losses) / len(losses) if losses else None
    
    # Calculate max drawdown if we have price data
    max_drawdown = None
    if not price_data.empty and 'close' in price_data.columns and len(positions) > 0:
        # Calculate equity curve
        equity_curve = _calculate_equity_curve(positions, price_data['close'].values, initial_capital)
        max_drawdown = _calculate_max_drawdown(equity_curve)
    
    # Calculate volatility
    volatility = np.std(returns) if returns else None
    
    # Create metrics object
    metrics = SymbolMetrics(
        total_return=total_return,
        win_rate=win_rate,
        avg_gain=avg_gain,
        avg_loss=avg_loss,
        max_drawdown=max_drawdown,
        volatility=volatility
    )
    
    # Attach the returns for overall calculations
    metrics.returns = returns
    
    # Attach drawdowns if available
    if max_drawdown is not None:
        metrics.drawdowns = max_drawdown
    
    return metrics

def _calculate_overall_metrics(
    trades: List[Trade],
    returns: List[float],
    drawdowns: List[float],
    initial_capital: float,
    metrics_to_calculate: List[str]
) -> Metrics:
    """
    Calculate overall performance metrics
    
    Returns:
        Overall metrics object
    """
    metrics = Metrics()
    
    # Always calculate basic metrics
    if trades:
        metrics.num_trades = len(trades)
        
        winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl and t.pnl < 0]
        
        metrics.win_rate = len(winning_trades) / len(trades) if trades else 0
        
        total_pnl = sum(t.pnl if t.pnl else 0 for t in trades)
        metrics.total_return = total_pnl / initial_capital
        
        metrics.avg_trade = total_pnl / len(trades) if trades else 0
        
        if losing_trades:
            metrics.profit_factor = sum(t.pnl for t in winning_trades) / abs(sum(t.pnl for t in losing_trades)) if sum(t.pnl for t in losing_trades) != 0 else 0
    
    # Calculate requested metrics
    if "sharpe_ratio" in metrics_to_calculate and returns:
        metrics.sharpe_ratio = _calculate_sharpe_ratio(returns)
    
    if "max_drawdown" in metrics_to_calculate and drawdowns:
        metrics.max_drawdown = max(drawdowns) if drawdowns else 0
    
    if "volatility" in metrics_to_calculate and returns:
        metrics.volatility = np.std(returns)
    
    if "max_consecutive_wins" in metrics_to_calculate or "max_consecutive_losses" in metrics_to_calculate:
        # Calculate win/loss streaks
        if trades:
            # Create list of wins (1) and losses (0)
            outcomes = [1 if t.pnl and t.pnl > 0 else 0 for t in trades]
            
            # Find max consecutive wins
            max_wins = _max_consecutive(outcomes, 1)
            metrics.max_consecutive_wins = max_wins
            
            # Find max consecutive losses
            max_losses = _max_consecutive(outcomes, 0)
            metrics.max_consecutive_losses = max_losses
    
    if "cagr" in metrics_to_calculate and trades:
        # Calculate CAGR (Compound Annual Growth Rate)
        if len(trades) > 1:
            # Get first and last trade dates
            first_date = pd.to_datetime(trades[0].entry_date)
            last_date = pd.to_datetime(trades[-1].exit_date) if trades[-1].exit_date else pd.to_datetime(trades[-1].entry_date)
            
            # Calculate years
            years = (last_date - first_date).days / 365.25
            
            if years > 0:
                # Calculate CAGR
                final_capital = initial_capital * (1 + metrics.total_return)
                metrics.cagr = (final_capital / initial_capital) ** (1 / years) - 1
    
    if "calmar_ratio" in metrics_to_calculate and hasattr(metrics, 'cagr') and hasattr(metrics, 'max_drawdown'):
        # Calculate Calmar ratio (CAGR / Max Drawdown)
        if metrics.max_drawdown and metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.cagr / metrics.max_drawdown
    
    if "sortino_ratio" in metrics_to_calculate and returns:
        # Calculate Sortino ratio (Return / Downside deviation)
        metrics.sortino_ratio = _calculate_sortino_ratio(returns)
    
    return metrics

def _calculate_sharpe_ratio(returns, risk_free_rate=0, periods_per_year=252):
    """
    Calculate Sharpe ratio
    
    Args:
        returns: List of returns
        risk_free_rate: Risk-free rate (default: 0)
        periods_per_year: Number of periods per year (default: 252 for trading days)
    
    Returns:
        Sharpe ratio as float
    """
    # Use CuPy if available for faster computation
    if CUPY_AVAILABLE:
        import cupy as cp
        try:
            # Transfer data to GPU
            cp_returns = cp.array(returns)
            
            # Calculate metrics
            excess_returns = cp_returns - risk_free_rate / periods_per_year
            annual_excess_return = cp.mean(excess_returns) * periods_per_year
            annual_volatility = cp.std(excess_returns, ddof=1) * cp.sqrt(cp.array(periods_per_year))
            
            # Calculate Sharpe ratio
            sharpe = annual_excess_return / annual_volatility if annual_volatility != 0 else 0
            
            # Transfer result back to CPU
            return float(sharpe)
        except Exception as e:
            logger.warning(f"Error calculating Sharpe ratio with CuPy: {str(e)}. Falling back to NumPy.")
    
    # NumPy fallback
    excess_returns = np.array(returns) - risk_free_rate / periods_per_year
    annual_excess_return = np.mean(excess_returns) * periods_per_year
    annual_volatility = np.std(excess_returns, ddof=1) * np.sqrt(periods_per_year)
    
    return annual_excess_return / annual_volatility if annual_volatility != 0 else 0

def _calculate_sortino_ratio(returns, risk_free_rate=0, periods_per_year=252):
    """
    Calculate Sortino ratio
    
    Args:
        returns: List of returns
        risk_free_rate: Risk-free rate (default: 0)
        periods_per_year: Number of periods per year (default: 252 for trading days)
    
    Returns:
        Sortino ratio as float
    """
    # Use CuPy if available for faster computation
    if CUPY_AVAILABLE:
        import cupy as cp
        try:
            # Transfer data to GPU
            cp_returns = cp.array(returns)
            
            # Calculate metrics
            excess_returns = cp_returns - risk_free_rate / periods_per_year
            annual_excess_return = cp.mean(excess_returns) * periods_per_year
            
            # Calculate downside deviation (standard deviation of negative returns only)
            downside_returns = cp.minimum(excess_returns, 0)
            downside_deviation = cp.sqrt(cp.mean(cp.square(downside_returns))) * cp.sqrt(cp.array(periods_per_year))
            
            # Calculate Sortino ratio
            sortino = annual_excess_return / downside_deviation if downside_deviation != 0 else 0
            
            # Transfer result back to CPU
            return float(sortino)
        except Exception as e:
            logger.warning(f"Error calculating Sortino ratio with CuPy: {str(e)}. Falling back to NumPy.")
    
    # NumPy fallback
    excess_returns = np.array(returns) - risk_free_rate / periods_per_year
    annual_excess_return = np.mean(excess_returns) * periods_per_year
    
    # Calculate downside deviation
    downside_returns = np.minimum(excess_returns, 0)
    downside_deviation = np.sqrt(np.mean(np.square(downside_returns))) * np.sqrt(periods_per_year)
    
    return annual_excess_return / downside_deviation if downside_deviation != 0 else 0

def _calculate_max_drawdown(equity_curve):
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve: Array of equity values
    
    Returns:
        Maximum drawdown as float
    """
    # Use CuPy if available for faster computation
    if CUPY_AVAILABLE:
        import cupy as cp
        try:
            # Transfer data to GPU
            cp_equity = cp.array(equity_curve)
            
            # Calculate running maximum
            running_max = cp.maximum.accumulate(cp_equity)
            
            # Calculate drawdowns
            drawdowns = (running_max - cp_equity) / running_max
            
            # Find maximum drawdown
            max_drawdown = cp.max(drawdowns)
            
            # Transfer result back to CPU
            return float(max_drawdown)
        except Exception as e:
            logger.warning(f"Error calculating max drawdown with CuPy: {str(e)}. Falling back to NumPy.")
    
    # NumPy fallback
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = (running_max - equity_curve) / running_max
    max_drawdown = np.max(drawdowns)
    
    return max_drawdown

def _calculate_equity_curve(positions, prices, initial_capital):
    """
    Calculate equity curve from positions and prices
    
    Args:
        positions: Array of position values (-1, 0, 1)
        prices: Array of price values
        initial_capital: Initial capital
    
    Returns:
        Array of equity values
    """
    # Initialize equity curve with initial capital
    equity = np.zeros(len(positions))
    equity[0] = initial_capital
    
    # Calculate equity for each period
    for i in range(1, len(positions)):
        # Calculate P&L for period
        if positions[i-1] != 0:
            pnl = positions[i-1] * (prices[i] - prices[i-1]) * initial_capital * 0.1
        else:
            pnl = 0
        
        # Update equity
        equity[i] = equity[i-1] + pnl
    
    return equity

def _max_consecutive(arr, val):
    """
    Calculate maximum consecutive occurrences of val in arr
    
    Args:
        arr: Array of values
        val: Value to count consecutive occurrences of
    
    Returns:
        Maximum consecutive occurrences as int
    """
    max_count = 0
    current_count = 0
    
    for v in arr:
        if v == val:
            current_count += 1
            max_count = max(max_count, current_count)
        else:
            current_count = 0
    
    return max_count