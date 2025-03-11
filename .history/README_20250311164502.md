# HaruTrader

An algorithmic trading and management application designed to automate trading operations on MetaTrader 5 (MT5) and manage all aspects of the trading process.

## Features

- Automated trading strategy execution
- Real-time market data collection and analysis
- Position and risk management
- Performance analytics and reporting
- Web-based dashboard for monitoring
- Telegram notifications
- Backtesting and strategy optimization

## Requirements

- Python 3.13.2
- MetaTrader 5 (MT5) terminal
- TimescaleDB
- Windows 10 Operating System

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HaruTrader.git
cd HaruTrader
```

2. Create and activate virtual environment:
```bash
python -m venv venv

# On Windows PowerShell:
.\venv\Scripts\activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Git Bash:
source venv/Scripts/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

5. Initialize the database:
```bash
python scripts/setup_database.py
```

## Usage

TODO: Add usage instructions

## Development

TODO: Add development guidelines

## Testing

TODO: Add testing instructions

## Documentation

Detailed documentation can be found in the `docs` directory:

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [User Guide](docs/user_guide.md)

## License

TODO: Add license information 