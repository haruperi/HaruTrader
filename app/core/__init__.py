"""
Core functionality for the algorithmic trading system.

This module provides the core components of the trading application.
"""

from .mt5_data import DataAcquisitionManager
from .notification import NotificationManager
from .database import DatabaseManager

__all__ = [
    'DataAcquisitionManager',
    'NotificationManager',
    'DatabaseManager'
]
