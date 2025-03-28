#!/bin/bash
# Application deployment for AlphaStrategyLab GPU Server
# This script clones the repo and sets up the application code

set -e  # Exit on error

echo "Deploying application code..."

# Set variables
APP_DIR="/opt/alphastrategylab/gpu_server"
CONFIG_DIR="/opt/alphastrategylab/config"
GITHUB_REPO=${GITHUB_REPO:-"https://github.com/yourusername/alphastrategylab.git"}

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt install -y git
fi

# Ask for repository URL if not provided
if [ -z "${GITHUB_REPO}" ] || [ "${GITHUB_REPO}" = "https://github.com/yourusername/alphastrategylab.git" ]; then
    read -p "Enter your GitHub repository URL: " GITHUB_REPO
    if [ -z "${GITHUB_REPO}" ]; then
        echo "No repository URL provided. Exiting."
        exit 1
    fi
fi

# Ask for API keys
read -p "Enter Tiingo API key (optional, press Enter to skip): " TIINGO_API_KEY
read -p "Enter a secure API key for the GPU server (leave blank to generate one): " GPU_SERVER_API_KEY

# Generate API key if not provided
if [ -z "${GPU_SERVER_API_KEY}" ]; then
    GPU_SERVER_API_KEY=$(openssl rand -base64 32)
    echo "Generated GPU server API key: ${GPU_SERVER_API_KEY}"
fi

# Clone the repository if directory doesn't exist or is empty
if [ ! -d "$APP_DIR" ] || [ -z "$(ls -A $APP_DIR)" ]; then
    echo "Cloning repository from ${GITHUB_REPO}..."
    rm -rf $APP_DIR
    git clone $GITHUB_REPO $APP_DIR
else
    echo "Application directory already exists and is not empty"
    echo "Updating existing code..."
    cd $APP_DIR
    git pull
fi

# Make sure we have the gpu_server directory
if [ ! -d "$APP_DIR/gpu_server" ]; then
    echo "Error: gpu_server directory not found in repository"
    echo "Please make sure your repository contains the GPU server code"
    exit 1
fi

# Use the gpu_server directory if that's the structure of the repo
if [ -d "$APP_DIR/gpu_server" ] && [ "$APP_DIR" != "$APP_DIR/gpu_server" ]; then
    echo "Moving gpu_server directory to correct location..."
    mv $APP_DIR/gpu_server/* $APP_DIR/
fi

# Set up Python virtual environment
echo "Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Try to install CUDA-specific packages if a GPU is available
if command -v nvcc &> /dev/null; then
    echo "Installing CUDA-specific packages..."
    pip install pycuda cupy-cuda11x || echo "Warning: Failed to install CUDA packages. GPU acceleration may not work."
fi

# Create environment file
echo "Setting up environment configuration..."
# Load database configuration
source $CONFIG_DIR/db.env

# Create .env file
cat > $APP_DIR/.env << EOF
# Server configuration
GPU_SERVER_HOST=0.0.0.0
GPU_SERVER_PORT=5050
GPU_SERVER_DEBUG=False

# Database configuration
DATABASE_URL=${DATABASE_URL}

# GPU configuration
GPU_DEVICE=0
MAX_CONCURRENT_JOBS=5
GPU_MEMORY_LIMIT=0.8

# Authentication
API_KEY_REQUIRED=True
GPU_SERVER_API_KEY=${GPU_SERVER_API_KEY}

# Data sources (optional)
TIINGO_API_KEY=${TIINGO_API_KEY}
EOF

# Set proper permissions
chown -R alphauser:alphauser $APP_DIR
chmod -R 755 $APP_DIR

echo "Application deployment complete"
echo "API endpoint will be available at: http://YOUR_SERVER_IP:5050"
echo "Use this API key for authentication: ${GPU_SERVER_API_KEY}"

exit 0