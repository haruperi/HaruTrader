"""
Trend Following Strategy.

This module implements a trend following strategy based on moving averages and ADX.
"""
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime

from app.strategy.base import Strategy
from app.strategy.indicators import Indicators
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TrendFollowingStrategy(Strategy):
    """
    Trend Following Strategy implementation.
    
    This strategy uses moving averages and other trend indicators to identify
    and follow market trends.
    """
    
    def __init__(
        self,
        name: str,
        symbols: List[str],
        timeframes: List[str],
        parameters: Dict[str, Any] = None,
        risk_per_trade: float = 0.01,
        max_open_positions: int = 5,
        max_open_positions_per_symbol: int = 1
    ):
        """
        Initialize a new trend following strategy.
        
        Args:
            name (str): Strategy name
            symbols (List[str]): List of symbols to trade
            timeframes (List[str]): List of timeframes to analyze
            parameters (Dict[str, Any], optional): Strategy-specific parameters
            risk_per_trade (float, optional): Risk per trade as a fraction of account balance
            max_open_positions (int, optional): Maximum number of open positions allowed
            max_open_positions_per_symbol (int, optional): Maximum number of open positions per symbol
        """
        # Default parameters
        default_params = {
            'fast_ma_period': 20,
            'slow_ma_period': 50,
            'signal_ma_period': 9,
            'adx_period': 14,
            'adx_threshold': 25,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'stop_loss_method': 'atr',
            'stop_loss_atr_multiplier': 2.0,
            'take_profit_method': 'risk_reward',
            'take_profit_risk_reward_ratio': 2.0,
            'trailing_stop_method': 'atr',
            'trailing_stop_atr_multiplier': 1.5,
            'entry_timeframe': 'H4',
            'confirmation_timeframe': 'D1'
        }
        
        # Merge default parameters with provided parameters
        if parameters:
            merged_params = default_params.copy()
            merged_params.update(parameters)
            parameters = merged_params
        else:
            parameters = default_params
            
        # Initialize base strategy
        super().__init__(
            name=name,
            symbols=symbols,
            timeframes=timeframes,
            parameters=parameters,
            risk_per_trade=risk_per_trade,
            max_open_positions=max_open_positions,
            max_open_positions_per_symbol=max_open_positions_per_symbol
        )
        
        logger.info(f"Initialized Trend Following Strategy: {name}")
        
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
        logger.info(f"Initialized Trend Following Strategy: {self.name}")
        
    def _validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        Validate strategy parameters.
        
        Args:
            parameters (Dict[str, Any]): Parameters to validate
            
        Returns:
            bool: True if parameters are valid, False otherwise
        """
        # Validate MA periods
        if 'fast_ma_period' in parameters and 'slow_ma_period' in parameters:
            if parameters['fast_ma_period'] >= parameters['slow_ma_period']:
                logger.warning("Fast MA period must be less than slow MA period")
                return False
                
        # Validate ADX threshold
        if 'adx_threshold' in parameters:
            if parameters['adx_threshold'] < 0 or parameters['adx_threshold'] > 100:
                logger.warning("ADX threshold must be between 0 and 100")
                return False
                
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
                
        # Validate stop loss and take profit methods
        valid_sl_methods = ['fixed_pips', 'percent', 'atr', 'swing_low_high', 'moving_average']
        if 'stop_loss_method' in parameters:
            if parameters['stop_loss_method'] not in valid_sl_methods:
                logger.warning(f"Invalid stop loss method: {parameters['stop_loss_method']}")
                return False
                
        valid_tp_methods = ['fixed_pips', 'percent', 'risk_reward', 'fibonacci', 'pivot_points']
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
            fast_ma_period = self.parameters['fast_ma_period']
            slow_ma_period = self.parameters['slow_ma_period']
            adx_period = self.parameters['adx_period']
            adx_threshold = self.parameters['adx_threshold']
            
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
            fast_ma = Indicators.ema(entry_data, fast_ma_period)
            slow_ma = Indicators.ema(entry_data, slow_ma_period)
            adx = Indicators.adx(entry_data, adx_period)
            
            # Calculate indicators for confirmation timeframe
            confirmation_ma = Indicators.ema(confirmation_data, slow_ma_period)
            
            # Check for buy signal
            buy_signal = (
                # Fast MA crosses above Slow MA
                fast_ma.iloc[-2] <= slow_ma.iloc[-2] and
                fast_ma.iloc[-1] > slow_ma.iloc[-1] and
                # Strong trend
                adx.iloc[-1] > adx_threshold and
                # Confirmation: Price above MA on higher timeframe
                confirmation_data['Close'].iloc[-1] > confirmation_ma.iloc[-1]
            )
            
            # Check for sell signal
            sell_signal = (
                # Fast MA crosses below Slow MA
                fast_ma.iloc[-2] >= slow_ma.iloc[-2] and
                fast_ma.iloc[-1] < slow_ma.iloc[-1] and
                # Strong trend
                adx.iloc[-1] > adx_threshold and
                # Confirmation: Price below MA on higher timeframe
                confirmation_data['Close'].iloc[-1] < confirmation_ma.iloc[-1]
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
                    'signal_type': 'trend_following',
                    'reason': 'Fast MA crossed above Slow MA with strong trend'
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
                    'signal_type': 'trend_following',
                    'reason': 'Fast MA crossed below Slow MA with strong trend'
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
            atr_multiplier = self.parameters.get('stop_loss_atr_multiplier', 2.0)
            
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
            
            stop_loss = ma
            
        else:
            # Default to ATR method
            logger.warning(f"Invalid stop loss method: {method}, using ATR")
            
            atr_period = self.parameters.get('atr_period', 14)
            atr_multiplier = self.parameters.get('stop_loss_atr_multiplier', 2.0)
            
            atr = Indicators.atr(data, atr_period).iloc[-1]
            
            if direction == 'buy':
                stop_loss = entry_price - (atr * atr_multiplier)
            else:  # sell
                stop_loss = entry_price + (atr * atr_multiplier)
                
        logger.debug(f"Calculated stop loss for {symbol} {direction}: {stop_loss:.5f}")
        return stop_loss
        
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
        
        if method == 'risk_reward':
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
                
        elif method == 'pivot_points':
            # Use pivot points
            level = self.parameters.get('take_profit_pivot_level', 'r2' if direction == 'buy' else 's2')
            
            # Calculate pivot points
            pivot_points = Indicators.pivot_points(data)
            
            # Use specified pivot level as take profit
            take_profit = pivot_points.get(level, entry_price)
            
        else:
            # Default to risk-reward method
            logger.warning(f"Invalid take profit method: {method}, using risk-reward")
            
            risk_reward_ratio = self.parameters.get('take_profit_risk_reward_ratio', 2.0)
            
            # Calculate risk in price terms
            risk = abs(entry_price - stop_loss_price)
            
            if direction == 'buy':
                take_profit = entry_price + (risk * risk_reward_ratio)
            else:  # sell
                take_profit = entry_price - (risk * risk_reward_ratio)
                
        logger.debug(f"Calculated take profit for {symbol} {direction}: {take_profit:.5f}")
        return take_profit 