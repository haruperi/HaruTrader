#!/usr/bin/env python
"""
Simple test script to verify logger functionality.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

print("Script starting...")

# Import the logger
print("Importing get_logger from algotrader.utils...")
from algotrader.utils import get_logger
print("Successfully imported get_logger")

# Create a logger
print("Creating logger...")
logger = get_logger("simple_logger_test")
print("Successfully created logger")

# Log some messages
print("Logging messages...")
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
print("Successfully logged messages")

# Import Settings and use it with the logger
print("Importing Settings from algotrader.config.settings...")
from algotrader.config.settings import Settings
print("Successfully imported Settings")

# Create settings
print("Creating Settings instance...")
settings = Settings()
print("Successfully created Settings instance")

# Log settings information
print("Logging settings information...")
logger.info(f"Log level: {settings.LOG_LEVEL}")
logger.info(f"Base directory: {settings.BASE_DIR}")
logger.info(f"Logs directory: {settings.LOGS_DIR}")
print("Successfully logged settings information")

print("All tests completed successfully!") 