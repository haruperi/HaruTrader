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
python -m app.utils.setup_database
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

## Strategies

### Mean Reversion Swingline Strategy

The Mean Reversion Swingline strategy is a trading strategy that combines the Swingline indicator with RSI to identify potential reversal points in price action. It enters trades when:

- For long positions: RSI is oversold and Swingline changes from down to up
- For short positions: RSI is overbought and Swingline changes from up to down

The strategy uses ATR for position sizing and stop loss/take profit calculation.

#### Key Components

1. **Swingline Indicator**: Tracks the direction of price swings (up or down)
2. **RSI (Relative Strength Index)**: Identifies overbought and oversold conditions
3. **ATR (Average True Range)**: Measures volatility for stop loss and take profit calculation

#### Parameters

- `rsi_period`: Period for RSI calculation (default: 14)
- `rsi_overbought`: RSI level considered overbought (default: 70)
- `rsi_oversold`: RSI level considered oversold (default: 30)
- `atr_period`: Period for ATR calculation (default: 14)
- `sl_atr_multiplier`: Multiplier for stop loss calculation (default: 1.5)
- `tp_atr_multiplier`: Multiplier for take profit calculation (default: 2.0)

#### Testing and Optimization

The strategy includes tests for testing and optimization:

- `tests/test_mean_reversion_swingline.py`: Tests the strategy with specific parameters
- `tests/test_optimize_mean_reversion_swingline.py`: Finds optimal parameter combinations

#### Example Usage

```bash
# Test the strategy with default parameters
python -m tests.test_mean_reversion_swingline --use-sample --plot

# Optimize the strategy
python -m tests.test_optimize_mean_reversion_swingline --use-sample --plot-best --save-results

# Run live trading (demo mode)
python -m app.live_trading.mean_reversion_swingline --symbol EURUSD --timeframe H1 --demo
```

#### Live Trading

The strategy includes a live trading script (`live_mean_reversion_swingline.py`) that can be used to run the strategy in real-time. The script:

1. Fetches market data at regular intervals
2. Generates trading signals based on the strategy rules
3. Calculates position size based on risk management parameters
4. Executes trades when signals are generated

Key parameters for live trading:

- `--symbol`: Trading symbol (default: EURUSD)
- `--timeframe`: Trading timeframe (default: H1)
- `--risk-percent`: Risk percent per trade (default: 1.0)
- `--update-interval`: Update interval in seconds (default: 60)
- `--demo`: Run in demo mode (no real trades)

Always test the strategy thoroughly in demo mode before using it with real money. 