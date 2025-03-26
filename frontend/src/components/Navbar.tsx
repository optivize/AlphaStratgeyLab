import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import { useTheme } from '../context/ThemeContext';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Dynamically set navbar classes based on theme
  const navbarClasses = theme === 'dark' 
    ? 'navbar navbar-expand-lg navbar-dark bg-dark'
    : 'navbar navbar-expand-lg navbar-light bg-light';

  return (
    <nav className={navbarClasses}>
      <div className="container">
        <Link className="navbar-brand" to="/dashboard">
          <img 
            src="/static/images/logo.svg" 
            alt="StockTester" 
            height="30" 
            className="d-inline-block align-top me-2" 
          />
          StockTester
        </Link>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarMain"
          aria-controls="navbarMain"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarMain">
          <ul className="navbar-nav me-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <Link className="nav-link" to="/dashboard">Dashboard</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/backtest/new">New Backtest</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/ai-backtest">AI Assistant</Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/watchlist">Watchlist</Link>
            </li>
          </ul>
          
          <div className="d-flex align-items-center">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* User Info & Logout */}
            {user && (
              <div className="d-flex align-items-center ms-3">
                <span className="me-3">
                  Welcome, {user.username}
                </span>
                <button
                  className="btn btn-outline-danger"
                  onClick={handleLogout}
                >
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;