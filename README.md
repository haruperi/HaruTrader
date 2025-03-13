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


# Project TODOs

## Phase 1: Project Setup and Core Infrastructure
[ ] Initial Project Setup
  - [ ] Create virtual environment and install Python 3.13.2
  - [ ] Set up requirements.txt with initial dependencies
  - [ ] Create .env.example with required environment variables
  - [ ] Set up project structure according to architecture diagram
  - [ ] Initialize git repository and set up .gitignore

[ ] Core Infrastructure Setup
  - [ ] Set up logging configuration in app/utils/logger.py
  - [ ] Implement timeutils.py for timezone handling
  - [ ] Create validation.py for input validation
  - [ ] Set up TimescaleDB connection and models
  - [ ] Configure OAuth2 authentication system

## Phase 2: MT5 Integration and Core Trading Components
[ ] MT5 Integration (app/core/mt5_data.py)
  - [ ] Implement MT5 client connection
  - [ ] Set up market data operations
  - [ ] Create data retrieval functions
  - [ ] Implement error handling and reconnection logic

[ ] Trader Module (app/trader/)
  - [ ] Implement order.py for order placement
  - [ ] Create position.py for position management
  - [ ] Develop risk.py for risk calculations
  - [ ] Set up history.py for trade history retrieval

[ ] Core Notification System (app/core/notification.py)
  - [ ] Set up Telegram bot integration
  - [ ] Implement message formatting
  - [ ] Create notification queue system
  - [ ] Add error reporting functionality

## Phase 3: Strategy Development
[ ] Base Strategy Framework (app/strategy/)
  - [ ] Create base.py with strategy interface
  - [ ] Implement indicators.py with technical indicators
  - [ ] Set up risk_management.py
  - [ ] Develop screener.py for symbol scanning

[ ] Initial Strategy Implementations
  - [ ] Create trend_following.py
  - [ ] Implement mean_reversion.py
  - [ ] Develop breakout.py
  - [ ] Add strategy parameter management

## Phase 4: Backtesting System
[ ] Backtesting Engine (app/backtest/)
  - [ ] Create event-based engine.py
  - [ ] Implement optimizer.py
  - [ ] Set up walk_forward.py
  - [ ] Add monte_carlo.py simulation
  - [ ] Implement cross_validation.py

## Phase 5: Live Trading System
[ ] Live Trading Module (app/live_trading/)
  - [ ] Develop executor.py for real-time execution
  - [ ] Create monitor.py for performance tracking
  - [ ] Implement recovery.py for failover
  - [ ] Add concurrent task handling

## Phase 6: Dashboard Development
[ ] Web Dashboard (app/dashboard/)
  - [ ] Set up Flask/FastAPI application
  - [ ] Create authentication system
  - [ ] Implement account endpoints
  - [ ] Add performance metrics endpoints
  - [ ] Develop strategy management endpoints
  - [ ] Create HTML templates and static assets

## Phase 7: Testing and Documentation
[ ] Testing Infrastructure
  - [ ] Set up pytest configuration
  - [ ] Create unit tests for each module
  - [ ] Implement integration tests
  - [ ] Add end-to-end tests
  - [ ] Create test fixtures and utilities

[ ] Documentation
  - [ ] Write architecture.md
  - [ ] Create API documentation
  - [ ] Develop deployment guide
  - [ ] Write user guide
  - [ ] Add inline code documentation

## Phase 8: Deployment and Monitoring
[ ] Deployment Setup
  - [ ] Create Docker configuration
  - [ ] Set up CI/CD pipeline
  - [ ] Configure production environment
  - [ ] Implement backup system

[ ] Monitoring System
  - [ ] Set up Grafana dashboards
  - [ ] Implement system health checks
  - [ ] Create performance monitoring
  - [ ] Add alert system

## Phase 9: Security and Optimization
[ ] Security Implementation
  - [ ] Implement API key encryption
  - [ ] Set up secure communication
  - [ ] Add audit logging
  - [ ] Implement access control

[ ] Performance Optimization
  - [ ] Optimize database queries
  - [ ] Improve concurrent operations
  - [ ] Enhance error handling
  - [ ] Add caching where appropriate

## Phase 10: Additional Features and Integration
[ ] External Data Integration
  - [ ] Add Investpy integration
  - [ ] Implement Forex Factory data collection
  - [ ] Set up social media sentiment analysis
  - [ ] Create news feed integration

[ ] Additional Features
  - [ ] Implement portfolio management
  - [ ] Add risk reporting
  - [ ] Create performance analytics
  - [ ] Develop custom indicators