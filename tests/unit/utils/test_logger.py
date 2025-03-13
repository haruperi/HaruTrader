"""
Unit tests for the logger module.

This module contains test cases for testing the logging functionality.
"""

import os
import logging
import pytest
from pathlib import Path
from app.utils import get_logger
from app.config.settings import Settings

# Test fixtures
@pytest.fixture
def settings():
    """Fixture to provide Settings instance."""
    return Settings()

@pytest.fixture
def temp_log_dir(tmp_path):
    """Fixture to provide a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def logger_name():
    """Fixture to provide a consistent logger name."""
    return "test_logger"

class TestLogger:
    """Test cases for the logger module."""
    
    def test_logger_creation(self, logger_name):
        """Test basic logger creation."""
        logger = get_logger(logger_name)
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name
        
    def test_log_levels(self, logger_name):
        """Test different log levels."""
        logger = get_logger(logger_name)
        
        # Test each log level
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in levels:
            logger.setLevel(level)
            assert logger.getEffectiveLevel() == getattr(logging, level)
            
    def test_file_logging(self, temp_log_dir, logger_name, monkeypatch):
        """Test logging to file."""
        # Patch the LOGS_DIR to use temporary directory
        monkeypatch.setattr('app.utils.logger.LOGS_DIR', temp_log_dir)
        
        logger = get_logger(logger_name, log_to_file=True, log_to_console=False)
        test_message = "Test log message"
        logger.info(test_message)
        
        # Check if log file exists and contains the message
        log_file = temp_log_dir / f"{logger_name}.log"
        assert log_file.exists()
        
        with open(log_file) as f:
            content = f.read()
            assert test_message in content
            
    def test_console_logging(self, logger_name, capsys):
        """Test logging to console."""
        logger = get_logger(logger_name, log_to_file=False, log_to_console=True)
        test_message = "Test console message"
        logger.info(test_message)
        
        # Check if message appears in stdout
        captured = capsys.readouterr()
        assert test_message in captured.out
        
    def test_sensitive_data_filtering(self, logger_name, capsys):
        """Test filtering of sensitive information."""
        logger = get_logger(logger_name, log_to_file=False, log_to_console=True)
        
        # Test different sensitive data patterns
        test_cases = [
            ('password=secret123', 'password=***123'),  # Password with equals
            ('{"api_key": "abcd1234"}', '{"api_key": "***234"}'),  # JSON format
            ("token='mytoken'", "token='***ken'"),  # Single quoted
            ('secret: "topsecret"', 'secret: "***ret"')  # Double quoted with colon
        ]
        
        for input_msg, expected_masked in test_cases:
            logger.info(input_msg)
            captured = capsys.readouterr()
            # Check if sensitive data is masked
            assert expected_masked in captured.out
            
    def test_detailed_formatting(self, logger_name, capsys):
        """Test detailed log formatting."""
        logger = get_logger(logger_name, detailed_format=True, log_to_file=False)
        test_message = "Test detailed format"
        logger.info(test_message)
        
        captured = capsys.readouterr()
        # Check if output contains the message and basic format elements
        assert test_message in captured.out
        assert logger_name in captured.out
        assert "INFO" in captured.out
        
    def test_log_rotation(self, temp_log_dir, logger_name, monkeypatch):
        """Test log file rotation."""
        monkeypatch.setattr('app.utils.logger.LOGS_DIR', temp_log_dir)
        
        logger = get_logger(logger_name, log_to_file=True, log_to_console=False)
        log_file = temp_log_dir / f"{logger_name}.log"
        
        # Generate enough logs to trigger rotation
        large_message = "x" * 1024 * 1024  # 1MB message
        for _ in range(11):  # Should create multiple log files
            logger.info(large_message)
            
        # Check if rotation occurred
        rotation_files = list(temp_log_dir.glob(f"{logger_name}.log.*"))
        assert len(rotation_files) > 0
        
    def test_multiple_handlers(self, logger_name):
        """Test logger with multiple handlers."""
        logger = get_logger(logger_name, log_to_file=True, log_to_console=True)
        
        # Count handlers
        handlers = logger.handlers
        assert len(handlers) >= 2  # Should have at least console and file handler
        
        # Check handler types
        handler_types = [type(h) for h in handlers]
        assert logging.StreamHandler in handler_types
        assert logging.handlers.RotatingFileHandler in handler_types
        
    def test_logger_persistence(self, logger_name):
        """Test that logger configuration persists."""
        # Create logger with specific configuration
        logger1 = get_logger(logger_name, log_level='DEBUG')
        original_level = logger1.getEffectiveLevel()
        
        # Get same logger again
        logger2 = get_logger(logger_name)
        
        # Check if configuration persisted
        assert logger2.getEffectiveLevel() == original_level
        assert len(logger2.handlers) == len(logger1.handlers)
        
    def test_invalid_log_level(self, logger_name):
        """Test handling of invalid log level."""
        logger = get_logger(logger_name, log_level='INVALID_LEVEL')
        
        # Should default to INFO
        assert logger.getEffectiveLevel() == logging.INFO

if __name__ == '__main__':
    pytest.main(['-v', __file__]) 