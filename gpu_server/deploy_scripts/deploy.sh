#!/bin/bash
# Main deployment script for AlphaStrategyLab GPU Server
# This script runs all deployment steps in sequence

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run this script as root or with sudo${NC}"
  exit 1
fi

# Helper functions
print_step() {
  echo -e "\n${BLUE}===== $1 =====${NC}\n"
}

print_success() {
  echo -e "${GREEN}$1${NC}"
}

print_error() {
  echo -e "${RED}$1${NC}"
}

# Welcome message
clear
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  AlphaStrategyLab GPU Server Deployment  ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo "This script will deploy the AlphaStrategyLab GPU Server"
echo "on this machine. Make sure you have a GPU available for"
echo "optimal performance."
echo ""
echo "The deployment process will:"
echo "  1. Install system dependencies (CUDA, etc.)"
echo "  2. Set up PostgreSQL database"
echo "  3. Deploy the application code"
echo "  4. Configure supervisor for process management"
echo "  5. Set up Nginx as a reverse proxy"
echo "  6. Configure monitoring and maintenance tools"
echo ""
read -p "Do you want to continue? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Deployment cancelled"
  exit 0
fi

# Get directory of this script
SCRIPT_DIR=$(dirname "$0")

# Step 1: System setup
print_step "Step 1/6: System Setup"
$SCRIPT_DIR/01-system-setup.sh || {
  print_error "System setup failed. Please check the errors and try again."
  exit 1
}
print_success "System setup completed successfully!"

# Step 2: Database setup
print_step "Step 2/6: Database Setup"
$SCRIPT_DIR/02-database-setup.sh || {
  print_error "Database setup failed. Please check the errors and try again."
  exit 1
}
print_success "Database setup completed successfully!"

# Step 3: Application deployment
print_step "Step 3/6: Application Deployment"
$SCRIPT_DIR/03-app-deploy.sh || {
  print_error "Application deployment failed. Please check the errors and try again."
  exit 1
}
print_success "Application deployment completed successfully!"

# Step 4: Supervisor setup
print_step "Step 4/6: Supervisor Setup"
$SCRIPT_DIR/04-supervisor-setup.sh || {
  print_error "Supervisor setup failed. Please check the errors and try again."
  exit 1
}
print_success "Supervisor setup completed successfully!"

# Step 5: Nginx setup
print_step "Step 5/6: Nginx Setup"
$SCRIPT_DIR/05-nginx-setup.sh || {
  print_error "Nginx setup failed. Please check the errors and try again."
  exit 1
}
print_success "Nginx setup completed successfully!"

# Step 6: Monitoring setup
print_step "Step 6/6: Monitoring Setup"
$SCRIPT_DIR/06-monitoring-setup.sh || {
  print_error "Monitoring setup failed. Please check the errors and try again."
  exit 1
}
print_success "Monitoring setup completed successfully!"

# Deployment complete
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}      Deployment Completed Successfully   ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""

# Display server information
SERVER_IP=$(hostname -I | awk '{print $1}')
API_KEY=$(grep GPU_SERVER_API_KEY /opt/alphastrategylab/gpu_server/.env | cut -d= -f2)

echo "GPU Server is now running and accessible at:"
echo "  http://${SERVER_IP}"
echo ""
echo "API Key for authentication: ${API_KEY}"
echo ""
echo "You can check the status of the server with:"
echo "  sudo supervisorctl status alphastrategy-gpu"
echo ""
echo "You can view the logs with:"
echo "  sudo tail -f /opt/alphastrategylab/logs/alphastrategy-gpu.log"
echo ""
echo "For more information, see the README.md file"

exit 0