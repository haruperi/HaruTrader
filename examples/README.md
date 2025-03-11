# HaruTrader Examples

This directory contains example scripts demonstrating how to use various components of the HaruTrader algorithmic trading platform.

## Market Data Examples

### 1. Basic Market Data Retrieval

The `test_market_data.py` script demonstrates how to retrieve market data using the `DataAcquisitionManager` class. This script requires a working MetaTrader 5 installation and connection. It shows two methods of retrieving data:

- **Time-based retrieval**: Using `start_time` and `end_time` parameters
- **Position-based retrieval**: Using `start_pos` and `end_pos` parameters

```bash
python examples/test_market_data.py
```

### 2. Mock Market Data Testing

The `test_market_data_mock.py` script demonstrates how to test the market data processing functionality without requiring an actual MetaTrader 5 connection. It uses mock data generated with realistic properties and also shows both time-based and position-based retrieval methods.

```bash
python examples/test_market_data_mock.py
```

### 3. Simple Trading Strategy

The `simple_strategy.py` script demonstrates how to use the market data in a simple moving average crossover trading strategy. It also uses mock data for testing.

```bash
python examples/simple_strategy.py
```

## Data Retrieval Methods

The `get_market_data` function supports two methods of retrieving data:

### Time-based Retrieval

```python
df = data_manager.get_market_data(
    symbol="EURUSD",
    timeframe="H1",
    start_time=datetime(2023, 1, 1),
    end_time=datetime(2023, 1, 7),
    include_volume=True
)
```

### Position-based Retrieval

```python
df = data_manager.get_market_data(
    symbol="EURUSD",
    timeframe="H1",
    start_pos=0,    # Current bar
    end_pos=100,    # Get 100 bars from the current bar
    include_volume=True
)
```

## Requirements

These examples require the following packages:

- pandas
- numpy
- matplotlib
- seaborn
- MetaTrader5 (for non-mock examples)

All required packages are included in the project's `requirements.txt` file.

## Output

The example scripts will:

1. Retrieve or generate market data
2. Process and clean the data
3. Display basic statistics and sample data
4. Generate plots in the `data/plots` directory
5. For the strategy example, calculate and display performance metrics

## Customization

You can modify the example scripts to:

- Change the symbol (e.g., "EURUSD", "USDJPY", "GBPUSD")
- Change the timeframe (e.g., "M1", "M5", "H1", "D1")
- Adjust the time range or position range
- Modify strategy parameters (for the strategy example)

## Troubleshooting

If you encounter issues with the MetaTrader 5 connection:

1. Ensure MetaTrader 5 is installed and running
2. Check that your credentials are correctly set in the `.env` file
3. Try using the mock data examples instead

For any other issues, please check the logs in the `logs` directory. 