#!/bin/bash
# Make all deployment scripts executable

# Get the directory of this script
SCRIPT_DIR=$(dirname "$0")

echo "Setting execute permissions on all deployment scripts..."
chmod +x "$SCRIPT_DIR/01-system-setup.sh"
chmod +x "$SCRIPT_DIR/02-database-setup.sh"
chmod +x "$SCRIPT_DIR/03-app-deploy.sh"
chmod +x "$SCRIPT_DIR/04-supervisor-setup.sh"
chmod +x "$SCRIPT_DIR/05-nginx-setup.sh"
chmod +x "$SCRIPT_DIR/06-monitoring-setup.sh"
chmod +x "$SCRIPT_DIR/deploy.sh"
chmod +x "$SCRIPT_DIR/menu.sh"
chmod +x "$SCRIPT_DIR/make_executable.sh"

echo "All scripts are now executable!"