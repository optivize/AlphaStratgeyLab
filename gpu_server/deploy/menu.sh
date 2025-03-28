#!/bin/bash
# Interactive menu for AlphaStrategyLab GPU Server deployment

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

# Helper function for printing messages
print_message() {
  echo -e "${BLUE}$1${NC}"
}

print_success() {
  echo -e "${GREEN}$1${NC}"
}

print_error() {
  echo -e "${RED}$1${NC}"
}

# Variables
SCRIPTS_DIR=$(dirname "$0")
CONFIG_FILE="$SCRIPTS_DIR/deployment.conf"

# Load configuration if it exists
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
fi

# Main menu
show_menu() {
  clear
  echo "==========================================="
  echo "  AlphaStrategyLab GPU Server Deployment  "
  echo "==========================================="
  echo ""
  echo "1) Full automated deployment"
  echo "2) Step-by-step deployment"
  echo "3) Manage deployed service"
  echo "4) View logs"
  echo "5) System status"
  echo "6) Configuration"
  echo "7) Exit"
  echo ""
  echo "==========================================="
  echo ""
}

# Full automated deployment
full_deployment() {
  print_message "Starting full automated deployment..."
  
  # Ask for GitHub repository URL
  if [ -z "${GITHUB_REPO}" ]; then
    read -p "Enter your GitHub repository URL: " GITHUB_REPO
  else
    read -p "Enter your GitHub repository URL [$GITHUB_REPO]: " input
    if [ ! -z "$input" ]; then
      GITHUB_REPO=$input
    fi
  fi
  
  # Save configuration
  echo "GITHUB_REPO=\"$GITHUB_REPO\"" > "$CONFIG_FILE"
  
  # Run the deployment script
  if $SCRIPTS_DIR/deploy.sh; then
    print_success "Deployment completed successfully!"
  else
    print_error "Deployment failed. Check the error messages above."
  fi
  
  read -p "Press Enter to continue..."
}

# Step-by-step deployment
step_deployment() {
  local choice
  
  while true; do
    clear
    echo "==========================================="
    echo "      Step-by-Step Deployment Menu        "
    echo "==========================================="
    echo ""
    echo "1) System setup (NVIDIA drivers, CUDA, etc.)"
    echo "2) Database setup"
    echo "3) Application deployment"
    echo "4) Supervisor setup"
    echo "5) Nginx setup"
    echo "6) Monitoring setup"
    echo "7) Return to main menu"
    echo ""
    echo "==========================================="
    echo ""
    read -p "Enter your choice [1-7]: " choice
    
    case $choice in
      1)
        print_message "Running system setup..."
        if $SCRIPTS_DIR/01-system-setup.sh; then
          print_success "System setup completed successfully!"
        else
          print_error "System setup failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      2)
        print_message "Running database setup..."
        if $SCRIPTS_DIR/02-database-setup.sh; then
          print_success "Database setup completed successfully!"
        else
          print_error "Database setup failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      3)
        print_message "Running application deployment..."
        # Ask for GitHub repository URL if not set
        if [ -z "${GITHUB_REPO}" ]; then
          read -p "Enter your GitHub repository URL: " GITHUB_REPO
          echo "GITHUB_REPO=\"$GITHUB_REPO\"" > "$CONFIG_FILE"
        fi
        export GITHUB_REPO
        
        if $SCRIPTS_DIR/03-app-deploy.sh; then
          print_success "Application deployment completed successfully!"
        else
          print_error "Application deployment failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      4)
        print_message "Running supervisor setup..."
        if $SCRIPTS_DIR/04-supervisor-setup.sh; then
          print_success "Supervisor setup completed successfully!"
        else
          print_error "Supervisor setup failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      5)
        print_message "Running Nginx setup..."
        if $SCRIPTS_DIR/05-nginx-setup.sh; then
          print_success "Nginx setup completed successfully!"
        else
          print_error "Nginx setup failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      6)
        print_message "Running monitoring setup..."
        if $SCRIPTS_DIR/06-monitoring-setup.sh; then
          print_success "Monitoring setup completed successfully!"
        else
          print_error "Monitoring setup failed. Check the error messages above."
        fi
        read -p "Press Enter to continue..."
        ;;
      7)
        return
        ;;
      *)
        print_error "Invalid option. Please try again."
        read -p "Press Enter to continue..."
        ;;
    esac
  done
}

# Manage service
manage_service() {
  local choice
  
  while true; do
    clear
    echo "==========================================="
    echo "          Service Management Menu         "
    echo "==========================================="
    echo ""
    echo "1) Check service status"
    echo "2) Start service"
    echo "3) Stop service"
    echo "4) Restart service"
    echo "5) Update application code"
    echo "6) Return to main menu"
    echo ""
    echo "==========================================="
    echo ""
    read -p "Enter your choice [1-6]: " choice
    
    case $choice in
      1)
        print_message "Service status:"
        supervisorctl status alphastrategy-gpu
        read -p "Press Enter to continue..."
        ;;
      2)
        print_message "Starting service..."
        supervisorctl start alphastrategy-gpu
        read -p "Press Enter to continue..."
        ;;
      3)
        print_message "Stopping service..."
        supervisorctl stop alphastrategy-gpu
        read -p "Press Enter to continue..."
        ;;
      4)
        print_message "Restarting service..."
        supervisorctl restart alphastrategy-gpu
        read -p "Press Enter to continue..."
        ;;
      5)
        print_message "Updating application code..."
        if [ -f "/opt/alphastrategylab/config/update-app.sh" ]; then
          /opt/alphastrategylab/config/update-app.sh
          print_success "Application update completed!"
        else
          print_error "Update script not found. Deploy the application first."
        fi
        read -p "Press Enter to continue..."
        ;;
      6)
        return
        ;;
      *)
        print_error "Invalid option. Please try again."
        read -p "Press Enter to continue..."
        ;;
    esac
  done
}

# View logs
view_logs() {
  local choice
  local log_file
  
  while true; do
    clear
    echo "==========================================="
    echo "               Log Viewer                 "
    echo "==========================================="
    echo ""
    echo "1) Application logs"
    echo "2) Error logs"
    echo "3) Nginx access logs"
    echo "4) Nginx error logs"
    echo "5) Database backup logs"
    echo "6) Return to main menu"
    echo ""
    echo "==========================================="
    echo ""
    read -p "Enter your choice [1-6]: " choice
    
    case $choice in
      1)
        log_file="/opt/alphastrategylab/logs/alphastrategy-gpu.log"
        if [ -f "$log_file" ]; then
          less "$log_file"
        else
          print_error "Log file not found. Deploy the application first."
          read -p "Press Enter to continue..."
        fi
        ;;
      2)
        log_file="/opt/alphastrategylab/logs/alphastrategy-gpu.err.log"
        if [ -f "$log_file" ]; then
          less "$log_file"
        else
          print_error "Log file not found. Deploy the application first."
          read -p "Press Enter to continue..."
        fi
        ;;
      3)
        log_file="/var/log/nginx/access.log"
        if [ -f "$log_file" ]; then
          less "$log_file"
        else
          print_error "Nginx access log not found. Install Nginx first."
          read -p "Press Enter to continue..."
        fi
        ;;
      4)
        log_file="/var/log/nginx/error.log"
        if [ -f "$log_file" ]; then
          less "$log_file"
        else
          print_error "Nginx error log not found. Install Nginx first."
          read -p "Press Enter to continue..."
        fi
        ;;
      5)
        log_file="/opt/alphastrategylab/logs/backup.log"
        if [ -f "$log_file" ]; then
          less "$log_file"
        else
          print_error "Backup log not found. Run a backup first."
          read -p "Press Enter to continue..."
        fi
        ;;
      6)
        return
        ;;
      *)
        print_error "Invalid option. Please try again."
        read -p "Press Enter to continue..."
        ;;
    esac
  done
}

# System status
system_status() {
  clear
  echo "==========================================="
  echo "             System Status                "
  echo "==========================================="
  echo ""
  
  if [ -f "/opt/alphastrategylab/config/system-status.sh" ]; then
    /opt/alphastrategylab/config/system-status.sh
  else
    echo "System status script not found. Running basic checks..."
    echo ""
    echo "--- GPU Status ---"
    if command -v nvidia-smi &> /dev/null; then
      nvidia-smi
    else
      echo "NVIDIA drivers not installed or GPU not detected"
    fi
    
    echo ""
    echo "--- Service Status ---"
    if command -v supervisorctl &> /dev/null; then
      supervisorctl status alphastrategy-gpu
    else
      echo "Supervisor not installed"
    fi
    
    echo ""
    echo "--- Disk Space ---"
    df -h /
    
    echo ""
    echo "--- Memory Usage ---"
    free -h
  fi
  
  echo ""
  read -p "Press Enter to continue..."
}

# Configuration
configure() {
  local choice
  
  while true; do
    clear
    echo "==========================================="
    echo "           Configuration Menu             "
    echo "==========================================="
    echo ""
    echo "1) Set GitHub repository URL"
    echo "2) Configure Tiingo API key"
    echo "3) Reset GPU server API key"
    echo "4) Configure database backup schedule"
    echo "5) Return to main menu"
    echo ""
    echo "==========================================="
    echo ""
    read -p "Enter your choice [1-5]: " choice
    
    case $choice in
      1)
        read -p "Enter your GitHub repository URL: " GITHUB_REPO
        echo "GITHUB_REPO=\"$GITHUB_REPO\"" > "$CONFIG_FILE"
        print_success "GitHub repository URL updated"
        read -p "Press Enter to continue..."
        ;;
      2)
        read -p "Enter your Tiingo API key: " TIINGO_API_KEY
        if [ -f "/opt/alphastrategylab/gpu_server/.env" ]; then
          sed -i "s/TIINGO_API_KEY=.*/TIINGO_API_KEY=$TIINGO_API_KEY/" /opt/alphastrategylab/gpu_server/.env
          print_success "Tiingo API key updated"
          read -p "Do you want to restart the service to apply changes? (y/n): " restart
          if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
            supervisorctl restart alphastrategy-gpu
          fi
        else
          print_error "Environment file not found. Deploy the application first."
        fi
        read -p "Press Enter to continue..."
        ;;
      3)
        NEW_API_KEY=$(openssl rand -base64 32)
        if [ -f "/opt/alphastrategylab/gpu_server/.env" ]; then
          sed -i "s/GPU_SERVER_API_KEY=.*/GPU_SERVER_API_KEY=$NEW_API_KEY/" /opt/alphastrategylab/gpu_server/.env
          print_success "GPU server API key reset to: $NEW_API_KEY"
          read -p "Do you want to restart the service to apply changes? (y/n): " restart
          if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
            supervisorctl restart alphastrategy-gpu
          fi
        else
          print_error "Environment file not found. Deploy the application first."
        fi
        read -p "Press Enter to continue..."
        ;;
      4)
        read -p "Enter cron schedule for database backups (e.g., '0 2 * * *' for 2 AM daily): " CRON_SCHEDULE
        if [ -f "/opt/alphastrategylab/config/backup-database.sh" ]; then
          (crontab -l 2>/dev/null || echo "") | grep -v "/opt/alphastrategylab/config/backup-database.sh" | { cat; echo "$CRON_SCHEDULE /opt/alphastrategylab/config/backup-database.sh >> /opt/alphastrategylab/logs/backup.log 2>&1"; } | crontab -
          print_success "Database backup schedule updated"
        else
          print_error "Backup script not found. Deploy the application first."
        fi
        read -p "Press Enter to continue..."
        ;;
      5)
        return
        ;;
      *)
        print_error "Invalid option. Please try again."
        read -p "Press Enter to continue..."
        ;;
    esac
  done
}

# Main program
main() {
  local choice
  
  while true; do
    show_menu
    read -p "Enter your choice [1-7]: " choice
    
    case $choice in
      1)
        full_deployment
        ;;
      2)
        step_deployment
        ;;
      3)
        manage_service
        ;;
      4)
        view_logs
        ;;
      5)
        system_status
        ;;
      6)
        configure
        ;;
      7)
        echo "Exiting..."
        exit 0
        ;;
      *)
        print_error "Invalid option. Please try again."
        read -p "Press Enter to continue..."
        ;;
    esac
  done
}

# Start the main program
main