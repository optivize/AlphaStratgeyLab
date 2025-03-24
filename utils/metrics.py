import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging
from core.models import BacktestMetrics, SymbolMetrics, TradeRecord

logger = logging.getLogger(__name__)

# Define available metrics
AVAILABLE_METRICS = {
    "total_return": {
        "name": "Total Return",
        "description": "Total percentage return of the strategy"
    },
    "sharpe_ratio": {
        "name": "Sharpe Ratio",
        "description": "Risk-adjusted return (using risk-free rate of 0)"
    },
    "max_drawdown": {
        "name": "Maximum Drawdown",
        "description": "Maximum peak-to-trough decline in portfolio value"
    },
    "volatility": {
        "name": "Volatility",
        "description": "Standard deviation of returns (annualized)"
    },
    "win_rate": {
        "name": "Win Rate",
        "description": "Percentage of trades that were profitable"
    },
    "profit_factor": {
        "name": "Profit Factor",
        "description": "Gross profit divided by gross loss"
    },
    "avg_trade": {
        "name": "Average Trade",
        "description": "Average profit/loss per trade"
    },
    "num_trades": {
        "name": "Number of Trades",
        "description": "Total number of trades executed"
    },
    "cagr": {
        "name": "CAGR",
        "description": "Compound Annual Growth Rate"
    },
    "calmar_ratio": {
        "name": "Calmar Ratio",
        "description": "CAGR divided by maximum drawdown"
    },
    "sortino_ratio": {
        "name": "Sortino Ratio",
        "description": "Risk-adjusted return using downside deviation"
    }
}

def calculate_metrics(
    trades: List[TradeRecord],
    positions: Dict[str, np.ndarray],
    price_data: Dict[str, pd.DataFrame],
    initial_capital: float,
    metrics_to_calculate: List[str]
) -> Tuple[BacktestMetrics, Dict[str, SymbolMetrics]]:
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
    logger.info(f"Calculating {len(metrics_to_calculate)} metrics")
    
    # Initialize metrics
    overall_metrics = BacktestMetrics()
    symbol_metrics = {}
    
    # Exit if no trades
    if not trades:
        return overall_metrics, symbol_metrics
    
    # Group trades by symbol
    trades_by_symbol = {}
    for trade in trades:
        if trade.symbol not in trades_by_symbol:
            trades_by_symbol[trade.symbol] = []
        trades_by_symbol[trade.symbol].append(trade)
    
    # Calculate symbol-specific metrics
    for symbol, symbol_trades in trades_by_symbol.items():
        # Calculate basic metrics
        total_pnl = sum(trade.pnl for trade in symbol_trades if trade.pnl is not None)
        winning_trades = [t for t in symbol_trades if t.pnl is not None and t.pnl > 0]
        losing_trades = [t for t in symbol_trades if t.pnl is not None and t.pnl < 0]
        
        win_rate = len(winning_trades) / len(symbol_trades) if symbol_trades else 0
        avg_gain = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        # Calculate symbol return
        symbol_return = total_pnl / initial_capital
        
        # Store metrics
        symbol_metrics[symbol] = SymbolMetrics(
            total_return=float(symbol_return),
            win_rate=float(win_rate),
            avg_gain=float(avg_gain),
            avg_loss=float(avg_loss)
        )
    
    # Calculate overall metrics
    all_pnls = [trade.pnl for trade in trades if trade.pnl is not None]
    total_pnl = sum(all_pnls)
    total_return = total_pnl / initial_capital
    
    winning_trades = [pnl for pnl in all_pnls if pnl > 0]
    losing_trades = [pnl for pnl in all_pnls if pnl < 0]
    
    win_rate = len(winning_trades) / len(all_pnls) if all_pnls else 0
    profit_factor = sum(winning_trades) / abs(sum(losing_trades)) if sum(losing_trades) != 0 else float('inf')
    avg_trade = total_pnl / len(all_pnls) if all_pnls else 0
    
    # Calculate advanced metrics if needed
    if "sharpe_ratio" in metrics_to_calculate:
        # Calculate daily returns (simplified)
        daily_returns = np.diff(np.array([initial_capital] + [initial_capital + sum(all_pnls[:i+1]) for i in range(len(all_pnls))])) / initial_capital
        sharpe = calculate_sharpe_ratio(daily_returns)
        overall_metrics.sharpe_ratio = float(sharpe)
    
    if "max_drawdown" in metrics_to_calculate:
        # Calculate equity curve
        equity_curve = np.array([initial_capital] + [initial_capital + sum(all_pnls[:i+1]) for i in range(len(all_pnls))])
        max_dd = calculate_max_drawdown(equity_curve)
        overall_metrics.max_drawdown = float(max_dd)
    
    # Set basic metrics
    overall_metrics.total_return = float(total_return)
    overall_metrics.win_rate = float(win_rate)
    overall_metrics.profit_factor = float(profit_factor)
    overall_metrics.avg_trade = float(avg_trade)
    overall_metrics.num_trades = len(all_pnls)
    
    return overall_metrics, symbol_metrics

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0, periods_per_year: int = 252) -> float:
    """
    Calculate the Sharpe ratio
    """
    if len(returns) < 2:
        return 0
    
    excess_returns = returns - risk_free_rate
    return (np.mean(excess_returns) / np.std(excess_returns, ddof=1)) * np.sqrt(periods_per_year)

def calculate_max_drawdown(equity_curve: np.ndarray) -> float:
    """
    Calculate the maximum drawdown
    """
    if len(equity_curve) < 2:
        return 0
    
    # Calculate running maximum
    running_max = np.maximum.accumulate(equity_curve)
    
    # Calculate drawdown in percentage terms
    drawdown = (running_max - equity_curve) / running_max
    
    return np.max(drawdown)
