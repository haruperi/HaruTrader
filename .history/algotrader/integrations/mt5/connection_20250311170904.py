"""
MetaTrader 5 connection module.

This module provides functionality to connect to MetaTrader 5 terminal
and manage the connection lifecycle.
"""
import os
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
import MetaTrader5 as mt5
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class MT5Connection:
    """
    MetaTrader 5 connection manager.
    
    This class handles the connection to the MetaTrader 5 terminal,
    authentication, and provides methods to check connection status.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the MT5 connection manager.
        
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