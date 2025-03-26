import axios from 'axios';
import { BacktestDefinition, WatchlistItem, ApiResponse, BacktestResponse } from '../types';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/sessions
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// API methods for the application
export const api = {
  // Authentication
  login: (email: string, password: string) => 
    apiClient.post('/auth/login', { email, password }),
  
  register: (username: string, email: string, password: string) => 
    apiClient.post('/auth/register', { username, email, password }),
  
  logout: () => 
    apiClient.post('/auth/logout'),
  
  checkAuth: () => 
    apiClient.get('/auth/me'),
  
  // Backtest operations
  submitBacktest: (backtest: BacktestDefinition) => 
    apiClient.post<ApiResponse<BacktestResponse>>('/backtest', backtest),
  
  getBacktestResults: (backtestId: string) => 
    apiClient.get<ApiResponse<BacktestResponse>>(`/backtest/${backtestId}`),
  
  // AI Backtest
  generateAIBacktest: (prompt: string) => 
    apiClient.post<ApiResponse<BacktestResponse>>('/ai/backtest', { prompt }),
  
  // Watchlist operations
  getWatchlist: () => 
    apiClient.get<ApiResponse<WatchlistItem[]>>('/watchlist'),
  
  addToWatchlist: (symbol: string) => 
    apiClient.post<ApiResponse<WatchlistItem>>('/watchlist', { symbol }),
  
  removeFromWatchlist: (symbol: string) => 
    apiClient.delete<ApiResponse<void>>(`/watchlist/${symbol}`),
  
  // Data operations
  uploadMarketData: (formData: FormData) => 
    apiClient.post<ApiResponse<any>>('/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }),
  
  // Strategy operations
  getStrategies: () => 
    apiClient.get<ApiResponse<any>>('/strategies'),
  
  getStrategyDetails: (strategyId: string) => 
    apiClient.get<ApiResponse<any>>(`/strategies/${strategyId}`),
  
  // Metrics operations
  getAvailableMetrics: () => 
    apiClient.get<ApiResponse<string[]>>('/metrics'),
};

export default api;