import datetime
import pytz
from typing import Optional, Union, Tuple, Dict, Any
import MetaTrader5 as mt5

from app.config.settings import Settings

# Define a mapping of timeframe strings to MT5 timeframe constants
def convert_timeframe_to_mt5(timeframe: str) -> Optional[int]:
    """
    Convert a timeframe string to MetaTrader 5 timeframe constant.
    
    Args:
        timeframe (str): Timeframe string (e.g., 'M1', 'M5', 'H1', 'D1')
        
    Returns:
        Optional[int]: MT5 timeframe constant or None if invalid
    """
    timeframe_map = {
        'M1': mt5.TIMEFRAME_M1,
        'M2': mt5.TIMEFRAME_M2,
        'M3': mt5.TIMEFRAME_M3,
        'M4': mt5.TIMEFRAME_M4,
        'M5': mt5.TIMEFRAME_M5,
        'M6': mt5.TIMEFRAME_M6,
        'M10': mt5.TIMEFRAME_M10,
        'M12': mt5.TIMEFRAME_M12,
        'M15': mt5.TIMEFRAME_M15,
        'M20': mt5.TIMEFRAME_M20,
        'M30': mt5.TIMEFRAME_M30,
        'H1': mt5.TIMEFRAME_H1,
        'H2': mt5.TIMEFRAME_H2,
        'H3': mt5.TIMEFRAME_H3,
        'H4': mt5.TIMEFRAME_H4,
        'H6': mt5.TIMEFRAME_H6,
        'H8': mt5.TIMEFRAME_H8,
        'H12': mt5.TIMEFRAME_H12,
        'D1': mt5.TIMEFRAME_D1,
        'W1': mt5.TIMEFRAME_W1,
        'MN1': mt5.TIMEFRAME_MN1
    }
    
    return timeframe_map.get(timeframe.upper())


class TimeUtils:
    """
    Utility class for handling date and time operations.
    Provides timezone conversions, market hours checks, and other time-related functions.
    """
    
    def __init__(self):
        """Initialize TimeUtils with settings."""
        self.settings = Settings()
        self.default_timezone = pytz.timezone(self.settings.DEFAULT_TIMEZONE)
        
    def get_current_time(self, timezone: Optional[str] = None) -> datetime.datetime:
        """
        Get current time in the specified timezone.
        
        Args:
            timezone (str, optional): Timezone name. Defaults to settings default.
            
        Returns:
            datetime.datetime: Current time in the specified timezone
        """
        tz = pytz.timezone(timezone) if timezone else self.default_timezone
        return datetime.datetime.now(tz)
    
    def convert_timezone(self, dt: datetime.datetime, 
                         to_timezone: str) -> datetime.datetime:
        """
        Convert datetime to another timezone.
        
        Args:
            dt (datetime.datetime): Datetime to convert
            to_timezone (str): Target timezone
            
        Returns:
            datetime.datetime: Converted datetime
        """
        if dt.tzinfo is None:
            dt = self.default_timezone.localize(dt)
            
        target_tz = pytz.timezone(to_timezone)
        return dt.astimezone(target_tz)
    
    def is_market_open(self, market: str = "default") -> bool:
        """
        Check if a specific market is currently open.
        
        Args:
            market (str): Market identifier. Defaults to "default".
            
        Returns:
            bool: True if market is open, False otherwise
        """
        # Get market hours from settings
        market_hours = getattr(self.settings, f"{market.upper()}_MARKET_HOURS", None)
        if not market_hours:
            return False
            
        # Get current time in market timezone
        market_tz = getattr(self.settings, f"{market.upper()}_TIMEZONE", 
                           self.settings.DEFAULT_TIMEZONE)
        current_time = self.get_current_time(market_tz)
        
        # Check if current time is within market hours
        current_weekday = current_time.weekday()
        if current_weekday >= 5:  # Weekend (5=Saturday, 6=Sunday)
            return False
            
        open_time_str, close_time_str = market_hours.split('-')
        open_hour, open_minute = map(int, open_time_str.split(':'))
        close_hour, close_minute = map(int, close_time_str.split(':'))
        
        open_time = current_time.replace(
            hour=open_hour, minute=open_minute, second=0, microsecond=0
        )
        close_time = current_time.replace(
            hour=close_hour, minute=close_minute, second=0, microsecond=0
        )
        
        return open_time <= current_time <= close_time
    
    def time_to_next_market_open(self, market: str = "default") -> datetime.timedelta:
        """
        Calculate time remaining until the next market open.
        
        Args:
            market (str): Market identifier. Defaults to "default".
            
        Returns:
            datetime.timedelta: Time until next market open
        """
        # Get market hours and timezone
        market_hours = getattr(self.settings, f"{market.upper()}_MARKET_HOURS", None)
        if not market_hours:
            return datetime.timedelta(0)
            
        market_tz = getattr(self.settings, f"{market.upper()}_TIMEZONE", 
                           self.settings.DEFAULT_TIMEZONE)
        current_time = self.get_current_time(market_tz)
        
        # Parse market open time
        open_time_str = market_hours.split('-')[0]
        open_hour, open_minute = map(int, open_time_str.split(':'))
        
        # Calculate next open time
        next_open = current_time.replace(
            hour=open_hour, minute=open_minute, second=0, microsecond=0
        )
        
        # If current time is past today's open, move to next business day
        if current_time > next_open:
            next_open += datetime.timedelta(days=1)
            
        # Skip weekends
        while next_open.weekday() >= 5:  # Weekend
            next_open += datetime.timedelta(days=1)
            
        return next_open - current_time
    
    def format_timestamp(self, dt: datetime.datetime, 
                         fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format datetime as string.
        
        Args:
            dt (datetime.datetime): Datetime to format
            fmt (str): Format string. Defaults to "%Y-%m-%d %H:%M:%S".
            
        Returns:
            str: Formatted datetime string
        """
        return dt.strftime(fmt)
    
    def parse_timestamp(self, timestamp_str: str, 
                        fmt: str = "%Y-%m-%d %H:%M:%S",
                        timezone: Optional[str] = None) -> datetime.datetime:
        """
        Parse timestamp string to datetime.
        
        Args:
            timestamp_str (str): Timestamp string to parse
            fmt (str): Format string. Defaults to "%Y-%m-%d %H:%M:%S".
            timezone (str, optional): Timezone name. Defaults to settings default.
            
        Returns:
            datetime.datetime: Parsed datetime
        """
        dt = datetime.datetime.strptime(timestamp_str, fmt)
        tz = pytz.timezone(timezone) if timezone else self.default_timezone
        return tz.localize(dt)


# Create a singleton instance
time_utils = TimeUtils() 