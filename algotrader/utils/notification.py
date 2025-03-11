"""
Notification utility module.

This module provides a simple interface for sending notifications from anywhere in the application.
"""
from ..controller.notification import NotificationManager

# Re-export NotificationManager for convenience
__all__ = ['NotificationManager'] 