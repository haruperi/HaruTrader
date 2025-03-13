# HaruTrader Tests

This directory contains test scripts for the HaruTrader application.

## Market Data Tests

These tests demonstrate how to retrieve market data using the DataAcquisitionManager.

### Time-Based and Position-Based Retrieval

This test shows how to retrieve market data using both time-based and position-based parameters:

```bash
python -m tests.test_market_data
```

### Mock Data Testing

This test demonstrates how to test the DataAcquisitionManager with mock data, without requiring an actual MetaTrader 5 connection:

```bash
python -m tests.test_market_data_mock
```

## Fundamental Data Tests

This test demonstrates how to retrieve fundamental data from various sources:

```bash
python -m tests.test_fundamental_data
```

## Logger Tests

This test demonstrates how to use the logger module:

```bash
python -m tests.test_logger
```

## Test Organization

The tests are organized into the following directories:

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for testing interactions between components
- `fixtures/`: Test data fixtures

## Running Tests

You can run all tests using pytest:

```bash
pytest
```

Or run specific test files:

```bash
pytest tests/test_market_data.py
```

## Test Requirements

These tests require the following packages:

- pandas
- numpy
- matplotlib
- seaborn
- MetaTrader5 (for non-mock tests)

## Troubleshooting

If you encounter issues running the tests:

1. Ensure your virtual environment is activated
2. Check that all required packages are installed
3. Try using the mock data tests instead

## Adding New Tests

When adding new tests:

1. Follow the naming convention: `test_*.py` for files, `Test*` for classes, and `test_*` for methods
2. Place unit tests in the `unit/` directory
3. Place integration tests in the `integration/` directory
4. Add any necessary test fixtures to the `fixtures/` directory 