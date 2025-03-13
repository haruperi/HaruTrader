"""
Mean Reversion Strategy implementation.

This module implements a mean reversion strategy that identifies overbought
and oversold conditions to generate trading signals.
"""
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime

from ..base import Strategy
from ..indicators import Indicators
from ...utils.logger import get_logger

logger = get_logger(__name__)

class MeanReversionStrategy(Strategy):
    """
    Mean Reversion Strategy implementation.
    
    This strategy identifies overbought and oversold conditions using
    oscillators and other indicators to generate counter-trend trading signals.
    """
    
    def __init__(
        self,
        name: str,
        symbols: List[str],
        timeframes: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        risk_per_trade: float = 0.01,
        max_open_positions: int = 5,
        max_open_positions_per_symbol: int = 1
    ):
        """
        Initialize a new mean reversion strategy.
        
        Args:
            name (str): Strategy name
            symbols (List[str]): List of symbols to trade
            timeframes (List[str]): List of timeframes to analyze
            parameters (Optional[Dict[str, Any]], optional): Strategy-specific parameters
            risk_per_trade (float, optional): Risk per trade as a fraction of account balance
            max_open_positions (int, optional): Maximum number of open positions allowed
            max_open_positions_per_symbol (int, optional): Maximum number of open positions per symbol
        """
        # Default parameters
        default_params: Dict[str, Any] = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'bb_period': 20,
            'bb_std_dev': 2.0,
            'stoch_k_period': 14,
            'stoch_d_period': 3,
            'stoch_overbought': 80,
            'stoch_oversold': 20,
            'atr_period': 14,
            'stop_loss_method': 'atr',
            'stop_loss_atr_multiplier': 1.5,
            'take_profit_method': 'atr',
            'take_profit_atr_multiplier': 2.0,
            'entry_timeframe': 'H4',
            'confirmation_timeframe': 'D1'
        }
        
        # Merge default parameters with provided parameters
        merged_params = default_params.copy()
        if parameters:
            merged_params.update(parameters)
            
        # Initialize base strategy
        super().__init__(
            name=name,
            symbols=symbols,
            timeframes=timeframes,
            parameters=merged_params,
            risk_per_trade=risk_per_trade,
            max_open_positions=max_open_positions,
            max_open_positions_per_symbol=max_open_positions_per_symbol
        )
        
        logger.info(f"Initialized Mean Reversion Strategy: {name}")
        
    def _initialize(self) -> None:
        """
        Initialize the strategy before activation.
        """
        # Validate required timeframes
        required_timeframes = [
            self.parameters['entry_timeframe'],
            self.parameters['confirmation_timeframe']
        ]
        
        for timeframe in required_timeframes:
            if timeframe not in self.timeframes:
                logger.warning(f"Required timeframe {timeframe} not in strategy timeframes")
                
        # Additional initialization if needed
        logger.info(f"Initialized Mean Reversion Strategy: {self.name}")
        
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.
        
        Args:
            parameters (Dict[str, Any]): Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        # Validate RSI thresholds
        if 'rsi_overbought' in parameters and 'rsi_oversold' in parameters:
            if parameters['rsi_oversold'] >= parameters['rsi_overbought']:
                logger.warning("RSI oversold must be less than RSI overbought")
                return False
                
            if parameters['rsi_oversold'] < 0 or parameters['rsi_oversold'] > 100:
                logger.warning("RSI oversold must be between 0 and 100")
                return False
                
            if parameters['rsi_overbought'] < 0 or parameters['rsi_overbought'] > 100:
                logger.warning("RSI overbought must be between 0 and 100")
                return False
                
        # Validate Stochastic thresholds
        if 'stoch_overbought' in parameters and 'stoch_oversold' in parameters:
            if parameters['stoch_oversold'] >= parameters['stoch_overbought']:
                logger.warning("Stochastic oversold must be less than Stochastic overbought")
                return False
                
            if parameters['stoch_oversold'] < 0 or parameters['stoch_oversold'] > 100:
                logger.warning("Stochastic oversold must be between 0 and 100")
                return False
                
            if parameters['stoch_overbought'] < 0 or parameters['stoch_overbought'] > 100:
                logger.warning("Stochastic overbought must be between 0 and 100")
                return False
                
        # Validate Bollinger Bands parameters
        if 'bb_period' in parameters:
            if parameters['bb_period'] < 2:
                logger.warning("Bollinger Bands period must be at least 2")
                return False
                
        if 'bb_std_dev' in parameters:
            if parameters['bb_std_dev'] <= 0:
                logger.warning("Bollinger Bands standard deviation must be positive")
                return False
                
        # Validate stop loss and take profit methods
        valid_sl_methods = ['fixed_pips', 'percent', 'atr', 'swing_low_high', 'moving_average']
        if 'stop_loss_method' in parameters:
            if parameters['stop_loss_method'] not in valid_sl_methods:
                logger.warning(f"Invalid stop loss method: {parameters['stop_loss_method']}")
                return False
                
        valid_tp_methods = ['fixed_pips', 'percent', 'atr', 'risk_reward', 'fibonacci']
        if 'take_profit_method' in parameters:
            if parameters['take_profit_method'] not in valid_tp_methods:
                logger.warning(f"Invalid take profit method: {parameters['take_profit_method']}")
                return False
                
        # All checks passed
        return True
        
    def _generate_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            List[Dict[str, Any]]: List of trading signals
        """
        signals = []
        
        try:
            # Get parameters
            entry_timeframe = self.parameters['entry_timeframe']
            confirmation_timeframe = self.parameters['confirmation_timeframe']
            rsi_period = self.parameters['rsi_period']
            rsi_overbought = self.parameters['rsi_overbought']
            rsi_oversold = self.parameters['rsi_oversold']
            bb_period = self.parameters['bb_period']
            bb_std_dev = self.parameters['bb_std_dev']
            stoch_k_period = self.parameters['stoch_k_period']
            stoch_d_period = self.parameters['stoch_d_period']
            stoch_overbought = self.parameters['stoch_overbought']
            stoch_oversold = self.parameters['stoch_oversold']
            
            # Check if we have data for required timeframes
            if entry_timeframe not in self.market_data.get(symbol, {}):
                logger.warning(f"No data for {symbol} on entry timeframe {entry_timeframe}")
                return signals
                
            if confirmation_timeframe not in self.market_data.get(symbol, {}):
                logger.warning(f"No data for {symbol} on confirmation timeframe {confirmation_timeframe}")
                return signals
                
            # Get market data
            entry_data = self.market_data[symbol][entry_timeframe]
            confirmation_data = self.market_data[symbol][confirmation_timeframe]
            
            # Calculate indicators for entry timeframe
            rsi = Indicators.rsi(entry_data, rsi_period)
            bb_upper, bb_middle, bb_lower = Indicators.bollinger_bands(entry_data, bb_period, bb_std_dev)
            stoch_k, stoch_d = Indicators.stochastic(entry_data, stoch_k_period, stoch_d_period)
            
            # Calculate indicators for confirmation timeframe
            confirmation_rsi = Indicators.rsi(confirmation_data, rsi_period)
            
            # Check for buy signal (oversold conditions)
            buy_signal = (
                # RSI is oversold
                rsi.iloc[-1] < rsi_oversold and
                # Price is below lower Bollinger Band
                entry_data['Close'].iloc[-1] < bb_lower.iloc[-1] and
                # Stochastic is oversold
                stoch_k.iloc[-1] < stoch_oversold and
                stoch_d.iloc[-1] < stoch_oversold and
                # Confirmation: RSI is also oversold on higher timeframe
                confirmation_rsi.iloc[-1] < rsi_oversold
            )
            
            # Check for sell signal (overbought conditions)
            sell_signal = (
                # RSI is overbought
                rsi.iloc[-1] > rsi_overbought and
                # Price is above upper Bollinger Band
                entry_data['Close'].iloc[-1] > bb_upper.iloc[-1] and
                # Stochastic is overbought
                stoch_k.iloc[-1] > stoch_overbought and
                stoch_d.iloc[-1] > stoch_overbought and
                # Confirmation: RSI is also overbought on higher timeframe
                confirmation_rsi.iloc[-1] > rsi_overbought
            )
            
            # Generate signals
            current_price = entry_data['Close'].iloc[-1]
            current_time = entry_data.index[-1]
            
            if buy_signal:
                # Calculate stop loss and take profit levels
                stop_loss_price = self._calculate_stop_loss(symbol, entry_data, current_price, 'buy')
                take_profit_price = self._calculate_take_profit(symbol, entry_data, current_price, 'buy', stop_loss_price)
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'buy',
                    'entry_price': current_price,
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price,
                    'time': current_time,
                    'timeframe': entry_timeframe,
                    'strategy': self.name,
                    'signal_type': 'mean_reversion',
                    'reason': 'Oversold conditions detected'
                })
                
                logger.info(f"Generated BUY signal for {symbol} at {current_price}")
                
            elif sell_signal:
                # Calculate stop loss and take profit levels
                stop_loss_price = self._calculate_stop_loss(symbol, entry_data, current_price, 'sell')
                take_profit_price = self._calculate_take_profit(symbol, entry_data, current_price, 'sell', stop_loss_price)
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'sell',
                    'entry_price': current_price,
                    'stop_loss': stop_loss_price,
                    'take_profit': take_profit_price,
                    'time': current_time,
                    'timeframe': entry_timeframe,
                    'strategy': self.name,
                    'signal_type': 'mean_reversion',
                    'reason': 'Overbought conditions detected'
                })
                
                logger.info(f"Generated SELL signal for {symbol} at {current_price}")
                
            return signals
            
        except Exception as e:
            logger.exception(f"Error generating signals for {symbol}: {str(e)}")
            return []
            
    def _calculate_stop_loss(
        self,
        symbol: str,
        data: pd.DataFrame,
        entry_price: float,
        direction: str
    ) -> float:
        """
        Calculate stop loss price.
        
        Args:
            symbol (str): Trading symbol
            data (pd.DataFrame): Market data
            entry_price (float): Entry price
            direction (str): Trade direction ('buy' or 'sell')
            
        Returns:
            float: Stop loss price
        """
        method = self.parameters['stop_loss_method']
        
        if method == 'atr':
            # Calculate ATR
            atr_period = self.parameters.get('atr_period', 14)
            atr_multiplier = self.parameters.get('stop_loss_atr_multiplier', 1.5)
            
            atr = Indicators.atr(data, atr_period).iloc[-1]
            
            if direction == 'buy':
                stop_loss = entry_price - (atr * atr_multiplier)
            else:  # sell
                stop_loss = entry_price + (atr * atr_multiplier)
                
        elif method == 'swing_low_high':
            # Use recent swing low/high
            lookback = self.parameters.get('swing_lookback', 20)
            
            if direction == 'buy':
                stop_loss = data['Low'].iloc[-lookback:].min()
            else:  # sell
                stop_loss = data['High'].iloc[-lookback:].max()
                
        elif method == 'percent':
            # Use percentage of entry price
            percent = self.parameters.get('stop_loss_percent', 1.0)
            
            if direction == 'buy':
                stop_loss = entry_price * (1 - percent / 100)
            else:  # sell
                stop_loss = entry_price * (1 + percent / 100)
                
        elif method == 'fixed_pips':
            # Use fixed number of pips
            pips = self.parameters.get('stop_loss_pips', 50)
            pip_value = self.parameters.get('pip_value', 0.0001)
            
            if direction == 'buy':
                stop_loss = entry_price - (pips * pip_value)
            else:  # sell
                stop_loss = entry_price + (pips * pip_value)
                
        elif method == 'moving_average':
            # Use moving average as stop loss
            ma_period = self.parameters.get('stop_loss_ma_period', 50)
            ma = Indicators.ema(data, ma_period).iloc[-1]
            
            # Convert to float to avoid linter errors
            stop_loss = float(ma)
                
        else:
            # Default to ATR method
            logger.warning(f"Invalid stop loss method: {method}, using ATR")
            
            atr_period = self.parameters.get('atr_period', 14)
            atr_multiplier = self.parameters.get('stop_loss_atr_multiplier', 1.5)
            
            atr = Indicators.atr(data, atr_period).iloc[-1]
            
            if direction == 'buy':
                stop_loss = entry_price - (atr * atr_multiplier)
            else:  # sell
                stop_loss = entry_price + (atr * atr_multiplier)
                
        logger.debug(f"Calculated stop loss for {symbol} {direction}: {stop_loss:.5f}")
        return float(stop_loss)  # Convert to float to avoid linter errors
        
    def _calculate_take_profit(
        self,
        symbol: str,
        data: pd.DataFrame,
        entry_price: float,
        direction: str,
        stop_loss_price: float
    ) -> float:
        """
        Calculate take profit price.
        
        Args:
            symbol (str): Trading symbol
            data (pd.DataFrame): Market data
            entry_price (float): Entry price
            direction (str): Trade direction ('buy' or 'sell')
            stop_loss_price (float): Stop loss price
            
        Returns:
            float: Take profit price
        """
        method = self.parameters['take_profit_method']
        
        if method == 'atr':
            # Calculate ATR
            atr_period = self.parameters.get('atr_period', 14)
            atr_multiplier = self.parameters.get('take_profit_atr_multiplier', 2.0)
            
            atr = Indicators.atr(data, atr_period).iloc[-1]
            
            if direction == 'buy':
                take_profit = entry_price + (atr * atr_multiplier)
            else:  # sell
                take_profit = entry_price - (atr * atr_multiplier)
                
        elif method == 'risk_reward':
            # Use risk-reward ratio
            risk_reward_ratio = self.parameters.get('take_profit_risk_reward_ratio', 2.0)
            
            # Calculate risk in price terms
            risk = abs(entry_price - stop_loss_price)
            
            if direction == 'buy':
                take_profit = entry_price + (risk * risk_reward_ratio)
            else:  # sell
                take_profit = entry_price - (risk * risk_reward_ratio)
                
        elif method == 'fibonacci':
            # Use Fibonacci extension
            level = self.parameters.get('take_profit_fib_level', 1.618)
            lookback = self.parameters.get('fib_lookback', 100)
            
            # Find recent swing low and high
            swing_low = data['Low'].iloc[-lookback:].min()
            swing_high = data['High'].iloc[-lookback:].max()
            
            if direction == 'buy':
                take_profit = entry_price + (swing_high - swing_low) * level
            else:  # sell
                take_profit = entry_price - (swing_high - swing_low) * level
                
        elif method == 'percent':
            # Use percentage of entry price
            percent = self.parameters.get('take_profit_percent', 2.0)
            
            if direction == 'buy':
                take_profit = entry_price * (1 + percent / 100)
            else:  # sell
                take_profit = entry_price * (1 - percent / 100)
                
        elif method == 'fixed_pips':
            # Use fixed number of pips
            pips = self.parameters.get('take_profit_pips', 100)
            pip_value = self.parameters.get('pip_value', 0.0001)
            
            if direction == 'buy':
                take_profit = entry_price + (pips * pip_value)
            else:  # sell
                take_profit = entry_price - (pips * pip_value)
                
        else:
            # Default to ATR method
            logger.warning(f"Invalid take profit method: {method}, using ATR")
            
            atr_period = self.parameters.get('atr_period', 14)
            atr_multiplier = self.parameters.get('take_profit_atr_multiplier', 2.0)
            
            atr = Indicators.atr(data, atr_period).iloc[-1]
            
            if direction == 'buy':
                take_profit = entry_price + (atr * atr_multiplier)
            else:  # sell
                take_profit = entry_price - (atr * atr_multiplier)
                
        logger.debug(f"Calculated take profit for {symbol} {direction}: {take_profit:.5f}")
        return float(take_profit)  # Convert to float to avoid linter errors 