# Dependency Management Strategy

This document outlines the strategy for managing dependencies in the HaruTrader application to avoid circular imports and ensure a clean, maintainable architecture.

## Module Hierarchy

The application follows a hierarchical structure where lower-level modules should not import from higher-level modules:

1. **Core Utilities** (`app.utils`): Base utilities that don't depend on other application modules
2. **Configuration** (`app.config`): Application settings and configuration
3. **Models** (`app.models`): Data models and schemas
4. **Integrations** (`app.integrations`): External API integrations
5. **Controllers** (`app.controller`): Business logic controllers
6. **Strategies** (`app.strategy`): Trading strategies
7. **Traders** (`app.trader`): Order execution and management
8. **Backtesting** (`app.backtest`): Backtesting framework
9. **Live Trading** (`app.live_trading`): Live trading system
10. **Dashboard** (`app.dashboard`): Web dashboard and visualization

## Dependency Rules

1. **Downward Dependencies Only**: Modules should only import from modules lower in the hierarchy.
2. **No Circular Imports**: Circular imports are strictly prohibited.
3. **Dependency Injection**: Use dependency injection to pass higher-level components to lower-level ones when needed.
4. **Fallback Mechanisms**: Implement fallback mechanisms for critical utilities like logging.

## Handling Circular Import Issues

### Defensive Imports

For critical utilities like logging that might be used across the application, implement defensive imports:

```python
try:
    from app.config.settings import Settings
    settings = Settings()
    # Use settings
except (ImportError, AttributeError):
    # Fallback to default values
    # ...
```

### Late Imports

Use late imports inside functions rather than at the module level when necessary:

```python
def function_that_needs_higher_level_module():
    # Import inside the function to avoid circular imports
    from app.higher_level_module import SomeClass
    # Use SomeClass
```

### Interface Segregation

Define interfaces in lower-level modules and implement them in higher-level modules:

```python
# In app.utils.interfaces
class DataSourceInterface:
    def get_data(self, symbol, timeframe):
        raise NotImplementedError()

# In app.integrations.some_broker
from app.utils.interfaces import DataSourceInterface

class BrokerDataSource(DataSourceInterface):
    def get_data(self, symbol, timeframe):
        # Implementation
```

## Testing Dependencies

When writing tests, use mocks to avoid importing the actual dependencies:

```python
# Instead of importing the actual module
# from app.integrations.broker import BrokerClient

# Use unittest.mock
from unittest.mock import MagicMock
broker_client = MagicMock()
```

## Dependency Visualization

Periodically generate a dependency graph to visualize the module dependencies:

```bash
pip install pydeps
pydeps --max-bacon=10 --cluster app > dependency_graph.svg
```

## Troubleshooting Circular Imports

If you encounter a circular import error:

1. Identify the circular dependency chain
2. Determine which module should be lower in the hierarchy
3. Refactor the code to break the circular dependency using one of the techniques above
4. Update this document if the module hierarchy needs adjustment

## Example: Logging Utility

The logging utility is a critical component used across the application. To avoid circular imports:

1. The logger implementation in `app.utils.logger` has a fallback mechanism for when `Settings` is not available
2. The logger can be configured with default values that don't require importing from higher-level modules
3. Module-specific loggers are created using `get_logger(__name__)` which doesn't require importing settings

This approach ensures that the logging utility can be used anywhere in the application without causing circular imports.

## Import Guidelines

### Absolute Imports

Always use absolute imports for clarity and to avoid circular dependencies:

```python
# Good
from app.config.settings import Settings
from app.utils.logger import get_logger

# Avoid relative imports like:
# from ..config.settings import Settings
```

### Higher-Level Module Imports

When a higher-level module needs to import from a lower-level module, use direct imports:

```python
# Good - Higher-level module importing from lower-level module
from app.utils.validation import validate_parameters
```

### Lower-Level Module Imports

When a lower-level module needs functionality from a higher-level module, use dependency injection or late imports:

```python
# Good - Using dependency injection
def process_data(data, client=None):
    """Process data using an optional client."""
    if client is None:
        # Late import to avoid circular dependency
        from app.integrations.broker import BrokerClient
        client = BrokerClient()
    # Process data using client
``` 