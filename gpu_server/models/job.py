"""
Job-related models for the GPU server
"""
import uuid
import enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class StrategyParameter(BaseModel):
    """Strategy parameter definition"""
    type: str
    default: Any
    description: str

class Strategy(BaseModel):
    """Strategy definition"""
    id: str
    name: str
    description: str
    parameters: Dict[str, StrategyParameter]

class StrategyConfig(BaseModel):
    """Strategy configuration"""
    name: str
    parameters: Dict[str, Any]
    custom_code: Optional[str] = None

class DataConfig(BaseModel):
    """Data configuration for backtest"""
    symbols: List[str]
    start_date: str
    end_date: str
    timeframe: str
    data_source: str = "default"

class ExecutionConfig(BaseModel):
    """Execution configuration for backtest"""
    initial_capital: float = 100000.0
    position_size: str = "10%"  # Can be percentage or fixed amount
    commission: float = 0.0
    slippage: float = 0.0

class OutputConfig(BaseModel):
    """Output configuration for backtest"""
    metrics: List[str]
    include_trades: bool = True
    include_equity_curve: bool = True

class BacktestRequest(BaseModel):
    """Backtest job request"""
    strategy: StrategyConfig
    data: DataConfig
    execution: ExecutionConfig
    output: OutputConfig
    user_id: Optional[int] = None
    priority: int = 0

class Trade(BaseModel):
    """Trade record"""
    symbol: str
    entry_date: str
    exit_date: Optional[str] = None
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float
    pnl: Optional[float] = None

class SymbolMetrics(BaseModel):
    """Symbol-specific metrics"""
    total_return: float
    win_rate: float
    avg_gain: Optional[float] = None
    avg_loss: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None

class Metrics(BaseModel):
    """Overall backtest metrics"""
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_return: Optional[float] = None
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    avg_trade: Optional[float] = None
    num_trades: Optional[int] = None
    max_consecutive_wins: Optional[int] = None
    max_consecutive_losses: Optional[int] = None
    cagr: Optional[float] = None
    calmar_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None

class BacktestResult(BaseModel):
    """Backtest job result"""
    overall_metrics: Metrics
    per_symbol_metrics: Dict[str, SymbolMetrics]
    equity_curve: Optional[List[float]] = None
    trades: Optional[List[Trade]] = None

class JobStatus(enum.Enum):
    """Job status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    results: Optional[BacktestResult] = None
    error: Optional[str] = None

class DataSource(BaseModel):
    """Data source information"""
    id: str
    name: str
    description: Optional[str] = None
    symbols_count: int
    created_at: datetime