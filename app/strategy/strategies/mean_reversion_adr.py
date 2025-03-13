import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List, Union
from datetime import datetime, timedelta

from app.strategy.base import Strategy
from app.strategy.indicators import Indicators
from app.utils import get_logger

logger = get_logger(__name__)

class MeanReversionADRStrategy(Strategy):
    """
    Mean Reversion strategy based on Average Daily Range (ADR).
    
    This strategy identifies potential reversal points when price has moved significantly
    in one direction within a single day, exceeding a certain percentage of the Average Daily Range.
    
    Strategy Logic:
    1. Calculate the Average Daily Range (ADR) over a specified period
    2. Calculate the current day's range as a percentage of the ADR
    3. If the current range exceeds the threshold and RSI confirms overbought/oversold:
       - For BUY: Price has moved down significantly (exceeding threshold) and RSI is oversold
       - For SELL: Price has moved up significantly (exceeding threshold) and RSI is overbought
    4. Place trades with stop loss based on ADR and take profit at a multiple of the risk
    
    Parameters:
    - adr_period: Number of days to calculate ADR
    - range_threshold: Percentage of ADR that current range must exceed to trigger signal
    - rsi_period: Period for RSI calculation
    - rsi_overbought: RSI level considered overbought
    - rsi_oversold: RSI level considered oversold
    - risk_reward_ratio: Risk to reward ratio for take profit calculation
    - stop_loss_adr_multiplier: Multiplier of ADR for stop loss calculation
    - tick_size: Minimum price movement for the instrument
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the Mean Reversion ADR Strategy.
        
        Args:
            params (Dict[str, Any], optional): Strategy parameters
        """
        default_params = {
            'adr_period': 14,
            'range_threshold': 70,  # Percentage of ADR
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'risk_reward_ratio': 2.0,
            'stop_loss_adr_multiplier': 0.5,  # Half of ADR
            'tick_size': 0.00001,
            'use_williams_r': False,  # Option to use Williams %R instead of RSI
            'williams_period': 14,
            'williams_overbought': -20,
            'williams_oversold': -80
        }
        
        if params is None:
            params = {}
            
        # Merge default parameters with provided parameters
        self.params = {**default_params, **params}
        
        # Initialize base class
        super().__init__(name="MeanReversionADR", params=self.params)
        
        # Validate parameters
        self._validate_parameters()
        
        logger.info(f"Initialized {self.name} strategy with parameters: {self.params}")
    
    def _validate_parameters(self) -> None:
        """
        Validate strategy parameters.
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if self.params['adr_period'] < 1:
            raise ValueError(f"ADR period must be positive, got {self.params['adr_period']}")
        
        if not (0 <= self.params['range_threshold'] <= 100):
            raise ValueError(f"Range threshold must be between 0 and 100, got {self.params['range_threshold']}")
        
        if self.params['rsi_period'] < 1:
            raise ValueError(f"RSI period must be positive, got {self.params['rsi_period']}")
        
        if not (50 <= self.params['rsi_overbought'] <= 100):
            raise ValueError(f"RSI overbought level must be between 50 and 100, got {self.params['rsi_overbought']}")
        
        if not (0 <= self.params['rsi_oversold'] <= 50):
            raise ValueError(f"RSI oversold level must be between 0 and 50, got {self.params['rsi_oversold']}")
        
        if self.params['risk_reward_ratio'] <= 0:
            raise ValueError(f"Risk reward ratio must be positive, got {self.params['risk_reward_ratio']}")
        
        if self.params['stop_loss_adr_multiplier'] <= 0:
            raise ValueError(f"Stop loss ADR multiplier must be positive, got {self.params['stop_loss_adr_multiplier']}")
        
        if self.params['tick_size'] <= 0:
            raise ValueError(f"Tick size must be positive, got {self.params['tick_size']}")
        
        if self.params['use_williams_r']:
            if self.params['williams_period'] < 1:
                raise ValueError(f"Williams %R period must be positive, got {self.params['williams_period']}")
            
            if not (-100 <= self.params['williams_oversold'] <= 0):
                raise ValueError(f"Williams %R oversold level must be between -100 and 0, got {self.params['williams_oversold']}")
            
            if not (-100 <= self.params['williams_overbought'] <= 0):
                raise ValueError(f"Williams %R overbought level must be between -100 and 0, got {self.params['williams_overbought']}")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on ADR and momentum indicators.
        
        Args:
            data (pd.DataFrame): Market data with OHLCV columns
            
        Returns:
            pd.DataFrame: Data with added signal columns
        """
        logger.info(f"Generating signals for {self.name} strategy")
        
        # Make a copy of the data to avoid modifying the original
        df = data.copy()
        
        # Check required columns
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found in data")
        
        # Calculate ADR
        adr_data, current_adr, current_range_pct, sl_level = Indicators.average_daily_range(
            df, 
            self.params['adr_period'],
            self.params['tick_size'],
            1.0  # We'll calculate our own stop loss
        )
        
        # Add ADR data to the dataframe
        df = pd.concat([df, adr_data[['ADR', 'daily_range', 'range_pct']]], axis=1)
        
        # Calculate momentum indicator (RSI or Williams %R)
        if self.params['use_williams_r']:
            df['williams_r'] = Indicators.williams_r(df, self.params['williams_period'])
            df['overbought'] = df['williams_r'] > self.params['williams_overbought']
            df['oversold'] = df['williams_r'] < self.params['williams_oversold']
        else:
            df['rsi'] = Indicators.rsi(df, self.params['rsi_period'])
            df['overbought'] = df['rsi'] > self.params['rsi_overbought']
            df['oversold'] = df['rsi'] < self.params['rsi_oversold']
        
        # Initialize signal columns
        df['signal'] = 0
        df['sl_price'] = np.nan
        df['tp_price'] = np.nan
        
        # Generate signals
        # BUY signal: Price has moved down significantly and momentum indicator is oversold
        buy_condition = (
            (df['range_pct'] > self.params['range_threshold']) & 
            (df['Close'] < df['Open']) &  # Price moved down today
            df['oversold']
        )
        
        # SELL signal: Price has moved up significantly and momentum indicator is overbought
        sell_condition = (
            (df['range_pct'] > self.params['range_threshold']) & 
            (df['Close'] > df['Open']) &  # Price moved up today
            df['overbought']
        )
        
        # Apply signals
        df.loc[buy_condition, 'signal'] = 1
        df.loc[sell_condition, 'signal'] = -1
        
        # Calculate stop loss and take profit for signals
        for idx in df[df['signal'] != 0].index:
            if df.loc[idx, 'signal'] == 1:  # BUY signal
                sl, tp = self._calculate_sl_tp(
                    df.loc[idx, 'Close'],
                    df.loc[idx, 'ADR'],
                    is_buy=True
                )
                df.loc[idx, 'sl_price'] = sl
                df.loc[idx, 'tp_price'] = tp
            
            elif df.loc[idx, 'signal'] == -1:  # SELL signal
                sl, tp = self._calculate_sl_tp(
                    df.loc[idx, 'Close'],
                    df.loc[idx, 'ADR'],
                    is_buy=False
                )
                df.loc[idx, 'sl_price'] = sl
                df.loc[idx, 'tp_price'] = tp
        
        logger.info(f"Generated {len(df[df['signal'] != 0])} signals")
        return df
    
    def _calculate_sl_tp(self, price: float, adr: float, is_buy: bool) -> Tuple[float, float]:
        """
        Calculate stop loss and take profit prices based on ADR.
        
        Args:
            price (float): Current price
            adr (float): Average Daily Range in ticks
            is_buy (bool): True for buy signals, False for sell signals
            
        Returns:
            Tuple[float, float]: Stop loss and take profit prices
        """
        # Convert ADR from ticks to price
        adr_price = adr * self.params['tick_size']
        
        # Calculate stop loss distance
        sl_distance = adr_price * self.params['stop_loss_adr_multiplier']
        
        # Calculate take profit distance based on risk-reward ratio
        tp_distance = sl_distance * self.params['risk_reward_ratio']
        
        if is_buy:
            sl_price = price - sl_distance
            tp_price = price + tp_distance
        else:
            sl_price = price + sl_distance
            tp_price = price - tp_distance
        
        # Round to tick size
        sl_price = round(sl_price / self.params['tick_size']) * self.params['tick_size']
        tp_price = round(tp_price / self.params['tick_size']) * self.params['tick_size']
        
        return sl_price, tp_price
    
    def get_signal(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Get the current trading signal based on the latest data.
        
        Args:
            data (pd.DataFrame): Market data with OHLCV columns
            
        Returns:
            Dict[str, Any]: Signal information including direction, stop loss, and take profit
        """
        # Generate signals for the data
        signals_df = self.generate_signals(data)
        
        # Get the latest signal
        latest = signals_df.iloc[-1]
        
        # Prepare signal information
        signal_info = {
            'strategy': self.name,
            'timestamp': latest.name,
            'price': latest['Close'],
            'direction': int(latest['signal']),
            'sl_price': latest['sl_price'] if not np.isnan(latest['sl_price']) else None,
            'tp_price': latest['tp_price'] if not np.isnan(latest['tp_price']) else None,
            'adr': latest['ADR'] if 'ADR' in latest else None,
            'range_pct': latest['range_pct'] if 'range_pct' in latest else None
        }
        
        # Add momentum indicator info
        if self.params['use_williams_r']:
            signal_info['williams_r'] = latest['williams_r']
        else:
            signal_info['rsi'] = latest['rsi']
        
        # Log signal
        if signal_info['direction'] != 0:
            direction_str = "BUY" if signal_info['direction'] == 1 else "SELL"
            logger.info(f"Generated {direction_str} signal at {signal_info['timestamp']} "
                       f"price={signal_info['price']}, sl={signal_info['sl_price']}, "
                       f"tp={signal_info['tp_price']}, adr={signal_info['adr']}, "
                       f"range_pct={signal_info['range_pct']}%")
        
        return signal_info
    
    def backtest(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Backtest the strategy on historical data.
        
        Args:
            data (pd.DataFrame): Historical market data
            
        Returns:
            pd.DataFrame: Backtest results with signals and performance metrics
        """
        logger.info(f"Backtesting {self.name} strategy")
        
        # Generate signals
        signals = self.generate_signals(data)
        
        # Initialize columns for backtest results
        signals['position'] = 0
        signals['entry_price'] = np.nan
        signals['exit_price'] = np.nan
        signals['exit_type'] = ''
        signals['pnl'] = 0.0
        signals['cumulative_pnl'] = 0.0
        
        # Track open positions
        position = 0
        entry_price = 0.0
        entry_index = None
        sl_price = None
        tp_price = None
        
        # Simulate trading
        for i in range(1, len(signals)):
            prev_idx = signals.index[i-1]
            curr_idx = signals.index[i]
            
            # Check if we have an open position
            if position != 0:
                # Check for stop loss or take profit hit
                if position == 1:  # Long position
                    if signals.loc[curr_idx, 'Low'] <= sl_price:
                        # Stop loss hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = sl_price
                        signals.loc[curr_idx, 'exit_type'] = 'sl'
                        signals.loc[curr_idx, 'pnl'] = (sl_price - entry_price) / entry_price * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Stop loss hit at {curr_idx}, exit_price={sl_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                    
                    elif signals.loc[curr_idx, 'High'] >= tp_price:
                        # Take profit hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = tp_price
                        signals.loc[curr_idx, 'exit_type'] = 'tp'
                        signals.loc[curr_idx, 'pnl'] = (tp_price - entry_price) / entry_price * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Take profit hit at {curr_idx}, exit_price={tp_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                
                elif position == -1:  # Short position
                    if signals.loc[curr_idx, 'High'] >= sl_price:
                        # Stop loss hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = sl_price
                        signals.loc[curr_idx, 'exit_type'] = 'sl'
                        signals.loc[curr_idx, 'pnl'] = (entry_price - sl_price) / entry_price * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Stop loss hit at {curr_idx}, exit_price={sl_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                    
                    elif signals.loc[curr_idx, 'Low'] <= tp_price:
                        # Take profit hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = tp_price
                        signals.loc[curr_idx, 'exit_type'] = 'tp'
                        signals.loc[curr_idx, 'pnl'] = (entry_price - tp_price) / entry_price * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Take profit hit at {curr_idx}, exit_price={tp_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
            
            # Check for new signal if we don't have an open position
            if position == 0 and signals.loc[prev_idx, 'signal'] != 0:
                position = signals.loc[prev_idx, 'signal']
                entry_price = signals.loc[curr_idx, 'Open']  # Enter on next bar open
                entry_index = curr_idx
                sl_price = signals.loc[prev_idx, 'sl_price']
                tp_price = signals.loc[prev_idx, 'tp_price']
                
                signals.loc[curr_idx, 'position'] = position
                signals.loc[curr_idx, 'entry_price'] = entry_price
                
                direction_str = "LONG" if position == 1 else "SHORT"
                logger.info(f"Entered {direction_str} position at {curr_idx}, entry_price={entry_price}, sl={sl_price}, tp={tp_price}")
        
        # Close any open position at the end of the backtest
        if position != 0:
            last_idx = signals.index[-1]
            exit_price = signals.loc[last_idx, 'Close']
            
            signals.loc[last_idx, 'position'] = 0
            signals.loc[last_idx, 'exit_price'] = exit_price
            signals.loc[last_idx, 'exit_type'] = 'close'
            
            if position == 1:
                signals.loc[last_idx, 'pnl'] = (exit_price - entry_price) / entry_price * 100
            else:
                signals.loc[last_idx, 'pnl'] = (entry_price - exit_price) / entry_price * 100
            
            logger.info(f"Closed position at end of backtest, exit_price={exit_price}, pnl={signals.loc[last_idx, 'pnl']:.2f}%")
        
        # Calculate cumulative PnL
        signals['cumulative_pnl'] = signals['pnl'].cumsum()
        
        # Calculate performance metrics
        total_trades = len(signals[signals['pnl'] != 0])
        winning_trades = len(signals[signals['pnl'] > 0])
        losing_trades = len(signals[signals['pnl'] < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = signals[signals['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = signals[signals['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
        
        total_return = signals['pnl'].sum()
        
        logger.info(f"Backtest completed with {total_trades} trades, win rate: {win_rate:.2f}, "
                   f"profit factor: {profit_factor:.2f}, total return: {total_return:.2f}%")
        
        return signals 