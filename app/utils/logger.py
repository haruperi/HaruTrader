"""
Logging utility for the app package.

This module provides logging functionality for the application.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Create a fallback logs directory if settings module is not available
try:
    from app.config.settings import Settings
    settings = Settings()
    LOGS_DIR = settings.LOGS_DIR
    DEFAULT_LOG_LEVEL = settings.LOG_LEVEL
except (ImportError, AttributeError):
    # Fallback to default values if settings module is not available
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    LOGS_DIR = BASE_DIR / 'logs'
    DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)

# Map string log levels to logging constants
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Configure default formatter
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

class SensitiveFilter(logging.Filter):
    """Filter to mask sensitive information in log messages."""
    
    def __init__(self, sensitive_words=None):
        super().__init__()
        self.sensitive_words = sensitive_words or ['password', 'token', 'key', 'secret', 'credential']
    
    def filter(self, record):
        if not hasattr(record, 'msg') or not isinstance(record.msg, str):
            return True
            
        msg = record.msg
        for word in self.sensitive_words:
            # Look for patterns like password=xyz or "password": "xyz"
            for pattern in [f"{word}=", f'"{word}":', f"'{word}':"]:
                if pattern in msg.lower():
                    # Find the value after the pattern and mask it
                    start_idx = msg.lower().find(pattern) + len(pattern)
                    # Skip whitespace
                    while start_idx < len(msg) and msg[start_idx].isspace():
                        start_idx += 1
                    
                    # Handle different value formats (quoted, unquoted)
                    if start_idx < len(msg):
                        if msg[start_idx] in ['"', "'"]:
                            # Find the closing quote
                            quote = msg[start_idx]
                            end_idx = msg.find(quote, start_idx + 1)
                            if end_idx > start_idx:
                                # Mask the value between quotes
                                value = msg[start_idx+1:end_idx]
                                masked_value = self._mask_value(value)
                                msg = msg[:start_idx+1] + masked_value + msg[end_idx:]
                        else:
                            # Find the end of the unquoted value (space, comma, etc.)
                            end_idx = start_idx
                            while end_idx < len(msg) and msg[end_idx] not in [' ', ',', '}', ')', '\n', '\t']:
                                end_idx += 1
                            
                            if end_idx > start_idx:
                                # Mask the unquoted value
                                value = msg[start_idx:end_idx]
                                masked_value = self._mask_value(value)
                                msg = msg[:start_idx] + masked_value + msg[end_idx:]
        
        record.msg = msg
        return True
    
    def _mask_value(self, value):
        """Mask a sensitive value, showing only the last few characters."""
        if len(value) <= 4:
            return '*' * len(value)
        return '*' * (len(value) - 4) + value[-4:]


def get_logger(name: str, log_level: Optional[str] = None, 
               log_to_file: bool = True, log_to_console: bool = True,
               detailed_format: bool = False) -> logging.Logger:
    """
    Get a logger with the specified name and configuration.
    
    Args:
        name: The name of the logger, typically __name__
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to a file
        log_to_console: Whether to log to the console
        detailed_format: Whether to use a detailed log format with filename and line number
    
    Returns:
        A configured logger instance
    """
    # Convert module name to a suitable filename
    if name == '__main__':
        file_name = 'main'
    else:
        # Replace dots with underscores for the filename
        file_name = name.replace('.', '_')
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Only configure the logger if it hasn't been configured yet
    if not logger.handlers:
        # Set log level
        level_name = log_level or DEFAULT_LOG_LEVEL
        level = LOG_LEVELS.get(level_name.upper(), logging.INFO)
        logger.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            DETAILED_FORMAT if detailed_format else DEFAULT_FORMAT
        )
        
        # Add console handler if requested
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Add file handler if requested
        if log_to_file:
            # Ensure logs directory exists
            os.makedirs(LOGS_DIR, exist_ok=True)
            
            # Create a rotating file handler
            log_file = LOGS_DIR / f"{file_name}.log"
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # Also log to a common application log file
            app_log_file = LOGS_DIR / "trading_app.log"
            app_file_handler = logging.handlers.RotatingFileHandler(
                app_log_file, maxBytes=10*1024*1024, backupCount=5
            )
            app_file_handler.setFormatter(formatter)
            logger.addHandler(app_file_handler)
        
        # Add sensitive information filter
        sensitive_filter = SensitiveFilter()
        for handler in logger.handlers:
            handler.addFilter(sensitive_filter)
        
        # Don't propagate to the root logger
        logger.propagate = False
    
    return logger


def configure_root_logger(log_level: str = None) -> None:
    """
    Configure the root logger.
    
    Args:
        log_level: The log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Set log level
    level_name = log_level or DEFAULT_LOG_LEVEL
    level = LOG_LEVELS.get(level_name.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format=DEFAULT_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.handlers.RotatingFileHandler(
                LOGS_DIR / "root.log", 
                maxBytes=10*1024*1024, 
                backupCount=5
            )
        ]
    )
    
    # Add sensitive information filter to root logger
    root_logger = logging.getLogger()
    sensitive_filter = SensitiveFilter()
    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter)


def get_log_config() -> Dict[str, Any]:
    """
    Get the logging configuration dictionary.
    
    Returns:
        Dict[str, Any]: Logging configuration dictionary
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': DEFAULT_FORMAT
            },
            'detailed': {
                'format': DETAILED_FORMAT
            }
        },
        'filters': {
            'sensitive': {
                '()': SensitiveFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'filters': ['sensitive'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filters': ['sensitive'],
                'filename': str(LOGS_DIR / 'trading_app.log'),
                'maxBytes': 10*1024*1024,
                'backupCount': 5
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': DEFAULT_LOG_LEVEL,
                'propagate': True
            },
            'app': {
                'handlers': ['console', 'file'],
                'level': DEFAULT_LOG_LEVEL,
                'propagate': False
            }
        }
    } 