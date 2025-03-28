#!/bin/bash
# Database setup for AlphaStrategyLab GPU Server
# This script sets up the PostgreSQL database

set -e  # Exit on error

echo "Setting up PostgreSQL database..."

# Check if PostgreSQL is installed, if not install it
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    apt install -y postgresql postgresql-contrib
else
    echo "PostgreSQL already installed"
fi

# Ensure PostgreSQL is running
systemctl start postgresql
systemctl enable postgresql

# Set database credentials (you might want to change these values)
DB_USER="alphauser"
DB_PASSWORD=$(openssl rand -base64 16)  # Generate a secure random password
DB_NAME="alphastrategy"

# Create database and user
echo "Creating database and user..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "User may already exist"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" || echo "Database may already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Save the database connection string to a config file for later use
CONFIG_DIR="/opt/alphastrategylab/config"
mkdir -p $CONFIG_DIR
echo "DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost/${DB_NAME}" > $CONFIG_DIR/db.env

echo "Database setup complete"
echo "Database credentials saved to: $CONFIG_DIR/db.env"
echo "Be sure to use these in your application configuration"

exit 0