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

# Ensure PostgreSQL is running - handle both systemd and non-systemd environments
if command -v systemctl &> /dev/null && systemctl list-units &> /dev/null; then
    echo "Using systemd to start PostgreSQL..."
    systemctl start postgresql || echo "Warning: Failed to start PostgreSQL with systemd"
    systemctl enable postgresql || echo "Warning: Failed to enable PostgreSQL with systemd"
else
    echo "Running in a non-systemd environment, using alternative service management..."
    if [ -f /etc/init.d/postgresql ]; then
        /etc/init.d/postgresql start || echo "Warning: Failed to start PostgreSQL with init.d script"
    elif [ -d /var/run/postgresql ]; then
        # For Docker/container environments where postgres might need manual starting
        echo "Attempting to start PostgreSQL manually..."
        if id -u postgres &>/dev/null; then
            # Start PostgreSQL server manually as postgres user if it's not running
            if ! sudo -u postgres pg_isready -q; then
                echo "Starting PostgreSQL server manually..."
                sudo -u postgres pg_ctl -D /var/lib/postgresql/14/main -l /var/log/postgresql/postgresql-14-main.log start || echo "Warning: Manual PostgreSQL start failed"
            else
                echo "PostgreSQL is already running"
            fi
        else
            echo "PostgreSQL user not found, cannot start manually"
        fi
    else
        echo "Warning: Could not determine how to start PostgreSQL in this environment"
        echo "Please ensure PostgreSQL is running before proceeding"
    fi
fi

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