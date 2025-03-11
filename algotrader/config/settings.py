"""
Application settings and configuration.
"""
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

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
    'port': int(os.getenv('DASHBOARD_PORT', '8050')),
    'debug': os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true',
}

# Trading parameters
TRADING_CONFIG = {
    'risk_per_trade': float(os.getenv('RISK_PER_TRADE', '0.02')),  # 2% of account balance
    'max_positions': int(os.getenv('MAX_POSITIONS', '10')),
    'default_stop_loss_pips': int(os.getenv('DEFAULT_STOP_LOSS_PIPS', '50')),
    'default_take_profit_pips': int(os.getenv('DEFAULT_TAKE_PROFIT_PIPS', '100')),
    'price_deviation': int(os.getenv('PRICE_DEVIATION', '10')),
    'magic_number': int(os.getenv('MAGIC_NUMBER', '123456')),
}

# Testing settings
TESTING_CONFIG = {
    'test_symbol': os.getenv('TEST_SYMBOL', 'EURUSD'),
    'test_volume': float(os.getenv('TEST_VOLUME', '0.01')),
    'test_stop_loss_pips': int(os.getenv('TEST_STOP_LOSS_PIPS', '50')),
    'test_take_profit_pips': int(os.getenv('TEST_TAKE_PROFIT_PIPS', '100')),
}

# Trading symbols
SYMBOLS_FOREX = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCHF", "USDCAD", "USDJPY"
]

SYMBOLS_COMMODITIES = [
    "XAUUSD", "XAUEUR", "XAUGBP", "XAUJPY", "XAUAUD", "XAUCHF", "XAGUSD"
]

SYMBOLS_INDICES = [
    "US500", "US30", "UK100", "GER40", "NAS100", "USDX", "EURX"
]

# Default logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')


class Settings:
    """
    Settings class that provides access to application configuration.
    This class makes configuration values accessible as attributes.
    """
    
    def __init__(self):
        """Initialize Settings with default values."""
        # Paths
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = DATA_DIR
        self.LOGS_DIR = LOGS_DIR
        self.MODELS_DIR = MODELS_DIR
        
        # Logging settings
        self.LOG_LEVEL = LOG_LEVEL
        self.DEFAULT_TIMEZONE = DEFAULT_TIMEZONE
        
        # Trading configurations
        self.MT5_CONFIG = MT5_CONFIG
        self.DB_CONFIG = DB_CONFIG
        self.TELEGRAM_CONFIG = TELEGRAM_CONFIG
        self.DASHBOARD_CONFIG = DASHBOARD_CONFIG
        self.TRADING_CONFIG = TRADING_CONFIG
        self.TESTING_CONFIG = TESTING_CONFIG
        
        # Symbols
        self.SYMBOLS_FOREX = SYMBOLS_FOREX
        self.SYMBOLS_COMMODITIES = SYMBOLS_COMMODITIES
        self.SYMBOLS_INDICES = SYMBOLS_INDICES
        
        # Market hours (default market hours 9:30-16:00)
        self.DEFAULT_MARKET_HOURS = os.getenv('DEFAULT_MARKET_HOURS', '9:30-16:00')
        self.DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')
        
        # Load any additional environment variables
        self._load_from_env()
    
    def _load_from_env(self):
        """Load additional settings from environment variables."""
        # This method can be extended to load more environment variables
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete configuration dictionary.
        
        Returns:
            Dict[str, Any]: Complete configuration dictionary
        """
        return {
            'mt5': self.MT5_CONFIG,
            'database': self.DB_CONFIG,
            'telegram': self.TELEGRAM_CONFIG,
            'dashboard': self.DASHBOARD_CONFIG,
            'trading': self.TRADING_CONFIG,
            'testing': self.TESTING_CONFIG,
            'symbols': {
                'forex': self.SYMBOLS_FOREX,
                'commodities': self.SYMBOLS_COMMODITIES,
                'indices': self.SYMBOLS_INDICES,
            }
        }
    
    def validate_config(self) -> bool:
        """
        Validate the configuration settings.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        # TODO: Implement configuration validation
        return True


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
        'testing': TESTING_CONFIG,
        'symbols': {
            'forex': SYMBOLS_FOREX,
            'commodities': SYMBOLS_COMMODITIES,
            'indices': SYMBOLS_INDICES,
        }
    }

def validate_config() -> bool:
    """
    Validate the configuration settings.
    
    Returns:
        bool: True if configuration is valid, False otherwise
    """
    # TODO: Implement configuration validation
    return True 