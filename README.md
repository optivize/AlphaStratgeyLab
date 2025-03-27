# AlphaStrategyLab

AlphaStrategyLab is a cutting-edge AI-powered platform for stock trading strategy development, enabling users to create, test, and refine trading approaches through natural language and intelligent computational analysis.

## Key Features

- **AI-Assisted Strategy Development**: Create trading strategies using natural language
- **GPU-Accelerated Backtesting**: Test strategies against historical market data with high performance
- **Multi-User Support**: Secure authentication and account management
- **Interactive Dashboard**: Visualize backtest results with detailed metrics
- **Watchlist Management**: Track stocks of interest
- **Multiple Strategy Templates**: Choose from pre-built strategy templates

## Tech Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: React, TypeScript (Template views included)
- **AI Integration**: LLM-powered strategy creation
- **Computation**: CUDA-accelerated backtesting engine

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL database
- Together AI API key (optional, for AI features)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-username/alpha-strategy-lab.git
   cd alpha-strategy-lab
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export DATABASE_URL=postgresql://user:password@localhost/backtest
   export SESSION_SECRET=your-secret-key
   export TOGETHER_KEY=your-together-ai-key (optional)
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Run the application:
   ```
   python main.py
   ```

6. Open your browser to http://localhost:5000

## API Reference

The platform provides a comprehensive REST API:

- `/api/v1/backtest`: Submit and retrieve backtest jobs
- `/api/v1/strategies`: Access strategy templates
- `/api/v1/watchlist`: Manage stock watchlist
- `/api/v1/ai/backtest`: Generate backtests using AI

## License

MIT