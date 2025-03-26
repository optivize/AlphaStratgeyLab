import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import './App.css';

// Page components
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import Backtest from './pages/Backtest';
import BacktestResults from './pages/BacktestResults';
import Watchlist from './pages/Watchlist';
import AIBacktest from './pages/AIBacktest';

// Context providers
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <div className="App" data-bs-theme="dark">
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/backtest/new" element={<Backtest />} />
          <Route path="/backtest/:id" element={<BacktestResults />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/ai-backtest" element={<AIBacktest />} />
        </Routes>
      </AuthProvider>
    </div>
  );
}

export default App;