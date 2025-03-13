import datetime
import pytz
from typing import Optional, Union, Tuple, Dict, Any, List
import MetaTrader5 as mt5
from zoneinfo import ZoneInfo
from dataclasses import dataclass

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

@dataclass
class TradingSession:
    """Trading session information."""
    name: str
    timezone: str
    start_time: str
    end_time: str
    main_markets: List[str]

class TimeUtils:
    """
    Utility class for handling date and time operations.
    Provides timezone conversions, market hours checks, and other time-related functions.
    """
    
    # Trading session definitions
    TRADING_SESSIONS = {
        'asian': TradingSession(
            name='Asian',
            timezone='Asia/Tokyo',
            start_time='00:00',
            end_time='09:00',
            main_markets=['JPY', 'AUD', 'NZD']
        ),
        'european': TradingSession(
            name='European',
            timezone='Europe/London',
            start_time='08:00',
            end_time='17:00',
            main_markets=['EUR', 'GBP', 'CHF']
        ),
        'us': TradingSession(
            name='US',
            timezone='America/New_York',
            start_time='08:00',
            end_time='17:00',
            main_markets=['USD', 'CAD']
        )
    }

    def __init__(self):
        """Initialize TimeUtils with settings."""
        self.settings = Settings()
        self.default_timezone = pytz.timezone(self.settings.DEFAULT_TIMEZONE)
        
        # Initialize market holidays (can be loaded from a config file or database)
        self.market_holidays = {
            '2024': {
                'new_years': '2024-01-01',
                'good_friday': '2024-03-29',
                'easter_monday': '2024-04-01',
                'memorial_day': '2024-05-27',
                'independence_day': '2024-07-04',
                'labor_day': '2024-09-02',
                'thanksgiving': '2024-11-28',
                'christmas': '2024-12-25'
            }
        }

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

    def is_dst(self, dt: datetime.datetime, timezone: str) -> bool:
        """
        Check if a given datetime is in DST for the specified timezone.
        
        Args:
            dt (datetime.datetime): Datetime to check
            timezone (str): Timezone name
            
        Returns:
            bool: True if datetime is in DST, False otherwise
        """
        tz = ZoneInfo(timezone)
        return dt.astimezone(tz).dst() != datetime.timedelta(0)

    def get_dst_transitions(self, year: int, timezone: str) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
        """
        Get DST transition dates for a specific year and timezone.
        
        Args:
            year (int): Year to check
            timezone (str): Timezone name
            
        Returns:
            Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]: DST start and end dates
        """
        tz = ZoneInfo(timezone)
        transitions = []
        
        # Check each day of the year for DST transitions
        start_date = datetime.datetime(year, 1, 1, tzinfo=tz)
        for i in range(365 + (1 if year % 4 == 0 else 0)):
            date = start_date + datetime.timedelta(days=i)
            next_date = date + datetime.timedelta(days=1)
            
            if date.dst() != next_date.dst():
                transitions.append(date)
                
            if len(transitions) == 2:
                break
                
        return (transitions[0], transitions[1]) if len(transitions) == 2 else (None, None)

    def is_trading_session_active(self, session: str) -> bool:
        """
        Check if a specific trading session is currently active.
        
        Args:
            session (str): Session identifier ('asian', 'european', 'us')
            
        Returns:
            bool: True if session is active, False otherwise
        """
        session = session.lower()
        if session not in self.TRADING_SESSIONS:
            return False
            
        session_info = self.TRADING_SESSIONS[session]
        current_time = self.get_current_time(session_info.timezone)
        
        # Parse session times
        start_hour, start_minute = map(int, session_info.start_time.split(':'))
        end_hour, end_minute = map(int, session_info.end_time.split(':'))
        
        session_start = current_time.replace(
            hour=start_hour, minute=start_minute, second=0, microsecond=0
        )
        session_end = current_time.replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0
        )
        
        return session_start <= current_time <= session_end

    def get_active_sessions(self) -> List[str]:
        """
        Get list of currently active trading sessions.
        
        Returns:
            List[str]: List of active session names
        """
        return [
            session_name 
            for session_name in self.TRADING_SESSIONS.keys()
            if self.is_trading_session_active(session_name)
        ]

    def is_market_holiday(self, date: Optional[datetime.datetime] = None) -> bool:
        """
        Check if a given date is a market holiday.
        
        Args:
            date (Optional[datetime.datetime]): Date to check. Defaults to current date.
            
        Returns:
            bool: True if date is a market holiday, False otherwise
        """
        if date is None:
            date = self.get_current_time()
            
        year_str = str(date.year)
        if year_str not in self.market_holidays:
            return False
            
        date_str = date.strftime('%Y-%m-%d')
        return date_str in self.market_holidays[year_str].values()

    def get_next_trading_day(self, date: Optional[datetime.datetime] = None) -> datetime.datetime:
        """
        Get the next trading day after the given date.
        
        Args:
            date (Optional[datetime.datetime]): Starting date. Defaults to current date.
            
        Returns:
            datetime.datetime: Next trading day
        """
        if date is None:
            date = self.get_current_time()
            
        next_day = date + datetime.timedelta(days=1)
        while next_day.weekday() >= 5 or self.is_market_holiday(next_day):
            next_day += datetime.timedelta(days=1)
            
        return next_day

# Create a singleton instance
time_utils = TimeUtils() 