"""
Market data acquisition and processing module.
"""
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from dotenv import load_dotenv
from ..config.settings import get_config, SYMBOLS_FOREX, SYMBOLS_COMMODITIES, SYMBOLS_INDICES
from .investpy import InvestpyClient
from .forex_factory import ForexFactoryClient
from .social_media import SocialMediaClient
from ..utils.logger import get_logger
from ..utils.validation import Validator, ValidationError
from ..utils.timeutils import convert_timeframe_to_mt5

logger = get_logger(__name__)

class MT5Client:
    """
    MetaTrader 5 client for connection management, market data retrieval, and trading operations.
    
    This class handles the connection to the MetaTrader 5 terminal,
    authentication, and provides methods for market data retrieval and trading.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MT5 client.
        
        Args:
            config: Optional dictionary with connection parameters.
                   If not provided, parameters will be loaded from environment variables.
        """
        # Load environment variables if not already loaded
        load_dotenv()
        
        self.config = config or {
            'login': os.getenv('MT5_LOGIN'),
            'password': os.getenv('MT5_PASSWORD'),
            'server': os.getenv('MT5_SERVER'),
            'path': os.getenv('MT5_PATH'),
            'timeout': 60000  # Connection timeout in milliseconds
        }
        
        self.connected = False
        self.initialized = False
        self.initialized_symbols = []
        self.failed_symbols = []
    
    def initialize_symbols(self) -> Tuple[List[str], List[str]]:
        """
        Initialize all trading symbols in MetaTrader 5.
        
        Returns:
            Tuple[List[str], List[str]]: A tuple containing (successful_symbols, failed_symbols)
        """
        logger.info("Initializing trading symbols in MetaTrader 5...")
        
        # Combine all symbols
        all_symbols = SYMBOLS_FOREX + SYMBOLS_COMMODITIES + SYMBOLS_INDICES
        
        successful_symbols = []
        failed_symbols = []
        
        for symbol in all_symbols:
            # Enable symbol in Market Watch
            if not mt5.symbol_select(symbol, True):
                error = mt5.last_error()
                logger.warning(f"Failed to initialize symbol {symbol}. Error code: {error[0]}, Error description: {error[1]}")
                failed_symbols.append(symbol)
            else:
                # Get symbol info to verify it's properly initialized
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    logger.debug(f"Symbol {symbol} initialized successfully")
                    successful_symbols.append(symbol)
                else:
                    error = mt5.last_error()
                    logger.warning(f"Symbol {symbol} selected but info not available. Error: {error[1]}")
                    failed_symbols.append(symbol)
        
        logger.info(f"Symbol initialization complete. Success: {len(successful_symbols)}, Failed: {len(failed_symbols)}")
        
        if failed_symbols:
            logger.warning(f"Failed symbols: {', '.join(failed_symbols)}")
        
        self.initialized_symbols = successful_symbols
        self.failed_symbols = failed_symbols
        
        return successful_symbols, failed_symbols
        
    def initialize(self) -> bool:
        """
        Initialize the MT5 terminal.
        
        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        if self.initialized:
            logger.info("MT5 is already initialized")
            return True
            
        logger.info("Initializing MT5 terminal...")
        
        # Initialize MT5
        mt5_path = self.config.get('path')
        if not mt5_path:
            logger.error("MT5 path not specified")
            return False
            
        init_result = mt5.initialize(
            path=mt5_path,
            login=int(self.config.get('login', 0)),
            password=self.config.get('password', ''),
            server=self.config.get('server', ''),
            timeout=int(self.config.get('timeout', 60000))
        )
        
        if not init_result:
            error = mt5.last_error()
            logger.error(f"MT5 initialization failed. Error code: {error[0]}, Error description: {error[1]}")
            return False
            
        self.initialized = True
        logger.info("MT5 terminal initialized successfully")
        
        # Initialize symbols
        self.initialize_symbols()
        
        return True
        
    def connect(self) -> bool:
        """
        Connect to the MT5 terminal.
        
        Returns:
            bool: True if connection was successful, False otherwise.
        """
        if not self.initialized and not self.initialize():
            return False
            
        if self.connected:
            logger.info("Already connected to MT5")
            return True
            
        logger.info("Connecting to MT5 terminal...")
        
        # Check if we're already authorized
        account_info = mt5.account_info()
        if account_info is not None:
            self.connected = True
            logger.info(f"Connected to MT5. Account: {account_info.login}, Server: {account_info.server}")
            return True
            
        # Try to login
        login_result = mt5.login(
            login=int(self.config.get('login', 0)),
            password=self.config.get('password', ''),
            server=self.config.get('server', '')
        )
        
        if not login_result:
            error = mt5.last_error()
            logger.error(f"MT5 login failed. Error code: {error[0]}, Error description: {error[1]}")
            return False
            
        self.connected = True
        account_info = mt5.account_info()
        logger.info(f"Connected to MT5. Account: {account_info.login}, Server: {account_info.server}")
        return True
        
    def disconnect(self) -> None:
        """
        Disconnect from the MT5 terminal.
        """
        if self.connected or self.initialized:
            logger.info("Shutting down MT5 connection...")
            mt5.shutdown()
            self.connected = False
            self.initialized = False
            self.initialized_symbols = []
            self.failed_symbols = []
            logger.info("MT5 connection closed")
            
    def is_connected(self) -> bool:
        """
        Check if connected to MT5.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        if not self.initialized:
            return False
            
        # Check if terminal is still responding
        account_info = mt5.account_info()
        self.connected = account_info is not None
        return self.connected
        
    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """
        Get account information.
        
        Returns:
            dict: Account information or None if not connected.
        """
        if not self.is_connected() and not self.connect():
            return None
            
        account_info = mt5.account_info()
        if account_info is None:
            return None
            
        # Convert named tuple to dictionary
        return {
            'login': account_info.login,
            'server': account_info.server,
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'leverage': account_info.leverage,
            'currency': account_info.currency,
            'name': account_info.name,
            'company': account_info.company
        }
    
    def get_initialized_symbols(self) -> List[str]:
        """
        Get the list of successfully initialized symbols.
        
        Returns:
            List[str]: List of initialized symbols
        """
        return self.initialized_symbols
    
    def get_failed_symbols(self) -> List[str]:
        """
        Get the list of symbols that failed to initialize.
        
        Returns:
            List[str]: List of failed symbols
        """
        return self.failed_symbols
        
    def get_rates(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        start_pos: Optional[int] = None,
        end_pos: Optional[int] = None,
        include_volume: bool = True
    ) -> pd.DataFrame:
        """
        Retrieve market data for a symbol.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., 'M1', 'M5', 'H1', 'D1')
            start_time (Optional[datetime]): Start time (used if start_pos is None)
            end_time (Optional[datetime]): End time (default: current time, used if start_pos is None)
            start_pos (Optional[int]): Start position (number of bars from the current bar)
            end_pos (Optional[int]): End position (number of bars from the current bar)
            include_volume (bool): Whether to include volume data
            
        Returns:
            pd.DataFrame: Market data with OHLCV columns
        """
        if not self.initialized:
            if not self.initialize():
                logger.error("Failed to initialize MT5Client for get_rates")
                return pd.DataFrame()
                
        # Convert timeframe string to MT5 timeframe constant
        mt5_timeframe = convert_timeframe_to_mt5(timeframe)
        if mt5_timeframe is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return pd.DataFrame()
            
        # Ensure symbol is available
        if not mt5.symbol_select(symbol, True):
            logger.error(f"Failed to select symbol {symbol}")
            return pd.DataFrame()
            
        # Retrieve rates from MT5 based on the provided parameters
        rates = None
        
        # Case 1: Using start_pos and end_pos (position-based retrieval)
        if start_pos is not None:
            # If end_pos is not provided, get all data from start_pos to the current bar
            count = abs(end_pos - start_pos) if end_pos is not None else abs(start_pos)
            
            # Use copy_rates_from_pos to get data based on position
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, start_pos, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {symbol} from position {start_pos} to {end_pos}")
                return pd.DataFrame()
                
        # Case 2: Using start_time and end_time (time-based retrieval)
        else:
            # Set end_time to current time if not provided
            if end_time is None:
                end_time = datetime.now()
                
            # Set start_time to 30 days before end_time if not provided
            if start_time is None:
                start_time = end_time - timedelta(days=30)
                
            # Use copy_rates_range to get data based on time range
            rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_time, end_time)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No data returned for {symbol} from {start_time} to {end_time}")
                return pd.DataFrame()
            
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        
        # Convert time column to datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Rename columns to match required format
        column_mapping = {
            'time': 'DateTime',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'tick_volume': 'Volume'
        }
        
        # Select and rename columns
        columns_to_keep = ['time', 'open', 'high', 'low', 'close']
        if include_volume:
            columns_to_keep.append('tick_volume')
            
        df = df[columns_to_keep].rename(columns=column_mapping)
        
        # Set DateTime as index
        df.set_index('DateTime', inplace=True)
        
        return df
        
    def __enter__(self):
        """
        Context manager entry.
        """
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        self.disconnect()

class MarketData:
    """
    Class for storing and manipulating market data.
    
    This class provides a structured way to store OHLCV data for different symbols
    and timeframes, along with methods for data manipulation and analysis.
    """
    
    def __init__(self, symbol: str, timeframe: str, data: Optional[pd.DataFrame] = None):
        """
        Initialize a new MarketData instance.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe of the data
            data (pd.DataFrame, optional): Initial market data
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = data if data is not None else pd.DataFrame()
        self.last_update_time = datetime.now() if data is not None else None
    
    def update(self, data: pd.DataFrame) -> None:
        """
        Update the market data with new data.
        
        Args:
            data (pd.DataFrame): New market data
        """
        if self.data.empty:
            self.data = data
        else:
            # Combine existing data with new data, removing duplicates
            combined = pd.concat([self.data, data])
            self.data = combined[~combined.index.duplicated(keep='last')].sort_index()
        
        self.last_update_time = datetime.now()
    
    def get_latest_bar(self) -> Optional[pd.Series]:
        """
        Get the latest bar of market data.
        
        Returns:
            pd.Series: Latest bar of market data, or None if no data is available
        """
        if self.data.empty:
            return None
        
        return self.data.iloc[-1]
    
    def get_latest_close(self) -> Optional[float]:
        """
        Get the latest close price.
        
        Returns:
            float: Latest close price, or None if no data is available
        """
        latest_bar = self.get_latest_bar()
        if latest_bar is None or 'Close' not in latest_bar:
            return None
        
        return latest_bar['Close']
    
    def get_data_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        num_bars: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get a range of market data.
        
        Args:
            start_time (datetime, optional): Start time for the range
            end_time (datetime, optional): End time for the range
            num_bars (int, optional): Number of bars to return from the end
            
        Returns:
            pd.DataFrame: Range of market data
        """
        if self.data.empty:
            return pd.DataFrame()
        
        # If num_bars is specified, return the last N bars
        if num_bars is not None:
            return self.data.iloc[-num_bars:]
        
        # If start_time and end_time are specified, return data in that range
        if start_time is not None and end_time is not None:
            return self.data[(self.data.index >= start_time) & (self.data.index <= end_time)]
        
        # If only start_time is specified, return data from that time onwards
        if start_time is not None:
            return self.data[self.data.index >= start_time]
        
        # If only end_time is specified, return data up to that time
        if end_time is not None:
            return self.data[self.data.index <= end_time]
        
        # If no parameters are specified, return all data
        return self.data
    
    def is_data_fresh(self, max_age_seconds: int = 300) -> bool:
        """
        Check if the market data is fresh.
        
        Args:
            max_age_seconds (int, optional): Maximum age in seconds for data to be considered fresh
            
        Returns:
            bool: True if data is fresh, False otherwise
        """
        if self.last_update_time is None:
            return False
        
        age = (datetime.now() - self.last_update_time).total_seconds()
        return age <= max_age_seconds
    
    def __len__(self) -> int:
        """
        Get the number of bars in the market data.
        
        Returns:
            int: Number of bars
        """
        return len(self.data)
    
    def __str__(self) -> str:
        """
        Get a string representation of the market data.
        
        Returns:
            str: String representation
        """
        return f"MarketData(symbol={self.symbol}, timeframe={self.timeframe}, bars={len(self)})"

class DataAcquisitionManager:
    """Manages market data acquisition from multiple sources."""
    
    def __init__(self):
        """Initialize the data acquisition manager."""
        self.config = get_config()
        self.mt5_client = MT5Client()
        self.investpy_client = InvestpyClient()
        self.forex_factory_client = ForexFactoryClient()
        self.social_media_client = SocialMediaClient()
        
        # Initialize MT5 client
        if not self.mt5_client.initialize():
            logger.warning("Failed to initialize MT5 client during DataAcquisitionManager initialization")
    
    def get_market_data(
        self,
        symbol: str,
        timeframe: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        start_pos: Optional[int] = None,
        end_pos: Optional[int] = None,
        include_volume: bool = True
    ) -> MarketData:
        """
        Retrieve market data for a symbol.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe (e.g., 'M1', 'M5', 'H1', 'D1')
            start_time (Optional[datetime]): Start time (used if start_pos is None)
            end_time (Optional[datetime]): End time (default: current time, used if start_pos is None)
            start_pos (Optional[int]): Start position (number of bars from the current bar)
            end_pos (Optional[int]): End position (number of bars from the current bar)
            include_volume (bool): Whether to include volume data
            
        Returns:
            MarketData: Market data object with OHLCV data
        """
        # Log appropriate message based on retrieval method
        if start_pos is not None:
            end_pos_str = f" to {end_pos}" if end_pos is not None else ""
            logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}, from position: {start_pos}{end_pos_str}")
        else:
            time_range = f"from: {start_time} to: {end_time}" if start_time else f"last 30 days to: {end_time or 'now'}"
            logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}, {time_range}")
        
        try:
            # Validate input parameters
            self._validate_market_data_params(symbol, timeframe, start_time, end_time, start_pos, end_pos)
            
            # Ensure MT5 client is connected
            if not self.mt5_client.is_connected() and not self.mt5_client.connect():
                logger.error("Failed to connect to MT5")
                return MarketData(symbol, timeframe)  # Return empty MarketData object
            
            # Retrieve market data from MT5
            df = self.mt5_client.get_rates(
                symbol=symbol, 
                timeframe=timeframe, 
                start_time=start_time, 
                end_time=end_time,
                start_pos=start_pos,
                end_pos=end_pos,
                include_volume=include_volume
            )
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return MarketData(symbol, timeframe)  # Return empty MarketData object
                
            # Clean the data
            df = self._clean_market_data(df)
            
            # Handle missing values
            df = self._handle_missing_values(df)
            
            # Create and return a MarketData object
            market_data = MarketData(symbol, timeframe, df)
            
            logger.info(f"Successfully retrieved {len(market_data)} records for {symbol}")
            return market_data
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return MarketData(symbol, timeframe)  # Return empty MarketData object
        except Exception as e:
            logger.exception(f"Error retrieving market data for {symbol}: {str(e)}")
            return MarketData(symbol, timeframe)  # Return empty MarketData object
    
    def _validate_market_data_params(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: Optional[datetime], 
        end_time: Optional[datetime],
        start_pos: Optional[int],
        end_pos: Optional[int]
    ) -> None:
        """
        Validate market data parameters.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            start_time (Optional[datetime]): Start time
            end_time (Optional[datetime]): End time
            start_pos (Optional[int]): Start position
            end_pos (Optional[int]): End position
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
            
        # Validate timeframe
        valid_timeframes = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M10', 'M12', 'M15', 
                           'M20', 'M30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12', 
                           'D1', 'W1', 'MN1']
        if timeframe.upper() not in valid_timeframes:
            raise ValidationError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")
            
        # Validate start_time
        if start_time is not None and not isinstance(start_time, datetime):
            raise ValidationError("start_time must be a datetime object")
            
        # Validate end_time if provided
        if end_time is not None and not isinstance(end_time, datetime):
            raise ValidationError("end_time must be a datetime object")
                
        # Validate time range if both start_time and end_time are provided
        if end_time is not None and start_time is not None:
            if end_time <= start_time:
                raise ValidationError("end_time must be after start_time")
                
            # Validate time range is not too large
            time_diff = end_time - start_time
            max_days = 365  # Maximum allowed range in days
            if time_diff.days > max_days:
                raise ValidationError(f"Time range too large. Maximum allowed is {max_days} days")
        
        # Validate start_pos and end_pos
        if start_pos is not None and not isinstance(start_pos, int):
            raise ValidationError("start_pos must be an integer")
        if end_pos is not None and not isinstance(end_pos, int):
            raise ValidationError("end_pos must be an integer")
        
        if start_pos is not None and end_pos is not None:
            if start_pos > end_pos:
                raise ValidationError("start_pos must be less than or equal to end_pos")
            
        # Ensure either time-based or position-based parameters are provided
        if start_time is None and end_time is None and start_pos is None:
            raise ValidationError("Either start_time/end_time or start_pos/end_pos must be provided")
    
    def _clean_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean market data.
        
        Args:
            df (pd.DataFrame): Market data DataFrame
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by datetime
        df = df.sort_index()
        
        # Remove rows with negative or zero prices
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df = df[df[col] > 0]
                
        # Ensure High is the highest price
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            price_cols = ['Open', 'High', 'Low', 'Close']
            df['High'] = df[price_cols].max(axis=1)
            
            # Ensure Low is the lowest price
            df['Low'] = df[price_cols].min(axis=1)
            
            # Ensure High >= Open, Close and Low <= Open, Close
            df['High'] = df[['High', 'Open', 'Close']].max(axis=1)
            df['Low'] = df[['Low', 'Open', 'Close']].min(axis=1)
        
        # Remove rows with abnormal volume if Volume column exists
        if 'Volume' in df.columns:
            # Remove zero or negative volume
            df = df[df['Volume'] > 0]
            
            # Remove outliers (e.g., volume > 3 standard deviations from mean)
            mean_volume = df['Volume'].mean()
            std_volume = df['Volume'].std()
            df = df[df['Volume'] <= mean_volume + 3 * std_volume]
            
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in market data.
        
        Args:
            df (pd.DataFrame): Market data DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Check for missing values
        if not df.isna().any().any():
            return df
            
        # Fill missing values in OHLC columns with forward fill then backward fill
        ohlc_cols = [col for col in ['Open', 'High', 'Low', 'Close'] if col in df.columns]
        if ohlc_cols:
            # Handle each column individually to avoid linter errors
            for col in ohlc_cols:
                # Forward fill first
                df[col] = df[col].ffill()
                # Then backward fill any remaining NaNs
                df[col] = df[col].bfill()
            
        # Fill missing values in Volume column with zeros
        if 'Volume' in df.columns and df['Volume'].isna().any():
            df['Volume'] = df['Volume'].fillna(0)
            
        return df
    
    def get_fundamental_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        data_sources: Optional[List[str]] = None,
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve fundamental data for a symbol from multiple sources.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (Optional[datetime]): End date (defaults to current date if None)
            data_sources (Optional[List[str]]): List of data sources to use
                Options: 'investpy', 'forex_factory', 'social_media', 'all'
            include_sentiment (bool): Whether to include sentiment data
            
        Returns:
            Dict[str, Any]: Fundamental data including:
                - company_info: Company information (if available)
                - economic_events: Economic calendar events affecting the symbol
                - sentiment: Social media sentiment data (if include_sentiment is True)
                - market_sentiment: Market sentiment data from trading platforms
                - source_metadata: Information about data sources used
        """
        logger.info(f"Retrieving fundamental data for {symbol} from {start_date} to {end_date or datetime.now()}")
        
        # Set default end_date if not provided
        if end_date is None:
            end_date = datetime.now()
            
        # Validate inputs
        self._validate_fundamental_data_params(symbol, start_date, end_date)
        
        # Determine which data sources to use
        available_sources = ['investpy', 'forex_factory', 'social_media']
        if data_sources is None or 'all' in data_sources:
            data_sources = available_sources
        else:
            # Filter to only include valid sources
            data_sources = [source for source in data_sources if source in available_sources]
            
        if not data_sources:
            logger.warning("No valid data sources specified for fundamental data retrieval")
            return {}
            
        logger.info(f"Using data sources: {', '.join(data_sources)}")
        
        # Initialize result dictionary
        result = {
            'company_info': {},
            'economic_events': pd.DataFrame(),
            'sentiment': {},
            'market_sentiment': {},
            'source_metadata': {
                'sources_used': data_sources,
                'retrieval_time': datetime.now(),
                'time_range': {
                    'start': start_date,
                    'end': end_date
                }
            }
        }
        
        # Retrieve data from each source
        if 'investpy' in data_sources:
            self._get_investpy_data(symbol, start_date, end_date, result)
            
        if 'forex_factory' in data_sources:
            self._get_forex_factory_data(symbol, start_date, end_date, result)
            
        if 'social_media' in data_sources and include_sentiment:
            self._get_social_media_data(symbol, start_date, end_date, result)
            
        # Aggregate and verify data
        self._aggregate_fundamental_data(result)
        self._verify_fundamental_data(result)
        
        return result
        
    def _validate_fundamental_data_params(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """
        Validate parameters for fundamental data retrieval.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
            
        # Validate dates
        if not isinstance(start_date, datetime):
            raise ValidationError("Start date must be a datetime object")
            
        if not isinstance(end_date, datetime):
            raise ValidationError("End date must be a datetime object")
            
        if end_date < start_date:
            raise ValidationError("End date must be after start date")
            
        # Check if date range is too large (e.g., more than 1 year)
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise ValidationError(f"Date range exceeds maximum of {max_days} days")
    
    def _get_investpy_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from Investpy and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving Investpy data for {symbol}")
        
        try:
            # Get company information
            company_info = self.investpy_client.get_company_info(symbol)
            if company_info:
                result['company_info'].update(company_info)
                
            # Get economic calendar events
            calendar_data = self.investpy_client.get_economic_calendar(
                start_date=start_date,
                end_date=end_date
            )
            
            if not calendar_data.empty:
                # Filter events that might affect this symbol
                # This is a simplified approach - in a real implementation,
                # you would need more sophisticated filtering
                if 'USD' in symbol:
                    calendar_data = calendar_data[calendar_data['country'] == 'United States']
                elif 'EUR' in symbol:
                    calendar_data = calendar_data[calendar_data['country'].isin(['Eurozone', 'Germany', 'France'])]
                # Add more currency filters as needed
                
                result['economic_events'] = pd.concat([result['economic_events'], calendar_data])
                
        except Exception as e:
            logger.error(f"Error retrieving Investpy data: {str(e)}")
    
    def _get_forex_factory_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from Forex Factory and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving Forex Factory data for {symbol}")
        
        try:
            # Extract currencies from symbol (assuming format like 'EURUSD')
            currencies = []
            if len(symbol) >= 6:
                base_currency = symbol[0:3]
                quote_currency = symbol[3:6]
                currencies = [base_currency, quote_currency]
            
            # Get calendar events
            if currencies:
                calendar_data = self.forex_factory_client.get_calendar(
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies
                )
                
                if not calendar_data.empty:
                    result['economic_events'] = pd.concat([result['economic_events'], calendar_data])
            
            # Get market sentiment
            if len(symbol) >= 6:
                # Format symbol for sentiment query (e.g., 'EUR/USD')
                formatted_symbol = f"{symbol[0:3]}/{symbol[3:6]}"
                sentiment_data = self.forex_factory_client.get_market_sentiment(formatted_symbol)
                
                if sentiment_data:
                    result['market_sentiment'].update({
                        'forex_factory': sentiment_data
                    })
                    
        except Exception as e:
            logger.error(f"Error retrieving Forex Factory data: {str(e)}")
    
    def _get_social_media_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from social media and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving social media data for {symbol}")
        
        try:
            # Calculate lookback days from start_date to end_date
            lookback_days = (end_date - start_date).days
            lookback_days = max(1, lookback_days)  # Ensure at least 1 day
            
            # Get sentiment data
            sentiment_data = self.social_media_client.get_sentiment(
                symbol=symbol,
                lookback_days=lookback_days
            )
            
            if sentiment_data:
                result['sentiment'].update({
                    'social_media': sentiment_data
                })
                
            # Get mentions history
            mentions_data = self.social_media_client.get_mentions_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not mentions_data.empty:
                result['sentiment']['mentions_history'] = mentions_data
                
        except Exception as e:
            logger.error(f"Error retrieving social media data: {str(e)}")
    
    def _aggregate_fundamental_data(self, result: Dict[str, Any]) -> None:
        """
        Aggregate fundamental data from multiple sources.
        
        Args:
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info("Aggregating fundamental data from multiple sources")
        
        # Deduplicate economic events
        if not result['economic_events'].empty:
            # Sort by date and importance
            result['economic_events'] = result['economic_events'].sort_values(
                by=['date', 'importance'],
                ascending=[True, False]
            )
            
            # Remove duplicates, keeping the first occurrence (highest importance)
            if 'event' in result['economic_events'].columns:
                result['economic_events'] = result['economic_events'].drop_duplicates(
                    subset=['date', 'event'],
                    keep='first'
                )
                
        # Aggregate sentiment data
        if result['sentiment'] and 'social_media' in result['sentiment']:
            # Calculate overall sentiment score (simplified example)
            social_sentiment = result['sentiment']['social_media']
            market_sentiment = result['market_sentiment'].get('forex_factory', {})
            
            # Only calculate if we have both sources
            if social_sentiment and market_sentiment:
                # Simple weighted average (adjust weights as needed)
                result['sentiment']['aggregated'] = {
                    'bullish': (social_sentiment.get('bullish', 0) * 0.7 + 
                               market_sentiment.get('bullish', 0) * 0.3),
                    'bearish': (social_sentiment.get('bearish', 0) * 0.7 + 
                               market_sentiment.get('bearish', 0) * 0.3),
                    'neutral': (social_sentiment.get('neutral', 0) * 0.7 + 
                               market_sentiment.get('neutral', 0) * 0.3)
                }
    
    def _verify_fundamental_data(self, result: Dict[str, Any]) -> None:
        """
        Verify fundamental data for consistency and quality.
        
        Args:
            result (Dict[str, Any]): Result dictionary to verify
        """
        logger.info("Verifying fundamental data quality")
        
        # Check if we have any data
        has_company_info = bool(result['company_info'])
        has_economic_events = not result['economic_events'].empty
        has_sentiment = bool(result['sentiment'])
        has_market_sentiment = bool(result['market_sentiment'])
        
        # Add data quality metrics
        result['source_metadata']['data_quality'] = {
            'has_company_info': has_company_info,
            'has_economic_events': has_economic_events,
            'has_sentiment': has_sentiment,
            'has_market_sentiment': has_market_sentiment,
            'completeness_score': sum([
                has_company_info,
                has_economic_events,
                has_sentiment,
                has_market_sentiment
            ]) / 4.0  # Simple completeness score
        }
        
        # Log data quality
        logger.info(f"Fundamental data quality score: {result['source_metadata']['data_quality']['completeness_score']:.2f}")
        
        # Add warnings for missing data
        warnings = []
        if not has_company_info:
            warnings.append("Company information is missing")
        if not has_economic_events:
            warnings.append("Economic events data is missing")
        if not has_sentiment:
            warnings.append("Sentiment data is missing")
        if not has_market_sentiment:
            warnings.append("Market sentiment data is missing")
            
        if warnings:
            result['source_metadata']['warnings'] = warnings
            logger.warning(f"Fundamental data warnings: {', '.join(warnings)}")
    
    def get_economic_calendar(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        currencies: Optional[List[str]] = None,
        importance: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve economic calendar events.
        
        Args:
            start_date (datetime): Start date
            end_date (Optional[datetime]): End date
            currencies (Optional[List[str]]): List of currencies to filter
            importance (Optional[str]): Event importance level
            
        Returns:
            pd.DataFrame: Economic calendar events
        """
        # TODO: Implement economic calendar retrieval
        # TODO: Add event filtering
        # TODO: Add event categorization
        # TODO: Add event impact analysis
        return pd.DataFrame()
    
    def get_sentiment_data(
        self,
        symbol: str,
        lookback_days: int = 7
    ) -> Dict[str, float]:
        """
        Retrieve market sentiment data.
        
        Args:
            symbol (str): Trading symbol
            lookback_days (int): Number of days to look back
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        # TODO: Implement sentiment data retrieval
        # TODO: Add sentiment analysis
        # TODO: Add sentiment aggregation
        # TODO: Add sentiment validation
        return {}
    
    def get_tick_data(
        self,
        symbol: str,
        num_ticks: int = 1000
    ) -> pd.DataFrame:
        """
        Retrieve latest tick data.
        
        Args:
            symbol (str): Trading symbol
            num_ticks (int): Number of ticks to retrieve
            
        Returns:
            pd.DataFrame: Tick data
        """
        # TODO: Implement tick data retrieval
        # TODO: Add tick validation
        # TODO: Add tick processing
        # TODO: Add tick aggregation
        return pd.DataFrame()
    
    def get_order_book(
        self,
        symbol: str,
        depth: int = 20
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieve order book data.
        
        Args:
            symbol (str): Trading symbol
            depth (int): Order book depth
            
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Bid and ask order books
        """
        # TODO: Implement order book retrieval
        # TODO: Add order book validation
        # TODO: Add order book analysis
        # TODO: Add order book visualization
        return pd.DataFrame(), pd.DataFrame()
    
    def subscribe_to_market_data(
        self,
        symbols: List[str],
        callback: Callable
    ) -> bool:
        """
        Subscribe to real-time market data.
        
        Args:
            symbols (List[str]): List of symbols
            callback (Callable): Callback function for data updates
            
        Returns:
            bool: True if subscription successful, False otherwise
        """
        # TODO: Implement market data subscription
        # TODO: Add subscription management
        # TODO: Add data streaming
        # TODO: Add connection monitoring
        return False
    
    def unsubscribe_from_market_data(
        self,
        symbols: Optional[List[str]] = None
    ) -> bool:
        """
        Unsubscribe from market data.
        
        Args:
            symbols (Optional[List[str]]): List of symbols to unsubscribe
            
        Returns:
            bool: True if unsubscription successful, False otherwise
        """
        # TODO: Implement market data unsubscription
        # TODO: Add subscription cleanup
        # TODO: Add connection cleanup
        return False 