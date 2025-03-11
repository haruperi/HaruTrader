"""
MetaTrader 5 client module.

This module provides a client for interacting with the MetaTrader 5 platform,
including connection management, market data retrieval, and trading operations.
"""
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any
import MetaTrader5 as mt5
from dotenv import load_dotenv

from ...config.settings import SYMBOLS_FOREX, SYMBOLS_COMMODITIES, SYMBOLS_INDICES
from ...utils.logger import get_logger
from ...utils.timeutils import convert_timeframe_to_mt5

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