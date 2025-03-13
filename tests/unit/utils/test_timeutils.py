import pytest
import datetime
import pytz
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock
import MetaTrader5 as mt5

from app.utils.timeutils import TimeUtils, convert_timeframe_to_mt5, TradingSession, time_utils

class TestTimeframeConversion:
    """Test suite for timeframe conversion functionality."""
    
    def test_valid_timeframe_conversion(self):
        """Test converting valid timeframe strings to MT5 constants."""
        assert convert_timeframe_to_mt5('M1') == mt5.TIMEFRAME_M1
        assert convert_timeframe_to_mt5('H1') == mt5.TIMEFRAME_H1
        assert convert_timeframe_to_mt5('D1') == mt5.TIMEFRAME_D1
        assert convert_timeframe_to_mt5('W1') == mt5.TIMEFRAME_W1
        assert convert_timeframe_to_mt5('MN1') == mt5.TIMEFRAME_MN1
    
    def test_invalid_timeframe_conversion(self):
        """Test converting invalid timeframe strings."""
        assert convert_timeframe_to_mt5('invalid') is None
        assert convert_timeframe_to_mt5('') is None
        assert convert_timeframe_to_mt5('M0') is None

    def test_case_insensitive_conversion(self):
        """Test that timeframe conversion is case-insensitive."""
        assert convert_timeframe_to_mt5('m1') == mt5.TIMEFRAME_M1
        assert convert_timeframe_to_mt5('h4') == mt5.TIMEFRAME_H4
        assert convert_timeframe_to_mt5('d1') == mt5.TIMEFRAME_D1

class TestTimeUtils:
    """Test suite for TimeUtils class."""
    
    @pytest.fixture
    def time_utils_instance(self):
        """Create a TimeUtils instance for testing."""
        with patch('app.utils.timeutils.Settings') as mock_settings:
            mock_settings.return_value.DEFAULT_TIMEZONE = 'UTC'
            return TimeUtils()
    
    def test_get_current_time(self, time_utils_instance):
        """Test getting current time in different timezones."""
        # Test default timezone
        current_time = time_utils_instance.get_current_time()
        assert current_time.tzinfo is not None
        assert str(current_time.tzinfo) == 'UTC'
        
        # Test specific timezone
        ny_time = time_utils_instance.get_current_time('America/New_York')
        assert ny_time.tzinfo is not None
        assert 'America/New_York' in str(ny_time.tzinfo)
    
    def test_convert_timezone(self, time_utils_instance):
        """Test timezone conversion."""
        # Create a UTC datetime
        dt = datetime.datetime(2024, 3, 15, 12, 0, tzinfo=pytz.UTC)
        
        # Convert to New York time
        ny_time = time_utils_instance.convert_timezone(dt, 'America/New_York')
        assert ny_time.tzinfo is not None
        assert 'America/New_York' in str(ny_time.tzinfo)
        
        # Test conversion of naive datetime
        naive_dt = datetime.datetime(2024, 3, 15, 12, 0)
        converted = time_utils_instance.convert_timezone(naive_dt, 'America/New_York')
        assert converted.tzinfo is not None
    
    def test_is_market_open(self, time_utils_instance):
        """Test market open/closed status checking."""
        with patch('app.utils.timeutils.Settings') as mock_settings:
            # Configure mock settings with proper attribute names
            mock_settings_instance = MagicMock()
            mock_settings_instance.DEFAULT_MARKET_HOURS = '09:30-16:00'
            mock_settings_instance.DEFAULT_TIMEZONE = 'America/New_York'
            mock_settings.return_value = mock_settings_instance
            
            # Replace the settings instance in time_utils
            time_utils_instance.settings = mock_settings_instance
            
            # Mock current time to a weekday during market hours
            mock_dt = datetime.datetime(2024, 3, 15, 12, 0)  # Friday at noon
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value = mock_dt
                assert time_utils_instance.is_market_open()
            
            # Mock current time to weekend
            mock_dt = datetime.datetime(2024, 3, 16, 12, 0)  # Saturday at noon
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value = mock_dt
                assert not time_utils_instance.is_market_open()
    
    def test_trading_sessions(self, time_utils_instance):
        """Test trading session functionality."""
        # Test session existence
        assert 'asian' in time_utils_instance.TRADING_SESSIONS
        assert 'european' in time_utils_instance.TRADING_SESSIONS
        assert 'us' in time_utils_instance.TRADING_SESSIONS
        
        # Test session attributes
        asian_session = time_utils_instance.TRADING_SESSIONS['asian']
        assert isinstance(asian_session, TradingSession)
        assert asian_session.timezone == 'Asia/Tokyo'
        assert 'JPY' in asian_session.main_markets
    
    def test_is_dst(self, time_utils_instance):
        """Test DST detection."""
        # Test summer time in New York
        summer_dt = datetime.datetime(2024, 7, 1, 12, 0)
        assert time_utils_instance.is_dst(summer_dt, 'America/New_York')
        
        # Test winter time in New York
        winter_dt = datetime.datetime(2024, 1, 1, 12, 0)
        assert not time_utils_instance.is_dst(winter_dt, 'America/New_York')
    
    def test_get_dst_transitions(self, time_utils_instance):
        """Test getting DST transition dates."""
        transitions = time_utils_instance.get_dst_transitions(2024, 'America/New_York')
        assert len(transitions) == 2
        assert all(isinstance(dt, (datetime.datetime, type(None))) for dt in transitions)
    
    def test_market_holidays(self, time_utils_instance):
        """Test market holiday detection."""
        # Test known holiday
        holiday_date = datetime.datetime(2024, 12, 25)  # Christmas
        assert time_utils_instance.is_market_holiday(holiday_date)
        
        # Test regular trading day
        trading_date = datetime.datetime(2024, 3, 14)
        assert not time_utils_instance.is_market_holiday(trading_date)
    
    def test_get_next_trading_day(self, time_utils_instance):
        """Test getting next trading day."""
        # Test from Friday to Monday
        friday = datetime.datetime(2024, 3, 15)
        next_day = time_utils_instance.get_next_trading_day(friday)
        assert next_day.weekday() == 0  # Should be Monday
        
        # Test from before holiday to after holiday
        pre_christmas = datetime.datetime(2024, 12, 24)
        next_day = time_utils_instance.get_next_trading_day(pre_christmas)
        assert next_day.day == 26  # Should skip Christmas
    
    def test_format_and_parse_timestamp(self, time_utils_instance):
        """Test timestamp formatting and parsing."""
        # Test formatting
        dt = datetime.datetime(2024, 3, 15, 12, 30, 45, tzinfo=pytz.UTC)
        formatted = time_utils_instance.format_timestamp(dt)
        assert formatted == '2024-03-15 12:30:45'
        
        # Test parsing
        parsed = time_utils_instance.parse_timestamp('2024-03-15 12:30:45')
        assert parsed.year == 2024
        assert parsed.month == 3
        assert parsed.day == 15
        assert parsed.hour == 12
        assert parsed.minute == 30
        assert parsed.second == 45
        assert parsed.tzinfo is not None

def test_singleton_instance():
    """Test that the singleton instance is properly created."""
    assert time_utils is not None
    assert isinstance(time_utils, TimeUtils)
    
    # Test that we get the same instance when importing again
    from app.utils.timeutils import time_utils as time_utils2
    assert time_utils is time_utils2 