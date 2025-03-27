"""
Entry point script for the GPU server
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get("GPU_SERVER_DEBUG", "True").lower() in ("true", "1", "t", "yes") else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Import app after loading environment variables
from app import app

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.environ.get("GPU_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("GPU_SERVER_PORT", 5050))
    debug = os.environ.get("GPU_SERVER_DEBUG", "True").lower() in ("true", "1", "t", "yes")
    
    # Start the server
    app.run(host=host, port=port, debug=debug)