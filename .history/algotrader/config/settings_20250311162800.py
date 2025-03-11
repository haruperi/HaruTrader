import os
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logging configuration
def setup_logging() -> None:
    """Configure logging for the application."""
    log_file = os.getenv("LOG_FILE", "logs/harutrader.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

# MT5 configuration
MT5_CONFIG: Dict[str, Any] = {
    "login": int(os.getenv("MT5_LOGIN", 0)),
    "password": os.getenv("MT5_PASSWORD", ""),
    "server": os.getenv("MT5_SERVER", ""),
    "timeout": int(os.getenv("MT5_TIMEOUT", 60000))
}

# Database configuration
DB_CONFIG: Dict[str, str] = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "harutrader"),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", "")
}

# Telegram configuration
TELEGRAM_CONFIG: Dict[str, str] = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID", "")
}

# Dashboard configuration
DASHBOARD_CONFIG: Dict[str, Any] = {
    "secret_key": os.getenv("DASHBOARD_SECRET_KEY", ""),
    "host": os.getenv("DASHBOARD_HOST", "0.0.0.0"),
    "port": int(os.getenv("DASHBOARD_PORT", 5000))
}

# JWT configuration
JWT_CONFIG: Dict[str, Any] = {
    "secret_key": os.getenv("JWT_SECRET_KEY", ""),
    "algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
    "access_token_expire_minutes": int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
}

# Trading parameters
TRADING_CONFIG: Dict[str, Any] = {
    "risk_per_trade": float(os.getenv("RISK_PER_TRADE", 0.02)),
    "max_positions": int(os.getenv("MAX_POSITIONS", 5)),
    "default_stop_loss_pips": int(os.getenv("DEFAULT_STOP_LOSS_PIPS", 50)),
    "default_take_profit_pips": int(os.getenv("DEFAULT_TAKE_PROFIT_PIPS", 100))
} 