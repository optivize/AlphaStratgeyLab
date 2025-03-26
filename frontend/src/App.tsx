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

// Components
import PrivateRoute from './components/PrivateRoute';

// Context providers
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';

function App() {
  return (
    <div className="App">
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected routes */}
            <Route path="/dashboard" element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            } />
            <Route path="/backtest/new" element={
              <PrivateRoute>
                <Backtest />
              </PrivateRoute>
            } />
            <Route path="/backtest/:id" element={
              <PrivateRoute>
                <BacktestResults />
              </PrivateRoute>
            } />
            <Route path="/watchlist" element={
              <PrivateRoute>
                <Watchlist />
              </PrivateRoute>
            } />
            <Route path="/ai-backtest" element={
              <PrivateRoute>
                <AIBacktest />
              </PrivateRoute>
            } />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </div>
  );
}

export default App;