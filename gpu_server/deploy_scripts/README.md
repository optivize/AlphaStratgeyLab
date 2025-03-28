# AlphaStrategyLab GPU Server Deployment Scripts

These scripts automate the deployment of the AlphaStrategyLab GPU Server on a remote server with GPU capabilities.

## Prerequisites

- A server with Ubuntu 20.04 or newer
- NVIDIA GPU (recommended but not required)
- Root or sudo access
- Git repository containing the AlphaStrategyLab GPU Server code

## Deployment Instructions

### 1. Prepare Your Server

1. SSH into your server:
   ```bash
   ssh username@your-server-ip
   ```

2. Make sure your server is up to date:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

### 2. Clone and Deploy

1. Transfer the deployment scripts to your server:
   ```bash
   scp -r gpu_server/deploy_scripts/* username@your-server-ip:~/deploy_scripts/
   ssh username@your-server-ip
   cd ~/deploy_scripts
   ```

2. Make all scripts executable:
   ```bash
   chmod +x *.sh
   ```

3. Run the main deployment script:
   ```bash
   sudo ./deploy.sh
   ```

4. Follow the prompts during the installation process. You will be asked for:
   - Tiingo API key (optional)
   - GPU Server API key (will be generated if not provided)
   - Domain name for the server (optional, will use server IP if not provided)
   - Whether to set up SSL with Let's Encrypt

### 3. Manual Deployment

If you prefer to run each step manually, you can execute the scripts in order:

1. System setup:
   ```bash
   sudo ./01-system-setup.sh
   ```

2. Database setup:
   ```bash
   sudo ./02-database-setup.sh
   ```

3. Application deployment:
   ```bash
   sudo ./03-app-deploy.sh
   ```

4. Supervisor setup:
   ```bash
   sudo ./04-supervisor-setup.sh
   ```

5. Nginx setup:
   ```bash
   sudo ./05-nginx-setup.sh
   ```

6. Monitoring setup:
   ```bash
   sudo ./06-monitoring-setup.sh
   ```

## Post-Deployment

After successful deployment, you can:

1. Check the service status:
   ```bash
   sudo supervisorctl status alphastrategy-gpu
   ```

2. View logs:
   ```bash
   tail -f /opt/alphastrategylab/logs/alphastrategy-gpu.log
   ```

3. Access the API at:
   ```
   http://your-server-ip
   ```
   or
   ```
   https://your-domain.com
   ```
   (if you set up SSL)

4. Check the system status:
   ```bash
   sudo /opt/alphastrategylab/config/system-status.sh
   ```

## Maintenance

### Update the Application

To update the application with the latest code from your repository:

```bash
sudo /opt/alphastrategylab/config/update-app.sh
```

### Database Backups

Database backups are automatically created daily at 2 AM and stored in `/opt/alphastrategylab/backups`. You can manually trigger a backup with:

```bash
sudo /opt/alphastrategylab/config/backup-database.sh
```

## Troubleshooting

If you encounter issues during deployment:

1. Check the logs:
   ```bash
   tail -f /opt/alphastrategylab/logs/alphastrategy-gpu.log
   ```

2. Check the supervisor error log:
   ```bash
   tail -f /opt/alphastrategylab/logs/alphastrategy-gpu.err.log
   ```

3. Check the service status:
   ```bash
   sudo supervisorctl status alphastrategy-gpu
   ```

4. Restart the service:
   ```bash
   sudo supervisorctl restart alphastrategy-gpu
   ```

### Container Environment Issues

If deploying in a container environment (Docker, Kubernetes, etc.):

1. Use the automated non-interactive mode:
   ```bash
   export AUTO_MODE=1
   sudo -E ./deploy.sh
   ```

2. Common container-specific issues:
   - Systemd not available: The scripts will automatically detect this and use alternative service management
   - PostgreSQL service fails to start: Scripts will attempt to start PostgreSQL manually
   - Nvidia/CUDA installation fails: Use the host's GPU drivers with volume mounts instead of installing in the container
   - No interactive input available: Use environment variables to control installation flow:
     ```bash
     export AUTO_MODE=1
     export AUTO_SKIP_NVIDIA=1
     export AUTO_SKIP_CUDA=1
     export AUTO_SKIP_INTERACTIVE=1
     ```

## Security Notes

- The deployment script generates random passwords and API keys
- Make sure to keep the GPU Server API key secure
- For production environments, always use HTTPS (SSL)
- Consider setting up a firewall (UFW) to restrict access to your server

## Support

If you encounter issues with the deployment scripts, please open an issue on the repository.