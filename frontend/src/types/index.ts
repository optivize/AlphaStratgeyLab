// Strategy types
export interface StrategyParameter {
  type: string;
  default: any;
  description: string;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  parameters: Record<string, StrategyParameter>;
}

// Backtest types
export interface BacktestDefinition {
  strategy: {
    name: string;
    parameters: Record<string, any>;
    custom_code?: string;
  };
  data: {
    symbols: string[];
    start_date: string;
    end_date: string;
    timeframe: string;
    data_source: string;
  };
  execution: {
    initial_capital: number;
    position_size: string;
    commission: number;
    slippage: number;
  };
  output: {
    metrics: string[];
    include_trades: boolean;
    include_equity_curve: boolean;
  };
}

export interface Trade {
  symbol: string;
  entry_date: string;
  exit_date?: string;
  entry_price: number;
  exit_price?: number;
  position_size: number;
  pnl?: number;
}

export interface SymbolMetrics {
  total_return: number;
  win_rate: number;
  avg_gain?: number;
  avg_loss?: number;
  max_drawdown?: number;
  volatility?: number;
}

export interface BacktestMetrics {
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_return?: number;
  volatility?: number;
  win_rate?: number;
  profit_factor?: number;
  avg_trade?: number;
  num_trades?: number;
  max_consecutive_wins?: number;
  max_consecutive_losses?: number;
  cagr?: number;
  calmar_ratio?: number;
  sortino_ratio?: number;
}

export interface BacktestResult {
  overall_metrics: BacktestMetrics;
  per_symbol_metrics: Record<string, SymbolMetrics>;
  equity_curve?: number[];
  trades?: Trade[];
}

export interface BacktestResponse {
  backtest_id: string;
  status: string;
  execution_time: number;
  results?: BacktestResult;
  error?: string;
}

// Watchlist types
export interface WatchlistItem {
  symbol: string;
  added_at: string;
}

// API response types
export interface ApiResponse<T> {
  data: T;
  status: string;
  message?: string;
}