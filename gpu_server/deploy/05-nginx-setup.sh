#!/bin/bash
# Nginx setup for AlphaStrategyLab GPU Server
# This script sets up Nginx as a reverse proxy

set -e  # Exit on error

echo "Setting up Nginx as reverse proxy..."

# Ensure nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt install -y nginx
fi

# Ask for domain name or use server IP
read -p "Enter domain name for GPU server (leave blank to use server IP): " DOMAIN_NAME

# Create Nginx configuration file
echo "Creating Nginx configuration..."
if [ -z "${DOMAIN_NAME}" ]; then
    # Use server IP instead of domain
    SERVER_IP=$(hostname -I | awk '{print $1}')
    DOMAIN_NAME=$SERVER_IP
    echo "Using server IP: ${SERVER_IP}"
    
    # Create configuration file
    cat > /etc/nginx/sites-available/alphastrategy-gpu << EOF
server {
    listen 80;
    server_name ${SERVER_IP};

    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF
else
    # Use provided domain name
    echo "Using domain name: ${DOMAIN_NAME}"
    
    # Create configuration file
    cat > /etc/nginx/sites-available/alphastrategy-gpu << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }
}
EOF
fi

# Enable the site
ln -sf /etc/nginx/sites-available/alphastrategy-gpu /etc/nginx/sites-enabled/

# Test and restart Nginx
echo "Testing Nginx configuration..."
nginx -t

echo "Restarting Nginx..."
systemctl restart nginx
systemctl enable nginx

# Ask if SSL should be set up
read -p "Do you want to set up SSL with Let's Encrypt? (y/n): " SETUP_SSL

if [ "${SETUP_SSL}" = "y" ] || [ "${SETUP_SSL}" = "Y" ]; then
    # Check if certbot is installed
    if ! command -v certbot &> /dev/null; then
        echo "Installing certbot..."
        apt install -y certbot python3-certbot-nginx
    fi
    
    # Run certbot to get SSL certificate
    if [ "${DOMAIN_NAME}" != "${SERVER_IP}" ]; then
        echo "Setting up SSL with Let's Encrypt..."
        certbot --nginx -d ${DOMAIN_NAME} --non-interactive --agree-tos -m admin@${DOMAIN_NAME} || echo "SSL setup failed. You may need to configure DNS first."
    else
        echo "Cannot set up SSL with server IP. You need a domain name for SSL."
    fi
fi

echo "Nginx setup complete"
if [ "${DOMAIN_NAME}" != "${SERVER_IP}" ]; then
    echo "Your GPU server should be available at: http://${DOMAIN_NAME}"
    if [ "${SETUP_SSL}" = "y" ] || [ "${SETUP_SSL}" = "Y" ]; then
        echo "With SSL: https://${DOMAIN_NAME}"
    fi
else
    echo "Your GPU server should be available at: http://${SERVER_IP}"
fi

exit 0