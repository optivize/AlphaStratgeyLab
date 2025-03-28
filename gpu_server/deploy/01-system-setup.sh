#!/bin/bash
# System setup for AlphaStrategyLab GPU Server
# This script installs all necessary system dependencies

set -e  # Exit on error

echo "Installing system dependencies..."

# Update package lists
apt update

# Install basic system dependencies
apt install -y build-essential python3-dev python3-pip python3-venv nginx supervisor

# Check if NVIDIA GPU is available
if lspci | grep -i nvidia > /dev/null; then
  echo "NVIDIA GPU detected"
  
  # Check if NVIDIA drivers are already installed
  if ! command -v nvidia-smi &> /dev/null; then
    echo "Installing NVIDIA drivers..."
    apt install -y nvidia-driver-525
    
    # Verify installation
    echo "Verifying NVIDIA driver installation..."
    nvidia-smi || echo "Warning: NVIDIA driver installation may have failed"
  else
    echo "NVIDIA drivers already installed"
    nvidia-smi
  fi
  
  # Check if CUDA is already installed
  if ! command -v nvcc &> /dev/null; then
    echo "Installing CUDA Toolkit..."
    
    # Download CUDA installer
    cd /tmp
    wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
    
    # Run installer in silent mode
    sh cuda_11.8.0_520.61.05_linux.run --silent --toolkit --samples --override
    
    # Add CUDA to system PATH if not already there
    if ! grep -q 'export PATH=/usr/local/cuda/bin:$PATH' /etc/profile.d/cuda.sh 2>/dev/null; then
      echo 'export PATH=/usr/local/cuda/bin:$PATH' > /etc/profile.d/cuda.sh
      echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
      chmod +x /etc/profile.d/cuda.sh
    fi
    
    # Source the file to update current session
    source /etc/profile.d/cuda.sh
    
    # Verify CUDA installation
    echo "Verifying CUDA installation..."
    nvcc --version || echo "Warning: CUDA installation may have failed"
  else
    echo "CUDA already installed"
    nvcc --version
  fi
else
  echo "Warning: No NVIDIA GPU detected. GPU acceleration will not be available."
fi

# Create application directories
mkdir -p /opt/alphastrategylab/gpu_server
mkdir -p /opt/alphastrategylab/logs
mkdir -p /opt/alphastrategylab/backups

# Create a dedicated user for the application
if ! id -u alphauser &>/dev/null; then
    useradd -m -s /bin/bash alphauser
    echo "Created user: alphauser"
fi

# Set proper ownership
chown -R alphauser:alphauser /opt/alphastrategylab

echo "System setup complete"
exit 0