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
  
  # Comprehensive check for NVIDIA drivers
  if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo "NVIDIA drivers already installed and working"
    echo "Driver info:"
    nvidia-smi | grep "Driver Version"
  else
    echo "NVIDIA drivers not detected or not working properly"
    
    # Check for automated mode
    if [ "${AUTO_SKIP_NVIDIA}" = "1" ]; then
      echo "AUTO_SKIP_NVIDIA=1: Skipping NVIDIA driver installation in automated mode"
    else
      read -p "Do you want to install NVIDIA drivers? (y/n): " install_drivers
      if [ "$install_drivers" = "y" ] || [ "$install_drivers" = "Y" ]; then
        echo "Installing NVIDIA drivers..."
        apt install -y nvidia-driver-525
        
        # Verify installation
        echo "Verifying NVIDIA driver installation..."
        nvidia-smi || echo "Warning: NVIDIA driver installation may have failed"
      else
        echo "Skipping NVIDIA driver installation. GPU acceleration might not work."
      fi
    fi
  fi
  
  # Comprehensive check for CUDA
  if command -v nvcc &> /dev/null; then
    echo "CUDA Toolkit already installed"
    echo "CUDA Version:"
    nvcc --version | grep "release"
  elif [ -d "/usr/local/cuda" ] && [ -f "/usr/local/cuda/bin/nvcc" ]; then
    echo "CUDA Toolkit found but not in PATH"
    echo "Adding CUDA to system PATH..."
    echo 'export PATH=/usr/local/cuda/bin:$PATH' > /etc/profile.d/cuda.sh
    echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
    chmod +x /etc/profile.d/cuda.sh
    source /etc/profile.d/cuda.sh
    
    echo "CUDA Version:"
    nvcc --version
  else
    echo "CUDA Toolkit not detected"
    
    # Check for automated mode
    if [ "${AUTO_SKIP_CUDA}" = "1" ]; then
      echo "AUTO_SKIP_CUDA=1: Skipping CUDA installation in automated mode"
    else
      read -p "Do you want to install CUDA Toolkit? (y/n): " install_cuda
      if [ "$install_cuda" = "y" ] || [ "$install_cuda" = "Y" ]; then
        echo "Installing CUDA Toolkit..."
        
        # Download CUDA installer
        cd /tmp
        wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_520.61.05_linux.run
        
        # Run installer in silent mode
        sh cuda_11.8.0_520.61.05_linux.run --silent --toolkit --samples --override
        
        # Add CUDA to system PATH
        echo 'export PATH=/usr/local/cuda/bin:$PATH' > /etc/profile.d/cuda.sh
        echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> /etc/profile.d/cuda.sh
        chmod +x /etc/profile.d/cuda.sh
        
        # Source the file to update current session
        source /etc/profile.d/cuda.sh
        
        # Verify CUDA installation
        echo "Verifying CUDA installation..."
        nvcc --version || echo "Warning: CUDA installation may have failed"
      else
        echo "Skipping CUDA installation. GPU acceleration will not be available."
      fi
    fi
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