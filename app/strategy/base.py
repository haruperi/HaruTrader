"""
Base strategy class for all trading strategies.

This module defines the abstract base class that all trading strategies must inherit from.
It provides common functionality and enforces a consistent interface for strategy implementation.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime

from ..utils.logger import get_logger
from ..core.mt5_data import MarketData
from ..trader.trade import Order, Position

logger = get_logger(__name__)

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all strategy implementations must follow.
    It provides common functionality for strategy initialization, execution, and management.
    """
    
    def __init__(
        self,
        name: str,
        symbols: List[str],
        timeframes: List[str],
        parameters: Dict[str, Any] = None,
        risk_per_trade: float = 0.01,  # 1% risk per trade by default
        max_open_positions: int = 5,
        max_open_positions_per_symbol: int = 1
    ):
        """
        Initialize a new strategy instance.
        
        Args:
            name (str): Strategy name
            symbols (List[str]): List of symbols to trade
            timeframes (List[str]): List of timeframes to analyze
            parameters (Dict[str, Any], optional): Strategy-specific parameters
            risk_per_trade (float, optional): Risk per trade as a fraction of account balance
            max_open_positions (int, optional): Maximum number of open positions allowed
            max_open_positions_per_symbol (int, optional): Maximum number of open positions per symbol
        """
        self.name = name
        self.symbols = symbols
        self.timeframes = timeframes
        self.parameters = parameters or {}
        self.risk_per_trade = risk_per_trade
        self.max_open_positions = max_open_positions
        self.max_open_positions_per_symbol = max_open_positions_per_symbol
        
        # Initialize strategy state
        self.is_active = False
        self.last_update_time = None
        self.market_data = {}  # Dict to store market data for each symbol and timeframe
        self.positions = {}  # Dict to store open positions
        self.pending_orders = {}  # Dict to store pending orders
        
        # Initialize performance metrics
        self.performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'max_drawdown': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'risk_reward_ratio': 0.0
        }
        
        logger.info(f"Initialized strategy: {self.name} for symbols: {', '.join(self.symbols)}")
    
    def activate(self) -> bool:
        """
        Activate the strategy for trading.
        
        Returns:
            bool: True if activation was successful, False otherwise
        """
        try:
            # Perform any necessary initialization before activating
            self._initialize()
            
            self.is_active = True
            logger.info(f"Strategy {self.name} activated")
            return True
        except Exception as e:
            logger.exception(f"Failed to activate strategy {self.name}: {str(e)}")
            return False
    
    def deactivate(self) -> bool:
        """
        Deactivate the strategy.
        
        Returns:
            bool: True if deactivation was successful, False otherwise
        """
        try:
            self.is_active = False
            logger.info(f"Strategy {self.name} deactivated")
            return True
        except Exception as e:
            logger.exception(f"Failed to deactivate strategy {self.name}: {str(e)}")
            return False
    
    def update_market_data(
        self,
        symbol: str,
        timeframe: str,
        data: pd.DataFrame
    ) -> None:
        """
        Update market data for a specific symbol and timeframe.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe of the data
            data (pd.DataFrame): Market data as a DataFrame
        """
        if symbol not in self.symbols:
            logger.warning(f"Symbol {symbol} is not in the strategy's symbol list")
            return
            
        if timeframe not in self.timeframes:
            logger.warning(f"Timeframe {timeframe} is not in the strategy's timeframe list")
            return
            
        # Create nested dictionary structure if it doesn't exist
        if symbol not in self.market_data:
            self.market_data[symbol] = {}
            
        # Update the market data
        self.market_data[symbol][timeframe] = data
        
        # Update last update time
        self.last_update_time = datetime.now()
        
        logger.debug(f"Updated market data for {symbol} {timeframe}, shape: {data.shape}")
    
    def update_positions(self, positions: List[Position]) -> None:
        """
        Update the list of open positions.
        
        Args:
            positions (List[Position]): List of current open positions
        """
        # Clear existing positions
        self.positions = {}
        
        # Update with new positions
        for position in positions:
            if position.symbol not in self.positions:
                self.positions[position.symbol] = []
                
            self.positions[position.symbol].append(position)
            
        logger.debug(f"Updated positions for strategy {self.name}, total positions: {sum(len(pos) for pos in self.positions.values())}")
    
    def update_pending_orders(self, orders: List[Order]) -> None:
        """
        Update the list of pending orders.
        
        Args:
            orders (List[Order]): List of current pending orders
        """
        # Clear existing pending orders
        self.pending_orders = {}
        
        # Update with new pending orders
        for order in orders:
            if order.symbol not in self.pending_orders:
                self.pending_orders[order.symbol] = []
                
            self.pending_orders[order.symbol].append(order)
            
        logger.debug(f"Updated pending orders for strategy {self.name}, total orders: {sum(len(orders) for orders in self.pending_orders.values())}")
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the strategy and generate trading signals.
        
        Returns:
            List[Dict[str, Any]]: List of trading signals
        """
        if not self.is_active:
            logger.warning(f"Strategy {self.name} is not active, skipping execution")
            return []
            
        signals = []
        
        try:
            # Check if we have enough market data
            if not self._validate_market_data():
                logger.warning(f"Insufficient market data for strategy {self.name}, skipping execution")
                return []
                
            # Generate signals for each symbol
            for symbol in self.symbols:
                # Skip if we've reached the maximum number of open positions
                if self._check_position_limits():
                    logger.info(f"Maximum number of open positions reached for strategy {self.name}")
                    break
                    
                # Skip if we've reached the maximum number of open positions for this symbol
                if self._check_symbol_position_limits(symbol):
                    logger.info(f"Maximum number of open positions reached for symbol {symbol}")
                    continue
                    
                # Generate signals for this symbol
                symbol_signals = self._generate_signals(symbol)
                
                if symbol_signals:
                    signals.extend(symbol_signals)
            
            # Log the number of signals generated
            if signals:
                logger.info(f"Strategy {self.name} generated {len(signals)} trading signals")
            else:
                logger.debug(f"Strategy {self.name} did not generate any trading signals")
                
            return signals
            
        except Exception as e:
            logger.exception(f"Error running strategy {self.name}: {str(e)}")
            return []
    
    def update_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Update strategy parameters.
        
        Args:
            parameters (Dict[str, Any]): New parameters
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Validate parameters
            if not self._validate_parameters(parameters):
                logger.warning(f"Invalid parameters for strategy {self.name}")
                return False
                
            # Update parameters
            self.parameters.update(parameters)
            
            logger.info(f"Updated parameters for strategy {self.name}: {parameters}")
            return True
            
        except Exception as e:
            logger.exception(f"Error updating parameters for strategy {self.name}: {str(e)}")
            return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get strategy performance metrics.
        
        Returns:
            Dict[str, Any]: Performance metrics
        """
        return self.performance
    
    def update_performance_metrics(self, closed_positions: List[Position]) -> None:
        """
        Update strategy performance metrics based on closed positions.
        
        Args:
            closed_positions (List[Position]): List of recently closed positions
        """
        if not closed_positions:
            return
            
        # Update total trades
        self.performance['total_trades'] += len(closed_positions)
        
        # Calculate profits and losses
        for position in closed_positions:
            if position.profit >= 0:
                self.performance['winning_trades'] += 1
                self.performance['total_profit'] += position.profit
            else:
                self.performance['losing_trades'] += 1
                self.performance['total_loss'] += abs(position.profit)
        
        # Calculate win rate
        if self.performance['total_trades'] > 0:
            self.performance['win_rate'] = self.performance['winning_trades'] / self.performance['total_trades']
            
        # Calculate profit factor
        if self.performance['total_loss'] > 0:
            self.performance['profit_factor'] = self.performance['total_profit'] / self.performance['total_loss']
            
        # Calculate average win and loss
        if self.performance['winning_trades'] > 0:
            self.performance['average_win'] = self.performance['total_profit'] / self.performance['winning_trades']
            
        if self.performance['losing_trades'] > 0:
            self.performance['average_loss'] = self.performance['total_loss'] / self.performance['losing_trades']
            
        # Calculate risk-reward ratio
        if self.performance['average_loss'] > 0:
            self.performance['risk_reward_ratio'] = self.performance['average_win'] / self.performance['average_loss']
            
        logger.info(f"Updated performance metrics for strategy {self.name}")
    
    def _initialize(self) -> None:
        """
        Initialize the strategy before activation.
        This method can be overridden by subclasses to perform custom initialization.
        """
        pass
    
    def _validate_market_data(self) -> bool:
        """
        Validate that we have sufficient market data for all symbols and timeframes.
        
        Returns:
            bool: True if we have sufficient data, False otherwise
        """
        for symbol in self.symbols:
            if symbol not in self.market_data:
                logger.warning(f"No market data for symbol {symbol}")
                return False
                
            for timeframe in self.timeframes:
                if timeframe not in self.market_data[symbol]:
                    logger.warning(f"No market data for symbol {symbol} and timeframe {timeframe}")
                    return False
                    
                # Check if we have enough data points
                min_data_points = self.parameters.get('min_data_points', 100)
                if len(self.market_data[symbol][timeframe]) < min_data_points:
                    logger.warning(f"Insufficient data points for symbol {symbol} and timeframe {timeframe}")
                    return False
                    
        return True
    
    def _check_position_limits(self) -> bool:
        """
        Check if we've reached the maximum number of open positions.
        
        Returns:
            bool: True if we've reached the limit, False otherwise
        """
        total_positions = sum(len(positions) for positions in self.positions.values())
        return total_positions >= self.max_open_positions
    
    def _check_symbol_position_limits(self, symbol: str) -> bool:
        """
        Check if we've reached the maximum number of open positions for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if we've reached the limit, False otherwise
        """
        if symbol not in self.positions:
            return False
            
        return len(self.positions[symbol]) >= self.max_open_positions_per_symbol
    
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.
        This method can be overridden by subclasses to perform custom validation.
        
        Args:
            parameters (Dict[str, Any]): Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        return True
    
    @abstractmethod
    def _generate_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a symbol.
        This method must be implemented by all strategy subclasses.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            List[Dict[str, Any]]: List of trading signals
        """
        pass 