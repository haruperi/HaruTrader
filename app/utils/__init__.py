"""
Utility functions for the app package.

This module provides utility functions for the application.
"""

# Import utility functions to make them available at the module level
from app.utils.logger import get_logger, configure_root_logger

# Initialize root logger
configure_root_logger()

# Export specific functions for easier imports
__all__ = [
    # Logger
    'get_logger',
    'configure_root_logger',
]

# Note: The following modules will be imported as they are implemented
# from app.utils.time_utils import (
#     get_current_time, convert_timezone, format_timestamp, 
#     parse_timeframe, timeframe_to_seconds, get_market_hours
# )
# from app.utils.validation import (
#     validate_symbol, validate_timeframe, validate_order_type,
#     validate_order_params, validate_price
# )
