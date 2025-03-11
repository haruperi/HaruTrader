"""
Application settings and configuration.
"""
from pathlib import Path
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
MODELS_DIR = BASE_DIR / 'models'

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, MODELS_DIR]:
    directory.mkdir(exist_ok=True)

# MetaTrader 5 settings
MT5_CONFIG = {
    'login': int(os.getenv('MT5_LOGIN', '0')),
    'password': os.getenv('MT5_PASSWORD', ''),
    'server': os.getenv('MT5_SERVER', ''),
    'path': os.getenv('MT5_PATH', ''),
    'timeout': 60000,  # milliseconds
}

# Database settings
DB_CONFIG = {
    'host': os.getenv('TIMESCALE_HOST', 'localhost'),
    'port': int(os.getenv('TIMESCALE_PORT', '5432')),
    'database': os.getenv('TIMESCALE_DB', 'harutrader'),
    'user': os.getenv('TIMESCALE_USER', 'postgres'),
    'password': os.getenv('TIMESCALE_PASSWORD', ''),
}

# Telegram settings
TELEGRAM_CONFIG = {
    'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
}

# Web dashboard settings
DASHBOARD_CONFIG = {
    'secret_key': os.getenv('FLASK_SECRET_KEY', 'your-secret-key'),
    'host': os.getenv('DASHBOARD_HOST', '0.0.0.0'),
    'port': int(os.getenv('DASHBOARD_PORT', '5000')),
}

# Trading parameters
TRADING_CONFIG = {
    'risk_per_trade': 0.02,  # 2% risk per trade
    'max_positions': 5,
    'default_stop_loss_pips': 50,
    'default_take_profit_pips': 100,
}

# TODO: Add configuration validation
# TODO: Add configuration encryption for sensitive data
# TODO: Add configuration reload functionality
# TODO: Add configuration backup/restore
# TODO: Add configuration versioning
# TODO: Add configuration documentation
# TODO: Add configuration migration system
# TODO: Add configuration testing utilities
# TODO: Add configuration export/import functionality
# TODO: Add configuration change logging
# TODO: Add configuration access control

def get_config() -> Dict[str, Any]:
    """
    Get the complete configuration dictionary.
    
    Returns:
        Dict[str, Any]: Complete configuration dictionary
    """
    return {
        'mt5': MT5_CONFIG,
        'database': DB_CONFIG,
        'telegram': TELEGRAM_CONFIG,
        'dashboard': DASHBOARD_CONFIG,
        'trading': TRADING_CONFIG,
    }

def validate_config() -> bool:
    """
    Validate the configuration settings.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    # TODO: Implement configuration validation
    return True 