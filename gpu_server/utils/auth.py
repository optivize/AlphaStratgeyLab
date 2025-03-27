"""
Authentication utilities for the GPU server
"""
import logging
from functools import wraps
from flask import request, jsonify
import config

logger = logging.getLogger(__name__)

def require_api_key(func):
    """
    Decorator to require API key for endpoints
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not config.API_KEY_REQUIRED:
            return func(*args, **kwargs)
        
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("API key missing in request")
            return jsonify({
                "status": "error",
                "message": "API key is required"
            }), 401
            
        if api_key != config.API_KEY:
            logger.warning("Invalid API key provided")
            return jsonify({
                "status": "error",
                "message": "Invalid API key"
            }), 401
            
        return func(*args, **kwargs)
        
    return decorated_function