"""
Risk management module.

This module provides functionality for managing risk in trading strategies.
"""
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime

from app.utils.logger import get_logger
from .indicators import Indicators

logger = get_logger(__name__)

class RiskManagement:
    """
    Risk management class for trading strategies.
    
    This class provides methods for calculating stop loss, take profit levels,
    and position sizing based on risk parameters.
    """
    
    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
        symbol_info: Dict[str, Any]
    ) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            account_balance (float): Account balance
            risk_per_trade (float): Risk per trade as a fraction of account balance
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            symbol_info (Dict[str, Any]): Symbol information including contract size, etc.
            
        Returns:
            float: Position size in lots
        """
        try:
            # Calculate risk amount in account currency
            risk_amount = account_balance * risk_per_trade
            
            # Calculate price difference between entry and stop loss
            price_diff = abs(entry_price - stop_loss_price)
            
            if price_diff == 0:
                logger.warning("Stop loss price is equal to entry price, cannot calculate position size")
                return 0.0
                
            # Get contract size and point value
            contract_size = symbol_info.get('contract_size', 100000)  # Default to 100,000 for forex
            point_value = symbol_info.get('point_value', 0.0001)  # Default to 0.0001 for forex
            
            # Calculate position size in lots
            position_size = risk_amount / (price_diff * contract_size)
            
            # Round to nearest lot step
            lot_step = symbol_info.get('lot_step', 0.01)
            position_size = round(position_size / lot_step) * lot_step
            
            # Apply minimum and maximum lot size constraints
            min_lot = symbol_info.get('min_lot', 0.01)
            max_lot = symbol_info.get('max_lot', 100.0)
            
            position_size = max(min_lot, min(position_size, max_lot))
            
            logger.info(f"Calculated position size: {position_size} lots (risk: {risk_amount:.2f}, price diff: {price_diff:.5f})")
            return position_size
            
        except Exception as e:
            logger.exception(f"Error calculating position size: {str(e)}")
            return 0.0
    
    @staticmethod
    def calculate_stop_loss(
        data: pd.DataFrame,
        entry_price: float,
        direction: str,
        method: str = 'fixed_pips',
        params: Dict[str, Any] = None
    ) -> float:
        """
        Calculate stop loss price based on various methods.
        
        Args:
            data (pd.DataFrame): Price data
            entry_price (float): Entry price
            direction (str): Trade direction ('buy' or 'sell')
            method (str, optional): Method to calculate stop loss
                Options: 'fixed_pips', 'percent', 'atr', 'swing_low_high', 'moving_average'
            params (Dict[str, Any], optional): Parameters for the selected method
            
        Returns:
            float: Stop loss price
        """
        try:
            # Default parameters
            params = params or {}
            
            # Validate direction
            if direction not in ['buy', 'sell']:
                logger.warning(f"Invalid direction: {direction}, must be 'buy' or 'sell'")
                return 0.0
                
            # Calculate stop loss based on method
            if method == 'fixed_pips':
                pips = params.get('pips', 50)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    stop_loss = entry_price - (pips * pip_value)
                else:  # sell
                    stop_loss = entry_price + (pips * pip_value)
                    
            elif method == 'percent':
                percent = params.get('percent', 1.0)  # Default to 1%
                
                if direction == 'buy':
                    stop_loss = entry_price * (1 - percent / 100)
                else:  # sell
                    stop_loss = entry_price * (1 + percent / 100)
                    
            elif method == 'atr':
                period = params.get('period', 14)
                multiplier = params.get('multiplier', 2.0)
                
                # Calculate ATR
                atr = Indicators.atr(data, period).iloc[-1]
                
                if direction == 'buy':
                    stop_loss = entry_price - (atr * multiplier)
                else:  # sell
                    stop_loss = entry_price + (atr * multiplier)
                    
            elif method == 'swing_low_high':
                lookback = params.get('lookback', 20)
                
                if direction == 'buy':
                    # Find recent swing low
                    stop_loss = data['Low'].iloc[-lookback:].min()
                else:  # sell
                    # Find recent swing high
                    stop_loss = data['High'].iloc[-lookback:].max()
                    
            elif method == 'moving_average':
                period = params.get('period', 50)
                ma_type = params.get('ma_type', 'sma')
                
                # Calculate moving average
                if ma_type == 'sma':
                    ma = Indicators.sma(data, period).iloc[-1]
                elif ma_type == 'ema':
                    ma = Indicators.ema(data, period).iloc[-1]
                else:
                    logger.warning(f"Invalid MA type: {ma_type}, using SMA")
                    ma = Indicators.sma(data, period).iloc[-1]
                    
                # Use MA as stop loss
                stop_loss = ma
                
            else:
                logger.warning(f"Invalid stop loss method: {method}, using fixed pips")
                pips = params.get('pips', 50)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    stop_loss = entry_price - (pips * pip_value)
                else:  # sell
                    stop_loss = entry_price + (pips * pip_value)
            
            logger.info(f"Calculated stop loss: {stop_loss:.5f} using method: {method}")
            return stop_loss
            
        except Exception as e:
            logger.exception(f"Error calculating stop loss: {str(e)}")
            return 0.0
    
    @staticmethod
    def calculate_take_profit(
        data: pd.DataFrame,
        entry_price: float,
        direction: str,
        method: str = 'risk_reward',
        params: Dict[str, Any] = None,
        stop_loss: float = None
    ) -> float:
        """
        Calculate take profit price based on various methods.
        
        Args:
            data (pd.DataFrame): Price data
            entry_price (float): Entry price
            direction (str): Trade direction ('buy' or 'sell')
            method (str, optional): Method to calculate take profit
                Options: 'fixed_pips', 'percent', 'risk_reward', 'fibonacci', 'pivot_points'
            params (Dict[str, Any], optional): Parameters for the selected method
            stop_loss (float, optional): Stop loss price (required for risk_reward method)
            
        Returns:
            float: Take profit price
        """
        try:
            # Default parameters
            params = params or {}
            
            # Validate direction
            if direction not in ['buy', 'sell']:
                logger.warning(f"Invalid direction: {direction}, must be 'buy' or 'sell'")
                return 0.0
                
            # Calculate take profit based on method
            if method == 'fixed_pips':
                pips = params.get('pips', 100)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    take_profit = entry_price + (pips * pip_value)
                else:  # sell
                    take_profit = entry_price - (pips * pip_value)
                    
            elif method == 'percent':
                percent = params.get('percent', 2.0)  # Default to 2%
                
                if direction == 'buy':
                    take_profit = entry_price * (1 + percent / 100)
                else:  # sell
                    take_profit = entry_price * (1 - percent / 100)
                    
            elif method == 'risk_reward':
                risk_reward_ratio = params.get('risk_reward_ratio', 2.0)
                
                if stop_loss is None:
                    logger.warning("Stop loss is required for risk_reward method")
                    return 0.0
                    
                # Calculate risk in price terms
                risk = abs(entry_price - stop_loss)
                
                # Calculate take profit based on risk-reward ratio
                if direction == 'buy':
                    take_profit = entry_price + (risk * risk_reward_ratio)
                else:  # sell
                    take_profit = entry_price - (risk * risk_reward_ratio)
                    
            elif method == 'fibonacci':
                level = params.get('level', 1.618)
                lookback = params.get('lookback', 100)
                
                # Calculate Fibonacci retracement/extension levels
                if direction == 'buy':
                    # Find recent swing low and high
                    swing_low = data['Low'].iloc[-lookback:].min()
                    swing_high = data['High'].iloc[-lookback:].max()
                    
                    # Calculate extension level
                    take_profit = swing_low + (swing_high - swing_low) * level
                else:  # sell
                    # Find recent swing low and high
                    swing_low = data['Low'].iloc[-lookback:].min()
                    swing_high = data['High'].iloc[-lookback:].max()
                    
                    # Calculate extension level
                    take_profit = swing_high - (swing_high - swing_low) * level
                    
            elif method == 'pivot_points':
                level = params.get('level', 'r2' if direction == 'buy' else 's2')
                
                # Calculate pivot points
                pivot_points = Indicators.pivot_points(data)
                
                # Use specified pivot level as take profit
                take_profit = pivot_points.get(level, entry_price)
                
            else:
                logger.warning(f"Invalid take profit method: {method}, using fixed pips")
                pips = params.get('pips', 100)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    take_profit = entry_price + (pips * pip_value)
                else:  # sell
                    take_profit = entry_price - (pips * pip_value)
            
            logger.info(f"Calculated take profit: {take_profit:.5f} using method: {method}")
            return take_profit
            
        except Exception as e:
            logger.exception(f"Error calculating take profit: {str(e)}")
            return 0.0
    
    @staticmethod
    def calculate_trailing_stop(
        data: pd.DataFrame,
        entry_price: float,
        current_price: float,
        direction: str,
        method: str = 'fixed_pips',
        params: Dict[str, Any] = None,
        current_stop: float = None
    ) -> float:
        """
        Calculate trailing stop price based on various methods.
        
        Args:
            data (pd.DataFrame): Price data
            entry_price (float): Entry price
            current_price (float): Current price
            direction (str): Trade direction ('buy' or 'sell')
            method (str, optional): Method to calculate trailing stop
                Options: 'fixed_pips', 'percent', 'atr', 'chandelier', 'parabolic_sar'
            params (Dict[str, Any], optional): Parameters for the selected method
            current_stop (float, optional): Current stop loss price
            
        Returns:
            float: New trailing stop price
        """
        try:
            # Default parameters
            params = params or {}
            
            # Validate direction
            if direction not in ['buy', 'sell']:
                logger.warning(f"Invalid direction: {direction}, must be 'buy' or 'sell'")
                return 0.0
                
            # Initialize new stop to current stop
            new_stop = current_stop or (entry_price - 0.01 if direction == 'buy' else entry_price + 0.01)
            
            # Calculate trailing stop based on method
            if method == 'fixed_pips':
                pips = params.get('pips', 50)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    calculated_stop = current_price - (pips * pip_value)
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    calculated_stop = current_price + (pips * pip_value)
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
                    
            elif method == 'percent':
                percent = params.get('percent', 1.0)  # Default to 1%
                
                if direction == 'buy':
                    calculated_stop = current_price * (1 - percent / 100)
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    calculated_stop = current_price * (1 + percent / 100)
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
                    
            elif method == 'atr':
                period = params.get('period', 14)
                multiplier = params.get('multiplier', 2.0)
                
                # Calculate ATR
                atr = Indicators.atr(data, period).iloc[-1]
                
                if direction == 'buy':
                    calculated_stop = current_price - (atr * multiplier)
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    calculated_stop = current_price + (atr * multiplier)
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
                    
            elif method == 'chandelier':
                period = params.get('period', 22)
                multiplier = params.get('multiplier', 3.0)
                
                # Calculate ATR
                atr = Indicators.atr(data, period).iloc[-1]
                
                # Calculate highest high or lowest low
                if direction == 'buy':
                    highest_high = data['High'].iloc[-period:].max()
                    calculated_stop = highest_high - (atr * multiplier)
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    lowest_low = data['Low'].iloc[-period:].min()
                    calculated_stop = lowest_low + (atr * multiplier)
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
                    
            elif method == 'parabolic_sar':
                # Use the last value of Parabolic SAR as trailing stop
                # This is a simplified implementation
                acceleration = params.get('acceleration', 0.02)
                max_acceleration = params.get('max_acceleration', 0.2)
                
                # In a real implementation, you would calculate Parabolic SAR
                # Here we're just using a placeholder
                if direction == 'buy':
                    calculated_stop = current_price - (current_price - entry_price) * acceleration
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    calculated_stop = current_price + (entry_price - current_price) * acceleration
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
                    
            else:
                logger.warning(f"Invalid trailing stop method: {method}, using fixed pips")
                pips = params.get('pips', 50)
                pip_value = params.get('pip_value', 0.0001)
                
                if direction == 'buy':
                    calculated_stop = current_price - (pips * pip_value)
                    # Only move stop up, never down
                    new_stop = max(new_stop, calculated_stop)
                else:  # sell
                    calculated_stop = current_price + (pips * pip_value)
                    # Only move stop down, never up
                    new_stop = min(new_stop, calculated_stop) if new_stop > 0 else calculated_stop
            
            logger.info(f"Calculated trailing stop: {new_stop:.5f} using method: {method}")
            return new_stop
            
        except Exception as e:
            logger.exception(f"Error calculating trailing stop: {str(e)}")
            return current_stop or 0.0
    
    @staticmethod
    def validate_risk_parameters(
        account_balance: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
        position_size: float,
        symbol_info: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate risk parameters to ensure they meet risk management criteria.
        
        Args:
            account_balance (float): Account balance
            risk_per_trade (float): Risk per trade as a fraction of account balance
            entry_price (float): Entry price
            stop_loss_price (float): Stop loss price
            position_size (float): Position size in lots
            symbol_info (Dict[str, Any]): Symbol information
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        try:
            # Check if risk per trade is within acceptable limits
            max_risk_per_trade = 0.02  # Maximum 2% risk per trade
            if risk_per_trade > max_risk_per_trade:
                return False, f"Risk per trade ({risk_per_trade:.2%}) exceeds maximum allowed ({max_risk_per_trade:.2%})"
                
            # Check if stop loss is too close to entry price
            min_stop_distance = symbol_info.get('min_stop_distance', 0.0001)
            stop_distance = abs(entry_price - stop_loss_price)
            
            if stop_distance < min_stop_distance:
                return False, f"Stop loss is too close to entry price (distance: {stop_distance:.5f}, minimum: {min_stop_distance:.5f})"
                
            # Calculate actual risk amount
            contract_size = symbol_info.get('contract_size', 100000)
            risk_amount = stop_distance * position_size * contract_size
            
            # Check if risk amount is within acceptable limits
            max_risk_amount = account_balance * max_risk_per_trade
            if risk_amount > max_risk_amount:
                return False, f"Risk amount ({risk_amount:.2f}) exceeds maximum allowed ({max_risk_amount:.2f})"
                
            # Check if position size is within symbol limits
            min_lot = symbol_info.get('min_lot', 0.01)
            max_lot = symbol_info.get('max_lot', 100.0)
            
            if position_size < min_lot:
                return False, f"Position size ({position_size:.2f} lots) is below minimum allowed ({min_lot:.2f} lots)"
                
            if position_size > max_lot:
                return False, f"Position size ({position_size:.2f} lots) exceeds maximum allowed ({max_lot:.2f} lots)"
                
            # All checks passed
            return True, "Risk parameters are valid"
            
        except Exception as e:
            logger.exception(f"Error validating risk parameters: {str(e)}")
            return False, f"Error validating risk parameters: {str(e)}" 