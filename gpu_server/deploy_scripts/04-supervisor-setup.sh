#!/bin/bash
# Supervisor setup for AlphaStrategyLab GPU Server
# This script sets up process management with Supervisor

set -e  # Exit on error

echo "Setting up Supervisor for process management..."

# Set variables
APP_DIR="/opt/alphastrategylab/gpu_server"
LOG_DIR="/opt/alphastrategylab/logs"

# Ensure supervisor is installed
if ! command -v supervisorctl &> /dev/null; then
    echo "Installing supervisor..."
    apt install -y supervisor
fi

# Ensure supervisord is running
systemctl start supervisor
systemctl enable supervisor

# Create supervisor configuration file
echo "Creating supervisor configuration..."
cat > /etc/supervisor/conf.d/alphastrategy-gpu.conf << EOF
[program:alphastrategy-gpu]
command=${APP_DIR}/venv/bin/python ${APP_DIR}/run.py
directory=${APP_DIR}
user=alphauser
autostart=true
autorestart=true
startretries=3
stdout_logfile=${LOG_DIR}/alphastrategy-gpu.log
stderr_logfile=${LOG_DIR}/alphastrategy-gpu.err.log
environment=PATH="${APP_DIR}/venv/bin:/usr/local/cuda/bin:%(ENV_PATH)s",LD_LIBRARY_PATH="/usr/local/cuda/lib64:%(ENV_LD_LIBRARY_PATH)s"
EOF

# Set proper permissions
mkdir -p ${LOG_DIR}
chown -R alphauser:alphauser ${LOG_DIR}
chmod -R 755 ${LOG_DIR}

# Reload supervisor configuration
echo "Reloading supervisor configuration..."
supervisorctl reread
supervisorctl update

# Start the service
echo "Starting the service..."
supervisorctl start alphastrategy-gpu || echo "Service may already be running or failed to start"

# Check service status
echo "Service status:"
supervisorctl status alphastrategy-gpu

echo "Supervisor setup complete"
exit 0