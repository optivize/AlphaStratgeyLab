import os
import uuid
from flask import Flask, render_template, send_from_directory, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import logging
from core.database import init_db, User, WatchlistItem, BacktestRecord, SessionLocal
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///backtest.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")

# Initialize database
with app.app_context():
    init_db()

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    with SessionLocal() as session:
        return session.query(User).get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's backtests
    with SessionLocal() as session:
        backtests = session.query(BacktestRecord).filter_by(user_id=current_user.id).order_by(BacktestRecord.created_at.desc()).all()
        watchlist = session.query(WatchlistItem).filter_by(user_id=current_user.id).all()
    
    return render_template('dashboard.html', backtests=backtests, watchlist=watchlist)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with SessionLocal() as session:
            user = session.query(User).filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        with SessionLocal() as session:
            # Check if username already exists
            if session.query(User).filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return render_template('register.html')
                
            # Check if email already exists
            if session.query(User).filter_by(email=email).first():
                flash('Email already exists', 'danger')
                return render_template('register.html')
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            
            session.add(user)
            session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

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
@login_required
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
        
        # Store the job in the database
        with SessionLocal() as session:
            # Create new backtest record
            backtest_record = BacktestRecord(
                id=backtest_id,
                user_id=current_user.id,
                request=data,
                status="pending"
            )
            session.add(backtest_record)
            session.commit()
        
        # In a real implementation, we would now send the job to the 
        # GPU processing engine via API call or message queue
        
        return jsonify({
            "backtest_id": backtest_id,
            "status": "pending",
            "message": "Backtest job submitted successfully. Results will be available soon."
        })
        
    except Exception as e:
        logger.exception(f"Error processing backtest request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/backtest/<backtest_id>', methods=['GET'])
@login_required
def get_backtest_results(backtest_id):
    """Retrieve results for a specific backtest"""
    try:
        logger.debug(f"Querying backtest results for ID: {backtest_id}")
        
        with SessionLocal() as session:
            # Query for the backtest record
            backtest_record = session.query(BacktestRecord).get(backtest_id)
            
            if not backtest_record:
                return jsonify({"error": "Backtest not found"}), 404
            
            # Check if the backtest belongs to the current user
            if backtest_record.user_id and backtest_record.user_id != current_user.id:
                return jsonify({"error": "Unauthorized access to backtest"}), 403
            
            # Return the current status of the backtest
            response = {
                "backtest_id": backtest_record.id,
                "status": backtest_record.status,
                "execution_time": backtest_record.execution_time or 0,
            }
            
            # Include results if available
            if backtest_record.results:
                response["results"] = backtest_record.results
            
            # Include error message if job failed
            if backtest_record.status == "failed" and backtest_record.error:
                response["error"] = backtest_record.error
            
            # For demonstration purposes, transition pending jobs to completed
            # In a real implementation, this would be done by the processing engine
            if backtest_record.status == "pending":
                # Update the status to simulate a completed job
                backtest_record.status = "completed"
                backtest_record.execution_time = 0.5
                
                # Create empty result structure with sample data
                backtest_record.results = {
                    "overall_metrics": {
                        "sharpe_ratio": 1.25,
                        "max_drawdown": -0.15,
                        "total_return": 0.22,
                        "win_rate": 0.63,
                        "profit_factor": 1.75
                    },
                    "per_symbol_metrics": {
                        symbol: {
                            "total_return": 0.22,
                            "win_rate": 0.63,
                            "avg_gain": 0.05,
                            "avg_loss": -0.03,
                            "max_drawdown": -0.15
                        } for symbol in backtest_record.request.get('data', {}).get('symbols', [])
                    },
                    "equity_curve": [100000] + [100000 * (1 + 0.22 * i / 100) for i in range(1, 101)],
                    "trades": [
                        {
                            "symbol": symbol,
                            "entry_date": "2024-01-05T10:30:00",
                            "exit_date": "2024-01-10T15:45:00",
                            "entry_price": 150.25,
                            "exit_price": 158.75,
                            "position_size": 100,
                            "pnl": 850.0
                        } for symbol in backtest_record.request.get('data', {}).get('symbols', [])
                    ]
                }
                
                session.commit()
                
                # Update the response
                response["status"] = "completed"
                response["execution_time"] = backtest_record.execution_time
                response["results"] = backtest_record.results
            
            return jsonify(response)
        
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

@app.route('/api/v1/watchlist', methods=['GET'])
@login_required
def get_watchlist():
    """Get user's stock watchlist"""
    try:
        with SessionLocal() as session:
            watchlist_items = session.query(WatchlistItem).filter_by(user_id=current_user.id).all()
            
            result = [{
                "symbol": item.symbol,
                "added_at": item.added_at.isoformat()
            } for item in watchlist_items]
            
            return jsonify(result)
    except Exception as e:
        logger.exception(f"Error retrieving watchlist: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/watchlist/add', methods=['POST'])
@login_required
def add_to_watchlist():
    """Add a stock to the user's watchlist"""
    try:
        data = request.json
        
        if not data or 'symbol' not in data:
            return jsonify({"error": "Symbol is required"}), 400
        
        symbol = data['symbol'].upper()
        
        with SessionLocal() as session:
            # Check if symbol already exists in watchlist
            existing = session.query(WatchlistItem).filter_by(user_id=current_user.id, symbol=symbol).first()
            
            if existing:
                return jsonify({"error": "Symbol already in watchlist"}), 400
            
            # Add new watchlist item
            watchlist_item = WatchlistItem(user_id=current_user.id, symbol=symbol)
            session.add(watchlist_item)
            session.commit()
            
            return jsonify({
                "symbol": symbol,
                "added_at": watchlist_item.added_at.isoformat(),
                "message": f"Added {symbol} to watchlist"
            })
    except Exception as e:
        logger.exception(f"Error adding to watchlist: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/backtest', methods=['POST'])
@login_required
def ai_backtest():
    """Process an AI-generated backtest request"""
    try:
        data = request.json
        
        if not data or 'query' not in data:
            return jsonify({"error": "Query is required"}), 400
        
        query = data['query']
        logger.debug(f"Received AI backtest query: {query}")
        
        # Get Together AI API key from environment
        together_key = os.environ.get("TOGETHER_KEY")
        logger.debug(f"Together AI API key available: {bool(together_key)}")
        
        # Process with Together AI API if key is available
        if together_key and len(query.strip()) > 10:  # Only process substantial queries
            try:
                import requests
                import json
                
                # API endpoint for Together AI
                api_url = "https://api.together.xyz/v1/completions"
                
                # Prepare prompt for the AI
                prompt = f"""
                You are an expert trading strategy assistant. Extract information from the following query to 
                create a structured trading strategy backtest configuration.
                
                User query: {query}
                
                Output a JSON object with the following structure:
                {{
                    "strategy": {{
                        "id": "MovingAverageCrossover|BollingerBands|MomentumStrategy|MeanReversion",
                        "name": "Strategy name",
                        "parameters": {{
                            // Strategy-specific parameters
                        }}
                    }},
                    "data": {{
                        "symbols": ["AAPL"], // Stock symbols
                        "start_date": "2023-01-01", // In YYYY-MM-DD format
                        "end_date": "2023-12-31", // In YYYY-MM-DD format
                        "timeframe": "1d"
                    }},
                    "execution": {{
                        "initial_capital": 100000,
                        "position_size": "equal",
                        "commission": 0.001,
                        "slippage": 0.0005
                    }}
                }}
                """
                
                # Prepare the request payload
                payload = {
                    "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "prompt": prompt,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repetition_penalty": 1.1
                }
                
                # Set headers with API key
                headers = {
                    "Authorization": f"Bearer {together_key}",
                    "Content-Type": "application/json"
                }
                
                # Make the API request
                logger.debug("Making request to Together AI API")
                ai_response = requests.post(api_url, json=payload, headers=headers)
                
                # Process the response
                if ai_response.status_code == 200:
                    try:
                        result = ai_response.json()
                        content = result.get('output', {}).get('choices', [{}])[0].get('text', '').strip()
                        
                        # Extract JSON from the response
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        
                        if json_start >= 0 and json_end > json_start:
                            json_str = content[json_start:json_end]
                            ai_config = json.loads(json_str)
                            
                            # Validate and use AI-generated config
                            if (ai_config and 'strategy' in ai_config and 
                                'data' in ai_config and 'execution' in ai_config):
                                return jsonify(ai_config)
                        
                        logger.debug(f"AI response processed, but couldn't extract valid JSON")
                    except Exception as e:
                        logger.exception(f"Error processing AI response: {str(e)}")
                else:
                    logger.error(f"Error from Together AI API: {ai_response.status_code} - {ai_response.text}")
            except Exception as e:
                logger.exception(f"Error calling Together AI API: {str(e)}")
                
        # Fallback to keyword-based approach if AI processing fails
        
        response = {
            "strategy": {
                "id": "MovingAverageCrossover",
                "name": "Moving Average Crossover",
                "parameters": {
                    "short_window": 20,
                    "long_window": 50,
                    "signal_threshold": 0.01
                }
            },
            "data": {
                "symbols": ["AAPL"],
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "timeframe": "1d"
            },
            "execution": {
                "initial_capital": 100000,
                "position_size": "equal",
                "commission": 0.001,
                "slippage": 0.0005
            }
        }
        
        # Process any specific keywords in the query
        if "tesla" in query.lower() or "tsla" in query.lower():
            response["data"]["symbols"] = ["TSLA"]
        elif "google" in query.lower() or "goog" in query.lower():
            response["data"]["symbols"] = ["GOOGL"]
        elif "amazon" in query.lower() or "amzn" in query.lower():
            response["data"]["symbols"] = ["AMZN"]
        elif "aapl" in query.lower() or "apple" in query.lower():
            response["data"]["symbols"] = ["AAPL"]
        elif "tech stocks" in query.lower():
            response["data"]["symbols"] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
        
        if "bollinger" in query.lower():
            response["strategy"]["id"] = "BollingerBands"
            response["strategy"]["name"] = "Bollinger Bands"
            response["strategy"]["parameters"] = {
                "window": 20,
                "num_std": 2.0
            }
        elif "momentum" in query.lower():
            response["strategy"]["id"] = "MomentumStrategy"
            response["strategy"]["name"] = "Momentum"
            response["strategy"]["parameters"] = {
                "momentum_window": 14,
                "threshold": 0.05
            }
        elif "mean reversion" in query.lower():
            response["strategy"]["id"] = "MeanReversion"
            response["strategy"]["name"] = "Mean Reversion"
            response["strategy"]["parameters"] = {
                "window": 30,
                "z_threshold": 1.5
            }
            
        # Process capital amount
        if "$50k" in query.lower() or "50k" in query.lower() or "50,000" in query.lower():
            response["execution"]["initial_capital"] = 50000
        
        return jsonify(response)
    
    except Exception as e:
        logger.exception(f"Error processing AI backtest request: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/watchlist/remove', methods=['POST'])
@login_required
def remove_from_watchlist():
    """Remove a stock from the user's watchlist"""
    try:
        data = request.json
        
        if not data or 'symbol' not in data:
            return jsonify({"error": "Symbol is required"}), 400
        
        symbol = data['symbol'].upper()
        
        with SessionLocal() as session:
            # Find and remove the watchlist item
            watchlist_item = session.query(WatchlistItem).filter_by(user_id=current_user.id, symbol=symbol).first()
            
            if not watchlist_item:
                return jsonify({"error": "Symbol not found in watchlist"}), 404
            
            session.delete(watchlist_item)
            session.commit()
            
            return jsonify({
                "symbol": symbol,
                "message": f"Removed {symbol} from watchlist"
            })
    except Exception as e:
        logger.exception(f"Error removing from watchlist: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
