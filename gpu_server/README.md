# AlphaStrategyLab GPU Backtesting Server

This component provides GPU-accelerated backtesting services for the AlphaStrategyLab platform. It is designed to be deployed on a separate server with GPU capability to handle computationally intensive backtesting operations.

## Overview

The GPU Backtesting Server is a self-contained component that communicates with the main AlphaStrategyLab application through RESTful APIs. It provides the following capabilities:

- High-performance backtesting of trading strategies using GPU acceleration
- Parallel processing of multiple backtest jobs
- CUDA-accelerated strategy execution
- Custom market data handling
- Comprehensive performance metrics calculation

## Architecture

The server consists of the following main components:

1. **Flask Web Server**: Provides RESTful API endpoints for submitting backtest jobs, retrieving results, and managing data sources.

2. **GPU Engine**: Core engine that executes trading strategies on GPU using CUDA kernels. Falls back to CPU execution if GPU is not available.

3. **Data Service**: Manages market data retrieval, caching, and custom data uploads.

4. **Strategy Library**: Collection of trading strategy templates that can be executed on GPU.

## Requirements

- CUDA-capable NVIDIA GPU (recommended)
- Python 3.8+
- Flask
- SQLAlchemy
- PyCUDA
- CuPy
- pandas
- numpy
- PostgreSQL database

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install CUDA dependencies (on the GPU server):
   ```
   pip install pycuda cupy-cuda11x
   ```
4. Configure the server by setting environment variables (see Configuration section)
5. Start the server:
   ```
   python app.py
   ```

## Configuration

The server can be configured using environment variables:

- `GPU_SERVER_HOST`: Hostname to bind the server (default: 0.0.0.0)
- `GPU_SERVER_PORT`: Port to listen on (default: 5050)
- `GPU_SERVER_DEBUG`: Enable debug mode (default: True)
- `DATABASE_URL`: PostgreSQL database connection string
- `GPU_DEVICE`: GPU device ID to use (default: 0)
- `MAX_CONCURRENT_JOBS`: Maximum number of concurrent backtest jobs (default: 10)
- `GPU_MEMORY_LIMIT`: Maximum fraction of GPU memory to use (default: 0.9)
- `TIINGO_API_KEY`: API key for Tiingo market data (optional)
- `API_KEY_REQUIRED`: Whether to require API key authentication (default: False)
- `GPU_SERVER_API_KEY`: API key for server authentication (required if API_KEY_REQUIRED is True)

## API Endpoints

### Authentication

If `API_KEY_REQUIRED` is set to `True`, all API requests must include the `X-API-Key` header with the configured API key.

### Backtest Operations

- `POST /backtest`: Submit a new backtest job
- `GET /backtest/<job_id>`: Get status and results of a backtest job
- `GET /strategies`: List available strategy templates
- `GET /gpu/status`: Get GPU status information

### Data Operations

- `GET /data/sources`: List available data sources
- `GET /data/symbols`: List available symbols for a data source
- `POST /data/upload`: Upload custom market data

## Integration with AlphaStrategyLab

The main AlphaStrategyLab application communicates with this GPU server using RESTful API calls. Integration steps:

1. Configure the main application with the GPU server URL and API key
2. Add API client in the main application to forward backtest requests to the GPU server
3. Set up scheduled tasks to retrieve completed backtest results

## Development and Deployment

### Development

For development and testing on systems without GPU:
- The server will automatically fall back to CPU execution when CUDA is not available
- Install the Python dependencies without CUDA extensions:
  ```
  pip install -r requirements-dev.txt
  ```

### Deployment

For production deployment on a GPU server:
1. Clone the repository on a server with GPU capability
2. Install all dependencies including CUDA extensions
3. Configure the server with appropriate environment variables
4. Set up a reverse proxy (e.g., Nginx) to handle HTTPS and security
5. Use a process manager (e.g., Supervisor) to keep the server running

## Security Considerations

- Enable API key authentication in production
- Deploy behind a secure reverse proxy
- Restrict network access to trusted IPs
- Set up HTTPS with proper certificates
- Monitor and restrict resource usage

## License

Copyright © 2024 AlphaStrategyLab