import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import Navbar from '../components/Navbar';

const AIBacktest: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<Array<{text: string, active: boolean}>>([
    { text: "Momentum strategy for tech stocks", active: true },
    { text: "Mean reversion for SPY", active: true },
    { text: "Moving average crossover for AAPL", active: true },
    { text: "Bollinger Bands strategy for high volatility stocks", active: true },
    { text: "60/40 portfolio rebalancing strategy", active: true },
    { text: "Trend following for cryptocurrencies", active: true },
    { text: "Value investing with low P/E ratios", active: true },
    { text: "Market timing using VIX", active: true }
  ]);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();

  const handleSuggestionClick = (suggestionText: string) => {
    setPrompt(suggestionText);
    // Focus the textarea after setting the suggestion
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.generateAIBacktest(prompt);
      
      // If successful, navigate to the backtest results page
      if (response.data && response.data.data && response.data.data.backtest_id) {
        navigate(`/backtest/${response.data.data.backtest_id}`);
      } else {
        throw new Error('Invalid response from AI backtest service');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to generate AI backtest. Please try again.');
      console.error('Error generating AI backtest:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Navbar />
      <div className="container mt-4">
        <div className="row">
          <div className="col-12">
            <h1 className="mb-4">AI Backtest Assistant</h1>
            <p className="lead mb-4">
              Describe the trading strategy you want to test in natural language, and our AI assistant will generate and run a backtest for you.
            </p>
          </div>
        </div>

        <div className="row mb-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Try these suggestions</h5>
              </div>
              <div className="card-body">
                <div className="d-flex flex-wrap">
                  {suggestions.map((suggestion, index) => (
                    <span 
                      key={index} 
                      className="backtest-pill"
                      onClick={() => handleSuggestionClick(suggestion.text)}
                    >
                      {suggestion.text}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Describe Your Trading Strategy</h5>
              </div>
              <div className="card-body">
                {error && (
                  <div className="alert alert-danger" role="alert">
                    {error}
                  </div>
                )}
                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <textarea
                      ref={textareaRef}
                      className="form-control"
                      placeholder="E.g., I want to test a strategy that buys Apple stock when the 50-day moving average crosses above the 200-day moving average and sells when it crosses below"
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      rows={5}
                      required
                    ></textarea>
                  </div>
                  <button 
                    type="submit" 
                    className="btn btn-primary"
                    disabled={loading || !prompt.trim()}
                  >
                    {loading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Generating Backtest...
                      </>
                    ) : 'Generate Backtest'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>

        <div className="row mt-4">
          <div className="col-12">
            <div className="card">
              <div className="card-header">
                <h5 className="mb-0">Example Prompts</h5>
              </div>
              <div className="card-body">
                <h6>Simple Strategy</h6>
                <p>"I want to test a moving average crossover strategy on Apple stock, buying when the 20-day MA crosses above the 50-day MA and selling when it crosses below."</p>
                
                <h6>Multi-Asset Strategy</h6>
                <p>"Create a portfolio of tech stocks (AAPL, MSFT, GOOGL) and test a trend following strategy that allocates more capital to stocks with positive 3-month momentum."</p>
                
                <h6>Complex Strategy</h6>
                <p>"I want to test a mean reversion strategy for SPY that buys when RSI drops below 30 and the VIX is above its 50-day moving average, then sells when the RSI goes above 70."</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default AIBacktest;