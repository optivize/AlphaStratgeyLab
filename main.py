import os
import uuid
from flask import Flask, render_template, send_from_directory, jsonify, request
import logging
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

# API Endpoints
@app.route('/api/v1/strategies')
def list_strategies():
    """List available strategy templates"""
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
    """Get details for a specific strategy template"""
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

@app.route('/api/v1/backtest', methods=['POST'])
def create_backtest():
    """Submit a new backtesting job"""
    try:
        logger.debug("Received backtest request")
        data = request.json
        
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Validate the request data
        logger.debug(f"Request data: {data}")
        
        # Generate a unique ID for the backtest
        backtest_id = str(uuid.uuid4())
        
        # Here we would normally send the job to the GPU processing engine
        # and store the job in a database for tracking
        
        # For now, just acknowledge receipt and return the job ID
        # The client will poll for results later
        
        return jsonify({
            "backtest_id": backtest_id,
            "status": "pending",
            "message": "Backtest job submitted successfully. Results will be available soon."
        })
        
    except Exception as e:
        logger.exception(f"Error processing backtest request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/backtest/<backtest_id>', methods=['GET'])
def get_backtest_results(backtest_id):
    """Retrieve results for a specific backtest"""
    try:
        # For development purposes to enable frontend testing,
        # we'll return a mock "completed" response with empty data
        
        # In a real implementation, we would check the status of the job
        # from the database/queue and return appropriate status messages
        
        logger.debug(f"Querying backtest results for ID: {backtest_id}")
        
        # Simulate a completed job with empty results structure
        mock_results = {
            "backtest_id": backtest_id,
            "status": "completed",
            "execution_time": 0.5,  # simulated time in seconds
            "results": {
                "overall_metrics": {
                    "sharpe_ratio": None,
                    "max_drawdown": None,
                    "total_return": None
                },
                "per_symbol_metrics": {},
                "equity_curve": [],
                "trades": []
            }
        }
        
        return jsonify(mock_results)
        
    except Exception as e:
        logger.exception(f"Error retrieving backtest results: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/data/upload', methods=['POST'])
def upload_market_data():
    """Upload custom market data"""
    # Placeholder for file upload endpoint
    return jsonify({
        "error": "This endpoint is not yet implemented"
    }), 501

@app.route('/api/v1/metrics', methods=['GET'])
def get_available_metrics():
    """Get available performance metrics for backtest evaluation"""
    metrics = [
        {
            "id": "sharpe_ratio",
            "name": "Sharpe Ratio",
            "description": "Risk-adjusted return metric (returns / volatility)"
        },
        {
            "id": "max_drawdown",
            "name": "Maximum Drawdown",
            "description": "Largest percentage drop from peak to trough"
        },
        {
            "id": "total_return",
            "name": "Total Return",
            "description": "Overall percentage return for the backtest period"
        },
        {
            "id": "volatility",
            "name": "Volatility",
            "description": "Standard deviation of returns"
        },
        {
            "id": "win_rate",
            "name": "Win Rate",
            "description": "Percentage of winning trades"
        },
        {
            "id": "profit_factor",
            "name": "Profit Factor",
            "description": "Gross profits divided by gross losses"
        },
        {
            "id": "cagr",
            "name": "CAGR",
            "description": "Compound Annual Growth Rate"
        },
        {
            "id": "calmar_ratio",
            "name": "Calmar Ratio",
            "description": "Annual return divided by maximum drawdown"
        },
        {
            "id": "sortino_ratio",
            "name": "Sortino Ratio",
            "description": "Return divided by downside deviation"
        }
    ]
    
    return jsonify(metrics)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
