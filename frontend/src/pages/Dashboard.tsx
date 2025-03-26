import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { BacktestResponse } from '../types';
import Navbar from '../components/Navbar';

const Dashboard: React.FC = () => {
  const [recentBacktests, setRecentBacktests] = useState<BacktestResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecentBacktests = async () => {
      try {
        // In a real implementation, this would fetch from the API
        // For now, we'll use a mock until the endpoint is created
        const response = await api.getBacktestResults('recent');
        setRecentBacktests(response.data.data || []);
      } catch (err) {
        setError('Failed to load recent backtests');
        console.error('Error fetching recent backtests:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentBacktests();
  }, []);

  return (
    <>
      <Navbar />
      <div className="container mt-4">
        <div className="row">
          <div className="col-12">
            <h1 className="mb-4">Dashboard</h1>
          </div>
        </div>

        <div className="row mb-4">
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h5 className="card-title">Quick Actions</h5>
                <div className="d-grid gap-2">
                  <Link to="/backtest/new" className="btn btn-primary">New Backtest</Link>
                  <Link to="/ai-backtest" className="btn btn-secondary">AI Backtest Assistant</Link>
                  <Link to="/watchlist" className="btn btn-secondary">Manage Watchlist</Link>
                </div>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="card h-100">
              <div className="card-body">
                <h5 className="card-title">Statistics</h5>
                <p className="card-text">Total Backtests: {recentBacktests.length}</p>
                {/* More statistics would go here */}
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h5 className="mb-0">Recent Backtests</h5>
              </div>
              <div className="card-body">
                {loading ? (
                  <div className="text-center my-4">
                    <div className="spinner-border text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                ) : error ? (
                  <div className="alert alert-danger" role="alert">
                    {error}
                  </div>
                ) : recentBacktests.length === 0 ? (
                  <div className="text-center my-4">
                    <p>No backtests found. Run your first backtest to see results here.</p>
                    <Link to="/backtest/new" className="btn btn-primary">Create New Backtest</Link>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Strategy</th>
                          <th>Symbols</th>
                          <th>Status</th>
                          <th>Execution Time</th>
                          <th>Results</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* Will be populated with real data from API */}
                        <tr>
                          <td>Moving Average Crossover</td>
                          <td>AAPL, MSFT, GOOGL</td>
                          <td>
                            <span className="badge bg-success">Completed</span>
                          </td>
                          <td>3.47s</td>
                          <td>
                            <Link to={`/backtest/1`} className="btn btn-sm btn-outline-primary">View</Link>
                          </td>
                        </tr>
                        <tr>
                          <td>Bollinger Bands</td>
                          <td>TSLA</td>
                          <td>
                            <span className="badge bg-success">Completed</span>
                          </td>
                          <td>2.31s</td>
                          <td>
                            <Link to={`/backtest/2`} className="btn btn-sm btn-outline-primary">View</Link>
                          </td>
                        </tr>
                        <tr>
                          <td>AI Generated Strategy</td>
                          <td>SPY, QQQ</td>
                          <td>
                            <span className="badge bg-success">Completed</span>
                          </td>
                          <td>5.82s</td>
                          <td>
                            <Link to={`/backtest/3`} className="btn btn-sm btn-outline-primary">View</Link>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default Dashboard;