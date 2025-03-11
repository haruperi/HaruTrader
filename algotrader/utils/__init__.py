"""
Utility functions for the algotrader package.
"""

# Import utility functions to make them available at the module level
from algotrader.utils.logger import get_logger, configure_root_logger

# Initialize root logger
configure_root_logger()

# Export specific functions for easier imports
__all__ = [
    # Logger
    'get_logger',
    'configure_root_logger',
]

# Note: The following modules will be imported as they are implemented
# from algotrader.utils.time_utils import (
#     get_current_time, convert_timezone, format_timestamp, 
#     parse_timeframe, timeframe_to_seconds, get_market_hours
# )
# from algotrader.utils.validation import (
#     validate_symbol, validate_timeframe, validate_order_type,
#     validate_order_params, validate_price
# )
# from algotrader.utils.financial import (
#     calculate_position_size, calculate_pip_value, calculate_risk_reward_ratio,
#     calculate_drawdown, calculate_sharpe_ratio, calculate_profit_factor
# )
# from algotrader.utils.data_transform import (
#     resample_ohlc, normalize_data, calculate_indicators, 
#     create_features, split_train_test
# )
# from algotrader.utils.config import load_config, save_config
# from algotrader.utils.http_client import make_request, download_file
# from algotrader.utils.security import encrypt_data, decrypt_data, hash_password
