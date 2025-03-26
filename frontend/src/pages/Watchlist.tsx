import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { WatchlistItem } from '../types';
import Navbar from '../components/Navbar';

const Watchlist: React.FC = () => {
  const [watchlistItems, setWatchlistItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newSymbol, setNewSymbol] = useState('');
  const [addingSymbol, setAddingSymbol] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    setLoading(true);
    try {
      const response = await api.getWatchlist();
      setWatchlistItems(response.data.data || []);
    } catch (err) {
      setError('Failed to load watchlist');
      console.error('Error fetching watchlist:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymbol = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSymbol) return;

    setAddingSymbol(true);
    setAddError(null);
    
    try {
      await api.addToWatchlist(newSymbol.toUpperCase());
      fetchWatchlist();
      setNewSymbol('');
    } catch (err: any) {
      setAddError(err.response?.data?.message || 'Failed to add symbol');
    } finally {
      setAddingSymbol(false);
    }
  };

  const handleRemoveSymbol = async (symbol: string) => {
    try {
      await api.removeFromWatchlist(symbol);
      fetchWatchlist();
    } catch (err) {
      setError('Failed to remove symbol');
      console.error('Error removing symbol:', err);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container mt-4">
        <div className="row">
          <div className="col-12">
            <h1 className="mb-4">Stock Watchlist</h1>
          </div>
        </div>

        <div className="row mb-4">
          <div className="col-md-6 mx-auto">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title">Add Symbol to Watchlist</h5>
                {addError && (
                  <div className="alert alert-danger" role="alert">
                    {addError}
                  </div>
                )}
                <form onSubmit={handleAddSymbol}>
                  <div className="input-group mb-3">
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Enter ticker symbol (e.g., AAPL)"
                      value={newSymbol}
                      onChange={(e) => setNewSymbol(e.target.value)}
                      required
                    />
                    <button 
                      className="btn btn-primary" 
                      type="submit"
                      disabled={addingSymbol}
                    >
                      {addingSymbol ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                          Adding...
                        </>
                      ) : 'Add'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Your Watchlist</h5>
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
                ) : watchlistItems.length === 0 ? (
                  <div className="text-center my-4">
                    <p>Your watchlist is empty. Add symbols to start tracking them.</p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Added Date</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {watchlistItems.map((item) => (
                          <tr key={item.symbol}>
                            <td>{item.symbol}</td>
                            <td>{new Date(item.added_at).toLocaleDateString()}</td>
                            <td>
                              <button
                                className="btn btn-sm btn-danger"
                                onClick={() => handleRemoveSymbol(item.symbol)}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
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

export default Watchlist;