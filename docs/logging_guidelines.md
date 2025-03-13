# Logging Guidelines for HaruTrader

This document outlines the logging standards and best practices for the HaruTrader algorithmic trading application. Following these guidelines ensures consistent, useful logs across the entire codebase.

## Basic Setup

Every module should set up logging as follows:

```python
from app.utils import get_logger

# Create a module-specific logger
logger = get_logger(__name__)
```

## Log Levels

Use the appropriate log level for each message:

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed information for debugging purposes | `logger.debug(f"Processing trade data: {data}")` |
| INFO | Confirmation that things are working as expected | `logger.info("Trading session started successfully")` |
| WARNING | Indication that something unexpected happened, but the application is still working | `logger.warning("API rate limit approaching, throttling requests")` |
| ERROR | Due to a more serious problem, the application couldn't perform a function | `logger.error("Failed to execute order due to insufficient funds")` |
| CRITICAL | A serious error indicating the application may be unable to continue running | `logger.critical("Database connection lost, cannot continue trading")` |

## Logging Best Practices

### 1. Include Context

Always include relevant context in log messages:

```python
# Good
logger.info(f"Order executed: symbol={symbol}, price=${price}, quantity={quantity}")

# Not as useful
logger.info("Order executed")
```

### 2. Log the Start and End of Important Operations

```python
def process_market_data(symbol):
    logger.info(f"Starting market data processing for {symbol}")
    try:
        # Processing logic here
        logger.info(f"Completed market data processing for {symbol}")
    except Exception as e:
        logger.error(f"Failed to process market data for {symbol}", exc_info=True)
```

### 3. Log All Exceptions

Always log exceptions with traceback information:

```python
try:
    # Some code that might raise an exception
except Exception as e:
    # Option 1: Using logger.exception (automatically includes traceback)
    logger.exception(f"Error occurred while processing {item}")
    
    # Option 2: Using logger.error with exc_info=True
    logger.error(f"Error occurred while processing {item}", exc_info=True)
```

### 4. Use Structured Logging When Appropriate

For logs that will be parsed by automated systems, use structured formats:

```python
logger.info(
    "Trade executed", 
    extra={
        "symbol": "AAPL", 
        "price": 150.25, 
        "quantity": 100,
        "side": "BUY",
        "timestamp": "2025-03-11T12:34:56Z"
    }
)
```

### 5. Avoid Excessive Logging

Avoid logging in tight loops or high-frequency operations without rate limiting:

```python
# Bad - will generate too many log entries
for tick in price_ticks:  # Could be thousands per second
    logger.debug(f"Processing tick: {tick}")

# Better
if len(price_ticks) > 0:
    logger.debug(f"Processing {len(price_ticks)} price ticks")
    # Process ticks
    logger.debug(f"Completed processing price ticks, last price: {price_ticks[-1]}")
```

### 6. Log Security-Sensitive Information Carefully

Never log sensitive information such as:
- API keys or passwords
- Full account details
- Personal identifiable information

```python
# Bad
logger.info(f"Connecting to API with key: {api_key}")

# Good
logger.info(f"Connecting to API with key: {'*' * 8}{api_key[-4:]}")
```

### 7. Include Timestamps and Correlation IDs

For distributed systems, include correlation IDs to track requests across services:

```python
def process_order(order_id, correlation_id=None):
    logger.info(f"Processing order {order_id}", extra={"correlation_id": correlation_id})
    # Processing logic
```

## Module-Specific Logging Guidelines

### Data Acquisition Module

- Log data source connections and disconnections
- Log data retrieval statistics (number of records, time taken)
- Log any data quality issues or missing data

### Strategy Module

- Log strategy initialization parameters
- Log signal generation with reasoning
- Log backtest results and performance metrics

### Execution Module

- Log all order submissions, modifications, and cancellations
- Log order fills and execution details
- Log slippage and execution quality metrics

### Risk Management Module

- Log risk checks and their results
- Log position and exposure calculations
- Log risk limit breaches

## Log File Management

- Log files are stored in the `logs/` directory
- Log files are rotated when they reach 10MB in size
- A maximum of 5 backup files are kept for each log file

## Troubleshooting

If logs are not appearing as expected:

1. Check the log level setting in the environment variables or `.env` file
2. Ensure the logs directory exists and is writable
3. Verify that the logger is properly initialized in the module

## Example Implementation

```python
from app.utils import get_logger

logger = get_logger(__name__)

class OrderExecutor:
    def __init__(self, broker_client):
        self.broker = broker_client
        logger.info(f"OrderExecutor initialized with broker: {broker_client.name}")
        
    def submit_order(self, symbol, side, quantity, order_type="market", price=None):
        logger.info(
            f"Submitting {order_type} order: {side} {quantity} {symbol} "
            f"{'@ $' + str(price) if price else ''}"
        )
        
        try:
            order_id = self.broker.place_order(symbol, side, quantity, order_type, price)
            logger.info(f"Order submitted successfully, order_id: {order_id}")
            return order_id
        except Exception as e:
            logger.error(
                f"Failed to submit order for {symbol}: {str(e)}", 
                exc_info=True
            )
            return None
``` 