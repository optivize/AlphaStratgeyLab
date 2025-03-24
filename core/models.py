from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from enum import Enum

class TimeFrame(str, Enum):
    DAY = "1d"
    HOUR = "1h"
    MINUTE = "1m"
    SECOND = "1s"
    TICK = "tick"

class PositionSizing(str, Enum):
    EQUAL = "equal"
    PERCENT = "percent"
    FIXED = "fixed"
    VOLATILITY = "volatility"

class StrategyDefinition(BaseModel):
    name: str
    parameters: Dict[str, Any]
    custom_code: Optional[str] = None

class DataRequest(BaseModel):
    symbols: List[str]
    start_date: date
    end_date: date
    timeframe: TimeFrame = TimeFrame.DAY
    data_source: str = "default"

class ExecutionParams(BaseModel):
    initial_capital: float = 100000.0
    position_size: PositionSizing = PositionSizing.EQUAL
    commission: float = 0.001
    slippage: float = 0.0005

class OutputRequest(BaseModel):
    metrics: List[str] = ["sharpe_ratio", "max_drawdown", "total_return"]
    include_trades: bool = True
    include_equity_curve: bool = True

class BacktestRequest(BaseModel):
    strategy: StrategyDefinition
    data: DataRequest
    execution: ExecutionParams = ExecutionParams()
    output: OutputRequest = OutputRequest()

class TradeRecord(BaseModel):
    symbol: str
    entry_date: str
    exit_date: Optional[str] = None
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float
    pnl: Optional[float] = None

class SymbolMetrics(BaseModel):
    total_return: float
    win_rate: float
    avg_gain: Optional[float] = None
    avg_loss: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None

class BacktestMetrics(BaseModel):
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
    overall_metrics: BacktestMetrics
    per_symbol_metrics: Dict[str, SymbolMetrics] = {}
    equity_curve: Optional[List[float]] = None
    trades: Optional[List[TradeRecord]] = None

class BacktestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class BacktestResponse(BaseModel):
    backtest_id: str
    status: str
    execution_time: float
    results: Optional[BacktestResult] = None
    error: Optional[str] = None

class StrategyParameterInfo(BaseModel):
    type: str
    default: Any
    description: str

class StrategyTemplate(BaseModel):
    id: str
    name: str
    description: str
    parameters: Dict[str, StrategyParameterInfo]

class DataSource(BaseModel):
    name: str
    description: str
    symbols_count: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timeframes: List[str]

class DataUploadResponse(BaseModel):
    source_name: str
    symbols: List[str]
    rows: int
    message: str
