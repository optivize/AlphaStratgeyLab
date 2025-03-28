#!/bin/bash
# Application deployment for AlphaStrategyLab GPU Server
# This script clones the repo and sets up the application code

set -e  # Exit on error

echo "Deploying application code..."

# Set variables
APP_DIR="/opt/alphastrategylab/gpu_server"
CONFIG_DIR="/opt/alphastrategylab/config"
SOURCE_DIR=${SOURCE_DIR:-"$(dirname $(dirname $(realpath $0)))"}

# Check if git is installed (may still be needed for updates)
if ! command -v git &> /dev/null; then
    echo "Installing git..."
    apt install -y git
fi

# Ask for API keys
read -p "Enter Tiingo API key (optional, press Enter to skip): " TIINGO_API_KEY
read -p "Enter a secure API key for the GPU server (leave blank to generate one): " GPU_SERVER_API_KEY

# Generate API key if not provided
if [ -z "${GPU_SERVER_API_KEY}" ]; then
    GPU_SERVER_API_KEY=$(openssl rand -base64 32)
    echo "Generated GPU server API key: ${GPU_SERVER_API_KEY}"
fi

# Create application directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    echo "Creating application directory..."
    mkdir -p $APP_DIR
fi

# Copy the GPU server code to the application directory
echo "Copying GPU server code to application directory..."
mkdir -p $APP_DIR
if [ -d "$SOURCE_DIR/gpu_server" ]; then
    # Copy from the gpu_server subdirectory
    rsync -av --exclude '.git' "$SOURCE_DIR/gpu_server/" $APP_DIR/
elif [ -d "$SOURCE_DIR" ]; then
    # If we're already in the gpu_server directory or have all the code
    rsync -av --exclude '.git' "$SOURCE_DIR/" $APP_DIR/
else
    echo "Error: Source directory not found"
    echo "Please make sure the gpu_server code is available"
    exit 1
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

# Check for CUDA and install appropriate Python packages
if command -v nvcc &> /dev/null; then
    echo "CUDA detected. Checking for CUDA Python packages..."
    
    # Check if CUDA Python packages are already installed
    if python3 -c "import pycuda" 2>/dev/null && python3 -c "import cupy" 2>/dev/null; then
        echo "CUDA Python packages already installed"
    else
        echo "Installing CUDA-specific Python packages..."
        
        # Check for automated mode
        if [ "${AUTO_SKIP_CUDA}" = "1" ]; then
            echo "AUTO_SKIP_CUDA=1: Skipping CUDA Python packages installation in automated mode"
        else
            read -p "Do you want to install CUDA Python packages? (y/n): " install_cuda_py
            if [ "$install_cuda_py" = "y" ] || [ "$install_cuda_py" = "Y" ]; then
                # Get CUDA version to determine correct cupy package
                CUDA_VERSION=$(nvcc --version | grep "release" | awk '{print $6}' | cut -c2-)
                CUDA_MAJOR=$(echo $CUDA_VERSION | cut -d. -f1)
                CUDA_MINOR=$(echo $CUDA_VERSION | cut -d. -f2)
                
                echo "Detected CUDA version: $CUDA_VERSION"
                
                # Install appropriate CUDA packages based on version
                if [ $CUDA_MAJOR -eq 11 ]; then
                    echo "Installing cupy-cuda11x and pycuda..."
                    pip install pycuda cupy-cuda11x || echo "Warning: Failed to install CUDA packages. GPU acceleration may not work."
                elif [ $CUDA_MAJOR -eq 12 ]; then
                    echo "Installing cupy-cuda12x and pycuda..."
                    pip install pycuda cupy-cuda12x || echo "Warning: Failed to install CUDA packages. GPU acceleration may not work."
                else
                    echo "Installing generic cupy and pycuda..."
                    pip install pycuda cupy || echo "Warning: Failed to install CUDA packages. GPU acceleration may not work."
                fi
            else
                echo "Skipping CUDA Python packages installation. GPU acceleration will not be available."
            fi
        fi
    fi
else
    echo "CUDA not detected. Skipping CUDA-specific Python packages."
    echo "Note: GPU acceleration will not be available without CUDA."
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