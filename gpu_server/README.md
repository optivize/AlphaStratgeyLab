# AlphaStrategyLab GPU Server

A GPU-accelerated backtesting engine for AlphaStrategyLab, designed to run on a remote server with NVIDIA GPU capabilities.

## Overview

This component provides high-performance backtesting services for trading strategies using GPU acceleration. It's designed to be deployed on a separate server with GPU capabilities, independent from the main AlphaStrategyLab application.

## Features

- GPU-accelerated strategy backtesting
- RESTful API for job submission and results retrieval
- Support for multiple strategy types
- Parallel job processing
- Database storage for backtest results
- Performance metrics calculation

## Architecture

The GPU Server consists of:
- Flask-based REST API
- GPU-accelerated computation engine
- Job queue and worker system
- Database integration
- Monitoring and maintenance tools

## Deployment Instructions

### Preparation

1. **Download the code**: First, download all the deployment scripts from your project:
   - Navigate to the `gpu_server/deploy_scripts` folder in your project
   - Download all the files to your local computer

2. **Transfer files to your remote server**: Use SCP, SFTP, or any file transfer method:
   ```bash
   scp -r gpu_server/deploy_scripts/* username@your-server-ip:~/deploy_scripts/
   ```

### Deployment Options

#### Option 1: Using the Interactive Menu (Recommended)

1. **SSH into your server**:
   ```bash
   ssh username@your-server-ip
   ```

2. **Navigate to the deployment directory**:
   ```bash
   cd ~/deploy_scripts
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x *.sh
   ./make_executable.sh
   ```

4. **Run the interactive menu**:
   ```bash
   sudo ./menu.sh
   ```

5. **Follow the menu prompts**:
   - For a new installation, select "Full automated deployment" 
   - To update an existing installation, select "Service Management Menu" → "Update application code"
   - For step-by-step control, select "Step-by-step deployment"
   
   > **Note:** The deployment scripts will automatically use the code you've transferred to the server. You don't need to provide a GitHub URL as the scripts will copy the code from the correct location.

#### Option 2: Using the Automated Deployment Script

1. **SSH into your server**:
   ```bash
   ssh username@your-server-ip
   ```

2. **Navigate to the deployment directory**:
   ```bash
   cd ~/deploy_scripts
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x *.sh
   ```

4. **Run the deployment script**:
   ```bash
   sudo ./deploy.sh
   ```

5. **Follow the prompts** during installation.

   > **Note:** The deployment scripts will automatically use the code you've transferred to the server. You don't need to provide a GitHub URL as the scripts will copy the code from the correct location.

#### Option 2.5: Fully Automated Non-Interactive Deployment (Container or CI/CD)

For containerized environments or CI/CD pipelines, you can use the fully automated mode:

1. **Set environment variables to enable automatic mode**:
   ```bash
   export AUTO_MODE=1  # Enable fully automated deployment
   export AUTO_SKIP_NVIDIA=1  # Skip NVIDIA driver installation prompts
   export AUTO_SKIP_CUDA=1  # Skip CUDA installation prompts
   ```

2. **Run the deployment script without any interactive prompts**:
   ```bash
   sudo -E ./deploy.sh  # The -E flag preserves environment variables
   ```

This mode automatically detects container environments and will behave appropriately:
- Skips all interactive prompts
- Preserves existing NVIDIA and CUDA installations
- Automatically configures using sensible defaults
- Uses alternative service management in non-systemd environmentsn.

#### Option 3: Step-by-Step Manual Deployment

If you prefer to run each step manually or just update specific components:

1. **Make scripts executable**:
   ```bash
   chmod +x *.sh
   ```

2. **Run individual scripts in sequence**:
   ```bash
   sudo ./01-system-setup.sh     # System dependencies
   sudo ./02-database-setup.sh   # Database configuration
   sudo ./03-app-deploy.sh       # App code deployment
   sudo ./04-supervisor-setup.sh # Process management
   sudo ./05-nginx-setup.sh      # Web server/proxy
   sudo ./06-monitoring-setup.sh # Monitoring tools
   ```
   
   > **Note:** The deployment scripts will automatically use the code you've transferred to the server. You don't need to provide a GitHub URL as the scripts will copy the code from the correct location.

### Post-Deployment

1. **Verify the service is running**:
   ```bash
   sudo supervisorctl status alphastrategy-gpu
   ```

2. **Check logs for any errors**:
   ```bash
   sudo tail -f /opt/alphastrategylab/logs/alphastrategy-gpu.log
   ```

3. **Access the API**: The GPU server should be available at:
   ```
   http://your-server-ip
   ```
   or if you configured SSL:
   ```
   https://your-domain.com
   ```

4. **Note your API key**: Make sure to save the API key shown at the end of the deployment process for authenticating with the GPU server from your main application.

### Updating an Existing Deployment

If you need to update an existing deployment with new code:

1. **Use the menu**:
   ```bash
   sudo ./menu.sh
   ```
   Then select "Manage deployed service" → "Update application code"

2. **Or run the update script directly**:
   ```bash
   sudo /opt/alphastrategylab/config/update-app.sh
   ```

## System Requirements

- Ubuntu 20.04 LTS or newer
- NVIDIA GPU (recommended: NVIDIA T4, V100, A100, or similar)
- CUDA 11.0+
- 8+ CPU cores
- 16+ GB RAM
- 100+ GB SSD storage
- PostgreSQL 12+

## API Reference

### Authentication

All API requests require an API key to be included in the header:

```
X-API-Key: your-api-key-here
```

### Endpoints

- `GET /health` - Health check endpoint
- `POST /backtest` - Submit a new backtest job
- `GET /backtest/{job_id}` - Get status of a backtest job
- `GET /data-sources` - List available data sources
- `GET /symbols` - List available symbols
- `POST /data/upload` - Upload custom market data
- `GET /gpu/status` - Get GPU status information
- `GET /strategies` - List available strategies

## Development

For local development without GPU:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `.env.example`)
4. Run the server: `python run.py`

## License

Proprietary - All rights reserved

## Support

For support, please contact the AlphaStrategyLab team.