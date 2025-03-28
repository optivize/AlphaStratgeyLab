#!/bin/bash
# Monitoring and maintenance setup for AlphaStrategyLab GPU Server
# This script sets up log rotation, backup scripts, and monitoring tools

set -e  # Exit on error

echo "Setting up monitoring and maintenance tools..."

# Set variables
LOG_DIR="/opt/alphastrategylab/logs"
BACKUP_DIR="/opt/alphastrategylab/backups"
CONFIG_DIR="/opt/alphastrategylab/config"
APP_DIR="/opt/alphastrategylab/gpu_server"

# Ensure directories exist
mkdir -p ${LOG_DIR}
mkdir -p ${BACKUP_DIR}
mkdir -p ${CONFIG_DIR}

# Set up log rotation
echo "Setting up log rotation..."
cat > /etc/logrotate.d/alphastrategy-gpu << EOF
${LOG_DIR}/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 alphauser alphauser
    sharedscripts
    postrotate
        supervisorctl restart alphastrategy-gpu >/dev/null 2>&1 || true
    endscript
}
EOF

# Create database backup script
echo "Creating database backup script..."
cat > ${CONFIG_DIR}/backup-database.sh << EOF
#!/bin/bash
# Database backup script
# This script creates a backup of the PostgreSQL database

# Load database configuration
source ${CONFIG_DIR}/db.env

# Extract database name from DATABASE_URL
DB_NAME=\$(echo \$DATABASE_URL | sed -r 's/.*\/([^?]+).*/\1/')

# Create backup filename with timestamp
TIMESTAMP=\$(date +%Y%m%d-%H%M%S)
BACKUP_FILE=${BACKUP_DIR}/\${DB_NAME}-\${TIMESTAMP}.sql

# Create backup
echo "Creating database backup to \${BACKUP_FILE}..."
PGPASSWORD=\$(echo \$DATABASE_URL | sed -r 's/.*:([^@]+)@.*/\1/') pg_dump -h localhost -U \$(echo \$DATABASE_URL | sed -r 's/.*\/\/([^:]+):.*/\1/') \${DB_NAME} > \${BACKUP_FILE}

# Compress the backup
gzip \${BACKUP_FILE}

# Remove backups older than 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -type f -mtime +30 -delete

echo "Database backup completed"
EOF

# Make backup script executable
chmod +x ${CONFIG_DIR}/backup-database.sh

# Set up cron job for daily backups
echo "Setting up cron job for daily backups..."
(crontab -l 2>/dev/null || echo "") | grep -v "${CONFIG_DIR}/backup-database.sh" | { cat; echo "0 2 * * * ${CONFIG_DIR}/backup-database.sh >> ${LOG_DIR}/backup.log 2>&1"; } | crontab -

# Create system status script
echo "Creating system status script..."
cat > ${CONFIG_DIR}/system-status.sh << EOF
#!/bin/bash
# System status script
# This script checks the status of the GPU server components

echo "========== AlphaStrategyLab GPU Server Status =========="
date

echo -e "\n--- GPU Status ---"
nvidia-smi || echo "No GPU detected or drivers not installed"

echo -e "\n--- Service Status ---"
supervisorctl status alphastrategy-gpu

echo -e "\n--- Disk Space ---"
df -h /

echo -e "\n--- Memory Usage ---"
free -h

echo -e "\n--- Recent Logs ---"
tail -n 20 ${LOG_DIR}/alphastrategy-gpu.log

echo -e "\n======================================================="
EOF

# Make status script executable
chmod +x ${CONFIG_DIR}/system-status.sh

# Create an update script
echo "Creating update script..."
cat > ${CONFIG_DIR}/update-app.sh << EOF
#!/bin/bash
# Application update script
# This script updates the GPU server application code

set -e  # Exit on error

cd ${APP_DIR}

echo "Pulling latest code..."
git pull

echo "Installing any new dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Restarting service..."
supervisorctl restart alphastrategy-gpu

echo "Update complete"
EOF

# Make update script executable
chmod +x ${CONFIG_DIR}/update-app.sh

# Set proper permissions for all scripts
chown -R alphauser:alphauser ${CONFIG_DIR}
chmod -R 755 ${CONFIG_DIR}

echo "Monitoring and maintenance setup complete"
echo "You can check system status with: ${CONFIG_DIR}/system-status.sh"
echo "You can update the application with: ${CONFIG_DIR}/update-app.sh"
echo "Database backups will run daily at 2 AM"

exit 0