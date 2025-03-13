"""
Logging utility for the app package.

This module provides logging functionality for the application.
"""

import logging
import logging.handlers
import os
import sys
import re
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

# Store logger configurations
_logger_configs = {}

class SensitiveFilter(logging.Filter):
    """Filter to mask sensitive information in log messages."""
    
    def __init__(self, sensitive_words=None):
        super().__init__()
        self.sensitive_words = sensitive_words or ['password', 'token', 'key', 'secret', 'credential']
        # Compile regex patterns for better performance
        self.patterns = [
            # JSON format: "key": "value" or 'key': 'value'
            re.compile(r'(["\']?(?:' + '|'.join(self.sensitive_words) + r')["\']?\s*[:=]\s*["\']?)([^"\'\s,})\n]+)(["\']?)', re.IGNORECASE),
        ]
    
    def filter(self, record):
        """Filter log records to mask sensitive information."""
        if not hasattr(record, 'msg') or not isinstance(record.msg, str):
            return True
            
        msg = str(record.msg)
        
        # Handle all formats with a single pattern
        msg = self.patterns[0].sub(
            lambda m: (
                m.group(1) +  # Keep the prefix (key name, quotes, and separator)
                '***' +  # Always use exactly 3 asterisks
                (m.group(2)[-3:] if len(m.group(2)) > 3 else m.group(2)) +  # Keep last 3 chars
                m.group(3)  # Keep the suffix (closing quote)
            ),
            msg
        )
        
        record.msg = msg
        return True


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
    global _logger_configs
    
    # Convert module name to a suitable filename
    if name == '__main__':
        file_name = 'main'
    else:
        # Replace dots with underscores for the filename
        file_name = name.replace('.', '_')
    
    # Get or create logger
    logger = logging.getLogger(name)
    
    # Check if logger was previously configured
    if name in _logger_configs:
        prev_config = _logger_configs[name]
        log_level = log_level or prev_config.get('log_level')
        log_to_file = prev_config.get('log_to_file', log_to_file)
        log_to_console = prev_config.get('log_to_console', log_to_console)
        detailed_format = prev_config.get('detailed_format', detailed_format)
    
    # Remove any existing handlers
    logger.handlers.clear()
    
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
        console_handler.setLevel(level)  # Set handler level
        logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        # Ensure logs directory exists
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Create a rotating file handler
        log_file = LOGS_DIR / f"{file_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=1024*1024, backupCount=5  # 1MB per file
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)  # Set handler level
        logger.addHandler(file_handler)
        
        # Also log to a common application log file
        app_log_file = LOGS_DIR / "trading_app.log"
        app_file_handler = logging.handlers.RotatingFileHandler(
            app_log_file, maxBytes=1024*1024, backupCount=5  # 1MB per file
        )
        app_file_handler.setFormatter(formatter)
        app_file_handler.setLevel(level)  # Set handler level
        logger.addHandler(app_file_handler)
    
    # Add sensitive information filter
    sensitive_filter = SensitiveFilter()
    for handler in logger.handlers:
        handler.addFilter(sensitive_filter)
    
    # Don't propagate to the root logger
    logger.propagate = False
    
    # Store configuration
    _logger_configs[name] = {
        'log_level': level_name,
        'log_to_file': log_to_file,
        'log_to_console': log_to_console,
        'detailed_format': detailed_format
    }
    
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
                maxBytes=1024*1024,  # 1MB per file
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
                'maxBytes': 1024*1024,  # 1MB per file
                'backupCount': 5
            }
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': DEFAULT_LOG_LEVEL,
                'propagate': True
            }
        }
    } 