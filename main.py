import os
from flask import Flask, render_template, send_from_directory, jsonify
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
