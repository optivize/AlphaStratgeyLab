import axios from 'axios';
import { 
  Strategy, 
  BacktestDefinition, 
  BacktestResponse, 
  WatchlistItem,
  ApiResponse
} from '../types';

// Axios defaults
axios.defaults.baseURL = '/api/v1';
axios.defaults.headers.common['Content-Type'] = 'application/json';
axios.defaults.withCredentials = true;

// API endpoints
export const api = {
  // Authentication
  login: (email: string, password: string) => 
    axios.post('/auth/login', { email, password }),
  
  register: (username: string, email: string, password: string) => 
    axios.post('/auth/register', { username, email, password }),
  
  logout: () => 
    axios.post('/auth/logout'),
  
  getCurrentUser: () => 
    axios.get('/auth/current_user'),
  
  // Strategies
  getStrategies: () => 
    axios.get<ApiResponse<Strategy[]>>('/strategies'),
  
  getStrategy: (id: string) => 
    axios.get<ApiResponse<Strategy>>(`/strategies/${id}`),
  
  // Backtests
  submitBacktest: (backtest: BacktestDefinition) => 
    axios.post<ApiResponse<BacktestResponse>>('/backtests', backtest),
  
  getBacktestResults: (id: string) => 
    axios.get<ApiResponse<BacktestResponse>>(`/backtests/${id}`),
  
  // AI Backtest
  generateAIBacktest: (prompt: string) => 
    axios.post<ApiResponse<BacktestResponse>>('/ai-backtest', { prompt }),
  
  // Watchlist
  getWatchlist: () => 
    axios.get<ApiResponse<WatchlistItem[]>>('/watchlist'),
  
  addToWatchlist: (symbol: string) => 
    axios.post<ApiResponse<WatchlistItem>>('/watchlist', { symbol }),
  
  removeFromWatchlist: (symbol: string) => 
    axios.delete<ApiResponse<void>>(`/watchlist/${symbol}`),
  
  // Market Data
  getAvailableSymbols: (source?: string) => 
    axios.get<ApiResponse<string[]>>('/data/symbols', { params: { source } }),
  
  getDataSources: () => 
    axios.get<ApiResponse<any[]>>('/data/sources'),
  
  uploadMarketData: (formData: FormData) => 
    axios.post<ApiResponse<any>>('/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }),
  
  // Metrics
  getAvailableMetrics: () => 
    axios.get<ApiResponse<any[]>>('/metrics')
};