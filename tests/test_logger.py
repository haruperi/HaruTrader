#!/usr/bin/env python
"""
Simple test script for the logger module.

This script demonstrates how to use the logger module.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Test importing the logger
print("Importing get_logger from app.utils...")
try:
    from app.utils import get_logger
    print("✅ Successfully imported get_logger")
except ImportError as e:
    print(f"❌ Failed to import get_logger: {e}")
    sys.exit(1)

# Create a logger
print("\nCreating logger...")
logger = get_logger(__name__)
print("✅ Successfully created logger")

# Test importing Settings
print("\nImporting Settings from app.config.settings...")
try:
    from app.config.settings import Settings
    print("✅ Successfully imported Settings")
except ImportError as e:
    print(f"❌ Failed to import Settings: {e}")

print("Script starting...")

# Log some messages
print("Logging messages...")
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
print("Successfully logged messages")

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