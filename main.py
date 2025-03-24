import os
import uuid
import datetime
from flask import Flask, render_template, send_from_directory, jsonify, request
import logging
import numpy as np
from core.database import init_db

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///backtest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
with app.app_context():
    init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/templates/<path:path>')
def send_template(path):
    return send_from_directory('templates', path)

@app.route('/api/v1/strategies')
def list_strategies():
    # Temporary implementation for prototyping
    strategies = [
        {
            "id": "MovingAverageCrossover",
            "name": "Moving Average Crossover",
            "description": "Trading based on short and long-term moving average signals"
        },
        {
            "id": "BollingerBands",
            "name": "Bollinger Bands",
            "description": "Trading based on price movements relative to volatility bands"
        },
        {
            "id": "MomentumStrategy",
            "name": "Momentum",
            "description": "Trading based on price momentum indicators"
        },
        {
            "id": "MeanReversion",
            "name": "Mean Reversion",
            "description": "Trading based on price deviation from historical means"
        }
    ]
    return jsonify(strategies)

@app.route('/api/v1/strategies/<strategy_id>')
def get_strategy(strategy_id):
    # Temporary implementation for prototyping
    strategy_info = {
        "MovingAverageCrossover": {
            "id": "MovingAverageCrossover",
            "name": "Moving Average Crossover",
            "description": "Trading based on short and long-term moving average signals",
            "parameters": {
                "short_window": {
                    "type": "integer",
                    "default": 20,
                    "description": "Short moving average window"
                },
                "long_window": {
                    "type": "integer",
                    "default": 50,
                    "description": "Long moving average window"
                },
                "signal_threshold": {
                    "type": "float",
                    "default": 0.01,
                    "description": "Signal threshold to trigger trades"
                }
            }
        },
        "BollingerBands": {
            "id": "BollingerBands",
            "name": "Bollinger Bands",
            "description": "Trading based on price movements relative to volatility bands",
            "parameters": {
                "window": {
                    "type": "integer",
                    "default": 20,
                    "description": "Window size for calculating moving average"
                },
                "num_std": {
                    "type": "float",
                    "default": 2.0,
                    "description": "Number of standard deviations for bands"
                }
            }
        },
        "MomentumStrategy": {
            "id": "MomentumStrategy",
            "name": "Momentum",
            "description": "Trading based on price momentum indicators",
            "parameters": {
                "momentum_window": {
                    "type": "integer",
                    "default": 14,
                    "description": "Window size for momentum calculation"
                },
                "threshold": {
                    "type": "float",
                    "default": 0.05,
                    "description": "Threshold for momentum signals"
                }
            }
        },
        "MeanReversion": {
            "id": "MeanReversion",
            "name": "Mean Reversion",
            "description": "Trading based on price deviation from historical means",
            "parameters": {
                "window": {
                    "type": "integer",
                    "default": 30,
                    "description": "Window size for mean calculation"
                },
                "z_threshold": {
                    "type": "float",
                    "default": 1.5,
                    "description": "Z-score threshold for signals"
                }
            }
        }
    }
    
    if strategy_id in strategy_info:
        return jsonify(strategy_info[strategy_id])
    else:
        return jsonify({"error": "Strategy not found"}), 404

# Backtest endpoints
@app.route('/api/v1/backtest', methods=['POST'])
def create_backtest():
    """Submit a new backtesting job"""
    try:
        logger.debug("Received backtest request")
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
            
        # Generate a unique ID for the backtest
        backtest_id = str(uuid.uuid4())
        
        # In a real implementation, we would validate the input data
        # and submit the job to a background worker
        
        # For prototyping, we'll return demo results immediately
        
        # Simulated execution time (in seconds)
        execution_time = 2.5
        
        # Generate sample equity curve
        days = 365  # One year of daily data
        equity_curve = generate_demo_equity_curve(
            days, 
            initial_capital=data.get('execution', {}).get('initial_capital', 100000)
        )
        
        # Generate sample trades
        trades = generate_demo_trades(
            days, 
            symbols=data.get('data', {}).get('symbols', ['AAPL', 'MSFT']),
            start_date=data.get('data', {}).get('start_date', '2023-01-01')
        )
        
        # Generate sample metrics
        metrics = generate_demo_metrics()
        
        # Generate sample symbol metrics
        symbol_metrics = {}
        for symbol in data.get('data', {}).get('symbols', ['AAPL', 'MSFT']):
            symbol_metrics[symbol] = {
                "total_return": np.random.uniform(0.05, 0.3),
                "win_rate": np.random.uniform(0.4, 0.7),
                "avg_gain": np.random.uniform(0.01, 0.05),
                "avg_loss": np.random.uniform(-0.03, -0.01),
                "max_drawdown": np.random.uniform(-0.2, -0.05),
                "volatility": np.random.uniform(0.1, 0.3)
            }
            
        # Compile results
        results = {
            "overall_metrics": metrics,
            "per_symbol_metrics": symbol_metrics,
            "equity_curve": equity_curve,
            "trades": trades
        }
            
        return jsonify({
            "backtest_id": backtest_id,
            "status": "completed",  # For prototyping, we're marking it as completed immediately
            "execution_time": execution_time,
            "results": results
        })
        
    except Exception as e:
        logger.exception(f"Error processing backtest request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/backtest/<backtest_id>', methods=['GET'])
def get_backtest_results(backtest_id):
    """Retrieve results for a specific backtest"""
    # In a real implementation, we would query the database for results
    # For prototyping, we'll return a not found error
    return jsonify({
        "error": "Backtest not found"
    }), 404

# Helper functions for generating demo data
def generate_demo_equity_curve(days, initial_capital=100000):
    """Generate a sample equity curve"""
    # Start with initial capital
    equity = initial_capital
    curve = [equity]
    
    # Generate random daily returns with a slight upward bias
    daily_returns = np.random.normal(0.0005, 0.01, days)
    
    # Calculate cumulative equity
    for daily_return in daily_returns:
        equity = equity * (1 + daily_return)
        curve.append(equity)
        
    return curve

def generate_demo_trades(days, symbols, start_date):
    """Generate sample trades"""
    trades = []
    
    # Parse start date
    start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    
    # Generate 20-30 random trades
    num_trades = np.random.randint(20, 30)
    
    for i in range(num_trades):
        # Random symbol
        symbol = np.random.choice(symbols)
        
        # Random entry date
        entry_offset = np.random.randint(0, days - 10)
        entry_date = (start + datetime.timedelta(days=entry_offset)).strftime('%Y-%m-%d')
        
        # Random exit date after entry
        exit_offset = np.random.randint(1, 10)
        exit_date = (start + datetime.timedelta(days=entry_offset + exit_offset)).strftime('%Y-%m-%d')
        
        # Random prices
        entry_price = np.random.uniform(50, 200)
        
        # Slightly biased towards profitable trades
        if np.random.random() > 0.4:  # 60% profitable trades
            exit_price = entry_price * (1 + np.random.uniform(0.01, 0.1))
        else:
            exit_price = entry_price * (1 - np.random.uniform(0.01, 0.08))
            
        # Position size
        position_size = np.random.randint(10, 100)
        
        # Calculate P&L
        pnl = (exit_price - entry_price) * position_size
        
        trades.append({
            "symbol": symbol,
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "position_size": position_size,
            "pnl": pnl
        })
        
    return trades

def generate_demo_metrics():
    """Generate sample backtest metrics"""
    return {
        "sharpe_ratio": np.random.uniform(1.0, 3.0),
        "max_drawdown": np.random.uniform(-0.25, -0.05),
        "total_return": np.random.uniform(0.1, 0.5),
        "volatility": np.random.uniform(0.1, 0.3),
        "win_rate": np.random.uniform(0.5, 0.7),
        "profit_factor": np.random.uniform(1.2, 2.5),
        "avg_trade": np.random.uniform(50, 200),
        "num_trades": np.random.randint(20, 100),
        "max_consecutive_wins": np.random.randint(3, 10),
        "max_consecutive_losses": np.random.randint(2, 6),
        "cagr": np.random.uniform(0.08, 0.25),
        "calmar_ratio": np.random.uniform(0.5, 3.0),
        "sortino_ratio": np.random.uniform(1.2, 4.0)
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
