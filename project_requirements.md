# Project Requirements Document for Algorithmic Trading and Management App

## Project Overview
The algorithmic trading and management application is a Python-based system designed to automate trading operations on MetaTrader 5 (MT5) and manage all aspects of the trading process. It will execute predefined strategies, manage open positions, collect and store market data, and analyze trading performance—all with minimal manual intervention. The initial version will integrate with MT5 for trade execution and data, using TimescaleDB for storing time-series data. Future expansions are planned to support additional broker APIs beyond MT5. The app is intended to run both on a cloud-based server (for 24/7 operation) and on a personal computer, ensuring flexibility in deployment environments.

## Development Environment
- Python 3.13.2
- Virtual Environment (venv)
- Windows 10 Operating System

## Setup Instructions

### 1. Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Git Bash:
source venv/Scripts/activate

# Deactivate when done
deactivate
```

### 2. Dependencies
All project dependencies are managed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

Current dependencies:
- pip >= 25.0.1
- setuptools >= 69.0.3
- wheel >= 0.42.0

## Development Guidelines
1. Always activate the virtual environment before working on the project
2. Add new dependencies to requirements.txt
3. Keep code organized and well-documented
4. Follow PEP 8 style guidelines for Python code

## Testing
- Run tests before committing changes
- Ensure all new features have corresponding tests
- Current test command: `python main.py`

## Notes
- Remember to update this document as the project evolves
- Document any important architectural decisions
- Keep track of any external service dependencies 


## Project Structure
HaruTrader/
├── README.md
├── requirements.txt
├── setup.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── algotrader/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py           # Application settings and configuration
│   │   └── credentials.py        # Secure credential management (encrypted)
│   │
│   ├── controller/
│   │   ├── __init__.py
│   │   ├── data_acquisition.py   # Market, fundamental, sentiment data collection
│   │   ├── notification.py       # Telegram alerts and notifications
│   │   └── persistence.py        # TimescaleDB storage operations
│   │
│   ├── trader/
│   │   ├── __init__.py
│   │   ├── order.py              # Order placement and management
│   │   ├── position.py           # Position management
│   │   ├── risk.py               # Risk calculation and lot sizing
│   │   └── history.py            # Trade history retrieval
│   │
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base.py               # Base strategy class
│   │   ├── indicators.py         # Technical indicators implementation
│   │   ├── screener.py           # Symbol screening functionality
│   │   ├── risk_management.py    # SL/TP calculation, position sizing
│   │   └── strategies/           # Individual strategy implementations
│   │       ├── __init__.py
│   │       ├── trend_following.py
│   │       ├── mean_reversion.py
│   │       └── breakout.py
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py             # Event-based backtesting engine
│   │   ├── optimizer.py          # Strategy parameter optimization
│   │   ├── walk_forward.py       # Walk-forward analysis
│   │   ├── monte_carlo.py        # Monte Carlo simulations
│   │   └── cross_validation.py   # Combinatorial Purged Cross Validation
│   │
│   ├── live_trading/
│   │   ├── __init__.py
│   │   ├── executor.py           # Real-time execution loop
│   │   ├── monitor.py            # Performance tracking
│   │   └── recovery.py           # Failover and recovery mechanisms
│   │
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── app.py                # Flask/FastAPI application
│   │   ├── auth.py               # OAuth2 authentication
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── account.py        # Account endpoints
│   │   │   ├── performance.py    # Performance metrics endpoints
│   │   │   └── strategy.py       # Strategy management endpoints
│   │   ├── static/               # CSS, JS, images
│   │   └── templates/            # HTML templates
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── market_data.py        # Market data models
│   │   ├── trade.py              # Trade and position models
│   │   ├── account.py            # Account and performance models
│   │   └── user.py               # User and authentication models
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── mt5/
│   │   │   ├── __init__.py
│   │   │   ├── client.py         # MT5 connection and API wrapper
│   │   │   └── data.py           # MT5 data retrieval
│   │   ├── telegram/
│   │   │   ├── __init__.py
│   │   │   └── bot.py            # Telegram bot implementation
│   │   ├── timescaledb/
│   │   │   ├── __init__.py
│   │   │   └── client.py         # TimescaleDB connection and queries
│   │   └── external_data/
│   │       ├── __init__.py
│   │       ├── investpy.py       # Investpy integration
│   │       ├── forex_factory.py  # Forex Factory integration
│   │       └── social_media.py   # Twitter, StockTwits integration
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Logging configuration
│       ├── security.py           # Encryption and security utilities
│       ├── validation.py         # Input validation
│       └── helpers.py            # Miscellaneous helper functions
│
├── scripts/
│   ├── setup_database.py         # Database initialization
│   ├── generate_reports.py       # Report generation scripts
│   └── deploy.py                 # Deployment automation
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── unit/                     # Unit tests for each module
│   │   ├── __init__.py
│   │   ├── test_controller.py
│   │   ├── test_trader.py
│   │   └── ...
│   ├── integration/              # Integration tests
│   │   ├── __init__.py
│   │   ├── test_mt5_integration.py
│   │   └── ...
│   └── fixtures/                 # Test data fixtures
│       ├── market_data.json
│       └── ...
│
└── docs/
    ├── architecture.md           # Architecture documentation
    ├── api.md                    # API documentation
    ├── deployment.md             # Deployment guide
    └── user_guide.md             # User guide

## User Roles
- **Admin**: Manages system configurations, user accounts, and overall strategy deployment.
- **Trader**: Executes trades, modifies orders, and analyzes performance.
- **Observer**: Has read-only access to trade data, reports, and analytics.

## Security & Authentication
- **User Authentication**: OAuth2 will be implemented for secure user logins and session management.
- **API Key Management**: External API keys (e.g., Telegram, Twitter) will be stored securely (encrypted or in secure environment variables).
- **MT5 Credentials**: Login details for MT5 will be encrypted at rest and only decrypted at runtime.
- **Secure Communication**: All network communications (broker, APIs, database) will use secure protocols (HTTPS/SSL/TLS).
- **Access Control & Audit Logging**: User roles will have strict permission sets; all critical operations and authentication events will be logged for audit purposes.

## Functional Requirements

### 1. Controller Module
**Overview:**  
The Controller module serves as the central coordinator for data acquisition, notifications, and data persistence.

- **Data Acquisition:**  
  - **Market Price Data:** Retrieve real-time market price data from MT5, including OHLCV data and tick data.
  - **Fundamental Data:** Collect economic indicators, news releases, and Fed meetings data via Investpy and Forex Factory.
  - **Sentiment Data:** Acquire sentiment information from StockTwits, Twitter, and other social media feeds.

- **Alerts & Notifications:**  
  - Use a Telegram Bot to send alerts to configured channels based on a channel ID.
  - Implement a Markdown composer to format messages in a readable style.

- **Cloud DB Storage (TimescaleDB):**  
  - Persist historical bars, account history, and closed positions.
  - Store live trade monitor data such as floating PnL, floating equity, and the number of open positions.

- **Logger:**  
  - Use Python’s built-in logging module to track important events and exceptions (e.g., MT5 connection failures, trade closures).

### 2. Trader Module
**Overview:**  
Handles order execution, position management, and retrieval of trading history.

- **Order Placement:**  
  - Calculate appropriate lot sizes based on specified risk parameters.
  - Place different types of orders (Market BUY/SELL, Limit BUY/SELL, Stop Limit BUY/SELL).
  - Report success or failure of order placement via Telegram.

- **Order/Position Management:**  
  - Retrieve open positions and pending orders.
  - Modify or cancel pending orders and update SL/TP for open positions.
  - Close open positions and report the results via Telegram.

- **Order Book Access:**  
  - Fetch closed positions and deal history from MT5 and return data as a Pandas DataFrame.
  - Display live floating equity, PnL, and generate a time-series balance curve.

### 3. Strategy Module
**Overview:**  
This module forms the trading brain, generating signals and managing risk. It now also includes a **Screener** component.

- **Signal Generation:**  
  - Utilize technical indicators (via libraries like TA-Lib) to generate BUY/SELL signals.
  - Implement logic for risk management (e.g., determining SL, TP, and position sizing).

- **Screener:**  
  - **Function:** The screener will continuously scan through a predefined list of symbols and compare each against the criteria of the available strategies.
  - **Process:**  
    - Retrieve the list of available strategies along with their conditions.
    - For each symbol, evaluate if current market conditions match any strategy’s entry criteria.
    - Display (or log) symbols that satisfy one or more strategy conditions.
  - **Output:**  
    - A dynamically updated view (which can be integrated into the dashboard) that highlights symbols matching strategy criteria.
    - This component aids traders in identifying new opportunities across a broad market.
    
- **Risk & Position Management:**  
  - Define and enforce risk rules (e.g., percentage of capital risked per trade).
  - Automatically set SL and TP based on strategy guidelines.
  - Enable adjustments to positions (e.g., trailing stops, break-even moves).

### 4. Account Monitoring & Performance Analytics Dashboard Module
**Overview:**  
Provides visualization and monitoring tools for assessing strategy performance and account status.

- **Performance Metrics:**  
  - Track PnL, ROI, Sharpe ratio, drawdowns, win rate, and other key trading metrics.
  
- **Live Monitoring:**  
  - Real-time display of account balance, equity, floating PnL, and open positions.

- **Web-Based Dashboard:**  
  - Build using Flask/FastAPI to provide an intuitive interface for Admin, Trader, and Observer roles.
  - Display charts (e.g., equity curve, trade history, and open positions table).
  
- **Reporting:**  
  - Generate periodic performance reports (daily, weekly) and send via email or Telegram.

### 5. Backtest Module
**Overview:**  
Allows simulation and optimization of trading strategies using historical data.

- **Event-Based Backtesting Engine:**  
  - Simulate market conditions and strategy performance using historical data.
  
- **Strategy Optimization:**  
  - Automate running parameter optimizations across a grid of possible strategy values.
  
- **Walk-Forward Optimization:**  
  - Implement walk-forward analysis to test strategy robustness on out-of-sample data.
  
- **Combinatorial Purged Cross Validation:**  
  - Use CPCV to avoid lookahead bias and improve the robustness of backtest results.
  
- **Monte Carlo Simulations:**  
  - Run Monte Carlo simulations on trade sequences to assess the probability of extreme outcomes.

### 6. Live Trading Module
**Overview:**  
Orchestrates real-time trade execution and system resilience during live operations.

- **Real-Time Execution Loop:**  
  - Continuously process market data and trigger strategy signals.
  - Execute trades promptly to minimize slippage.

- **Concurrent Task Handling:**  
  - Utilize threading or asynchronous programming to manage data feeds, order placement, and notifications concurrently.

- **Performance Tracking:**  
  - Continuously update live metrics and monitor trade performance.

- **Failover & Recovery:**  
  - Implement reconnection logic for MT5 outages.
  - Persist critical state data to resume operations seamlessly on restart.

- **Scalability & Notifications:**  
  - Scale to multiple symbols or strategies.
  - Provide status updates and alerts via Telegram.

## Technology Stack
- **Programming Language:** Python
- **Trading Platform:** MetaTrader 5 (MT5)
- **Database:** TimescaleDB (PostgreSQL with time-series capabilities)
- **Frameworks & Libraries:**
  - **Data Processing:** Pandas, NumPy
  - **Technical Analysis:** TA-Lib, Backtrader (for backtesting)
  - **Machine Learning (Optional):** TensorFlow, Scikit-Learn
  - **API & Web Services:** Flask or FastAPI for dashboard and API endpoints
  - **Notifications:** Telegram API
  - **Logging:** Python logging module; Grafana for advanced monitoring
  - **Other Tools:** Docker (for containerization), Tinker (for UI components, if needed)

## Execution Environment
- **Deployment:**  
  - Designed for deployment on both cloud-based servers and personal computers.
  - Must ensure the MT5 terminal is installed and accessible on the host system.
- **Containerization:**  
  - Use Docker for encapsulating the Python environment and dependencies (with caveats for MT5 integration on Windows).
- **Scalability:**  
  - The system will be built to support increased data volume, more symbols, and multiple strategies in the future.

## API Integrations and External Services
- **MT5 API:**  
  - Connect via the official MetaTrader5 Python package for trade execution and data retrieval.
- **TimescaleDB:**  
  - Store and query time-series data using TimescaleDB, interfaced through psycopg2 or SQLAlchemy.
- **Investpy & Forex Factory:**  
  - Retrieve economic indicators, news, and fundamental data.
- **Social Media Sentiment:**  
  - Integrate with Twitter and StockTwits to gauge market sentiment.
- **Telegram Bot:**  
  - Send formatted alerts and notifications via the Telegram Bot API.
- **Future Broker Integrations:**  
  - Architect the system to support additional broker APIs with minimal modifications to core modules.

## Architecture Overview
The application is organized into modular layers, ensuring separation of concerns and ease of future enhancements:

1. **Integration Layer:**  
   - Connects to external systems such as MT5, external data APIs, and TimescaleDB.
2. **Core Logic Layer:**  
   - **Controller:** Orchestrates data acquisition, notifications, and database storage.
   - **Strategy:** Generates trading signals based on technical and fundamental data, and now includes a screener for symbol scanning.
   - **Trader:** Manages order placement, modification, and trade history.
3. **Data Storage Layer:**  
   - Persists all historical data (market, trade, account performance) using TimescaleDB.
4. **Presentation Layer:**  
   - Provides a web-based dashboard for analytics and real-time monitoring, along with Telegram notifications.

## Deployment Considerations
- **Operating System & Dependencies:**  
  - MT5 is Windows-based; deployment should consider Windows environments or compatible workarounds (e.g., Wine on Linux).
- **Python Environment:**  
  - Use virtual environments or Docker containers to manage dependencies.
- **Configuration Management:**  
  - Externalize sensitive credentials (MT5, API keys) in secure config files or environment variables.
- **Service Management:**  
  - Ensure the bot auto-starts on reboot using system-specific service managers (systemd, Task Scheduler).
- **Networking & Security:**  
  - Secure connections for MT5, TimescaleDB, and external APIs.
- **Database Deployment:**  
  - Use local or managed TimescaleDB deployments with regular backups.
- **Monitoring & Logging:**  
  - Integrate with monitoring systems (Grafana, CloudWatch) to track performance and system health.
- **Web Dashboard:**  
  - Deploy the Flask/FastAPI-based dashboard on an accessible server endpoint with proper HTTPS and OAuth configurations.

---

This document outlines both functional and non-functional requirements, detailed module responsibilities, integration details, and deployment considerations for your trading and management app. The added screener under the Strategy Module will enable proactive symbol scanning and provide valuable signals for potential trading opportunities.

*End of Document*
