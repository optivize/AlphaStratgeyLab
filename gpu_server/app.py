"""
Main application file for the GPU Server
"""
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Import configuration
import config

# Import components
from data_service.data_processor import DataProcessor
from gpu_engine.engine import GPUBacktestEngine
from models.job import BacktestRequest, BacktestResult, JobStatus
from utils.auth import require_api_key

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up database connection
engine = create_engine(config.DATABASE_URL)
Base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# Initialize components
data_processor = DataProcessor()
gpu_engine = GPUBacktestEngine()

# Register middleware
if config.API_KEY_REQUIRED:
    logger.info("API Key authentication enabled")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    gpu_status = gpu_engine.get_status()
    return jsonify({
        "status": "healthy",
        "gpu": gpu_status,
        "version": "1.0.0"
    })

@app.route('/backtest', methods=['POST'])
@require_api_key
def submit_backtest():
    """Submit a new backtest job"""
    try:
        # Parse request
        payload = request.json
        backtest_request = BacktestRequest(**payload)
        
        # Create job ID and save to database
        job_id = gpu_engine.submit_job(backtest_request)
        
        return jsonify({
            "status": "success",
            "job_id": job_id,
            "message": "Backtest job submitted successfully"
        })
    except Exception as e:
        logger.error(f"Error submitting backtest: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/backtest/<job_id>', methods=['GET'])
@require_api_key
def get_backtest_status(job_id):
    """Get status of a backtest job"""
    try:
        status = gpu_engine.get_job_status(job_id)
        return jsonify({
            "status": "success",
            "job_id": job_id,
            "job_status": status.value,
            "results": status.results.dict() if status.results else None
        })
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/data/sources', methods=['GET'])
@require_api_key
def list_data_sources():
    """List available data sources"""
    try:
        sources = data_processor.list_data_sources()
        return jsonify({
            "status": "success",
            "sources": sources
        })
    except Exception as e:
        logger.error(f"Error listing data sources: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/data/symbols', methods=['GET'])
@require_api_key
def list_symbols():
    """List available symbols"""
    try:
        source = request.args.get('source', 'default')
        symbols = data_processor.list_symbols(source)
        return jsonify({
            "status": "success",
            "source": source,
            "symbols": symbols
        })
    except Exception as e:
        logger.error(f"Error listing symbols: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/data/upload', methods=['POST'])
@require_api_key
def upload_data():
    """Upload custom market data"""
    try:
        file = request.files['file']
        source_name = request.form.get('source_name', 'custom')
        result = data_processor.store_custom_data(file, source_name)
        return jsonify({
            "status": "success",
            "source": source_name,
            "symbols_added": result
        })
    except Exception as e:
        logger.error(f"Error uploading data: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/gpu/status', methods=['GET'])
@require_api_key
def gpu_status():
    """Get GPU status"""
    try:
        status = gpu_engine.get_status()
        return jsonify({
            "status": "success",
            "gpu_status": status
        })
    except Exception as e:
        logger.error(f"Error getting GPU status: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

@app.route('/strategies', methods=['GET'])
@require_api_key
def list_strategies():
    """List available strategies"""
    try:
        strategies = gpu_engine.list_strategies()
        return jsonify({
            "status": "success",
            "strategies": strategies
        })
    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )