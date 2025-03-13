import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Tuple, Any
from datetime import datetime, timedelta

from app.strategy.base import Strategy
from app.strategy.indicators import Indicators
from app.utils import get_logger

logger = get_logger(__name__)

class MeanReversionSwinglineStrategy(Strategy):
    """
    Mean Reversion strategy that combines ADR and Swingline indicators.
    
    This strategy identifies potential reversal points when price has moved significantly
    in one direction within a single day, exceeding a certain percentage of the Average Daily Range,
    and confirms the entry with a swingline direction change.
    
    Strategy Logic:
    1. Calculate the Average Daily Range (ADR) over a specified period
    2. Calculate the current day's range as a percentage of the ADR
    3. Calculate the Swingline indicator to identify trend direction changes
    4. If the current range exceeds the threshold, RSI confirms overbought/oversold, and Swingline confirms:
       - For BUY: Price has moved down significantly (exceeding threshold), RSI is oversold, and Swingline changes to up
       - For SELL: Price has moved up significantly (exceeding threshold), RSI is overbought, and Swingline changes to down
    5. Place trades with stop loss based on ADR and take profit at a multiple of the risk
    
    Parameters:
    - adr_period: Number of days to calculate ADR
    - range_threshold: Percentage of ADR that current range must exceed to trigger signal
    - rsi_period: Period for RSI calculation
    - rsi_overbought: RSI level considered overbought
    - rsi_oversold: RSI level considered oversold
    - risk_reward_ratio: Risk to reward ratio for take profit calculation
    - stop_loss_adr_multiplier: Multiplier of ADR for stop loss calculation
    - tick_size: Minimum price movement for the instrument
    - use_williams_r: Option to use Williams %R instead of RSI
    - williams_period: Period for Williams %R calculation
    - williams_overbought: Williams %R level considered overbought
    - williams_oversold: Williams %R level considered oversold
    """
    
    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the Mean Reversion Swingline Strategy.
        
        Args:
            symbols (List[str]): List of symbols to trade
            timeframes (List[str]): List of timeframes to analyze
            parameters (Dict[str, Any], optional): Strategy parameters
        """
        default_parameters = {
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
            'williams_oversold': -80,
            'require_swingline_confirmation': True,  # Whether to require swingline confirmation
            'swingline_lookback': 3,  # Number of bars to look back for swingline change
            'atr_period': 14,
            'sl_atr_multiplier': 1.5,
            'tp_atr_multiplier': 2.0,
            'risk_per_trade': 0.01,  # 1% risk per trade
            'max_trades_per_day': 3,
            'max_trades_per_symbol': 1,
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
            'timeframe': 'H1'
        }
        
        # Initialize base class with merged parameters
        merged_parameters = {**default_parameters, **(parameters or {})}
        super().__init__(
            name="MeanReversionSwingline",
            symbols=symbols,
            timeframes=timeframes,
            parameters=merged_parameters
        )
        
        # Validate parameters
        self._validate_strategy_parameters()
        
        # Initialize trade tracking
        self.trades_today = 0
        self.trades_per_symbol = {symbol: 0 for symbol in self.parameters['symbols']}
        
        logger.info(f"Initialized {self.name} strategy with parameters: {self.parameters}")
    
    def _validate_strategy_parameters(self) -> None:
        """
        Validate strategy parameters.
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if self.parameters['adr_period'] < 1:
            raise ValueError(f"ADR period must be positive, got {self.parameters['adr_period']}")
        
        if not (0 <= self.parameters['range_threshold'] <= 100):
            raise ValueError(f"Range threshold must be between 0 and 100, got {self.parameters['range_threshold']}")
        
        if self.parameters['rsi_period'] < 1:
            raise ValueError(f"RSI period must be positive, got {self.parameters['rsi_period']}")
        
        if not (50 <= self.parameters['rsi_overbought'] <= 100):
            raise ValueError(f"RSI overbought level must be between 50 and 100, got {self.parameters['rsi_overbought']}")
        
        if not (0 <= self.parameters['rsi_oversold'] <= 50):
            raise ValueError(f"RSI oversold level must be between 0 and 50, got {self.parameters['rsi_oversold']}")
        
        if self.parameters['risk_reward_ratio'] <= 0:
            raise ValueError(f"Risk reward ratio must be positive, got {self.parameters['risk_reward_ratio']}")
        
        if self.parameters['stop_loss_adr_multiplier'] <= 0:
            raise ValueError(f"Stop loss ADR multiplier must be positive, got {self.parameters['stop_loss_adr_multiplier']}")
        
        if self.parameters['tick_size'] <= 0:
            raise ValueError(f"Tick size must be positive, got {self.parameters['tick_size']}")
        
        if self.parameters['use_williams_r']:
            if self.parameters['williams_period'] < 1:
                raise ValueError(f"Williams %R period must be positive, got {self.parameters['williams_period']}")
            
            if not (-100 <= self.parameters['williams_oversold'] <= 0):
                raise ValueError(f"Williams %R oversold level must be between -100 and 0, got {self.parameters['williams_oversold']}")
            
            if not (-100 <= self.parameters['williams_overbought'] <= 0):
                raise ValueError(f"Williams %R overbought level must be between -100 and 0, got {self.parameters['williams_overbought']}")
        
        if self.parameters['swingline_lookback'] < 1:
            raise ValueError(f"Swingline lookback must be positive, got {self.parameters['swingline_lookback']}")
        
        if not (1 <= self.parameters['atr_period'] <= 100):
            raise ValueError(f"Invalid ATR period: {self.parameters['atr_period']}")
        
        if not (0.1 <= self.parameters['sl_atr_multiplier'] <= 10):
            raise ValueError(f"Invalid stop loss ATR multiplier: {self.parameters['sl_atr_multiplier']}")
        
        if not (0.1 <= self.parameters['tp_atr_multiplier'] <= 10):
            raise ValueError(f"Invalid take profit ATR multiplier: {self.parameters['tp_atr_multiplier']}")
        
        if not (0.001 <= self.parameters['risk_per_trade'] <= 0.05):
            raise ValueError(f"Invalid risk per trade: {self.parameters['risk_per_trade']}")
        
        if not (1 <= self.parameters['max_trades_per_day'] <= 20):
            raise ValueError(f"Invalid max trades per day: {self.parameters['max_trades_per_day']}")
        
        if not (1 <= self.parameters['max_trades_per_symbol'] <= 5):
            raise ValueError(f"Invalid max trades per symbol: {self.parameters['max_trades_per_symbol']}")
    
    def _generate_signals(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Generate trading signals for a specific symbol.
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            List[Dict[str, Any]]: List of trading signals
        """
        signals = []
        
        # Check if we have market data for this symbol
        if symbol not in self.market_data:
            logger.warning(f"No market data available for symbol {symbol}")
            return signals
        
        # Use the first available timeframe for this symbol
        timeframe = next(iter(self.market_data[symbol].keys()))
        data = self.market_data[symbol][timeframe]
        
        # Generate signals using the data
        signals_df = self.generate_signals(data)
        
        # Check if we have a signal in the latest bar
        latest = signals_df.iloc[-1]
        if latest['signal'] != 0:
            # Create signal dictionary
            signal = {
                'symbol': symbol,
                'timeframe': timeframe,
                'direction': int(latest['signal']),
                'price': float(latest['Close']),
                'stop_loss': float(latest['sl_price']) if not pd.isna(latest['sl_price']) else None,
                'take_profit': float(latest['tp_price']) if not pd.isna(latest['tp_price']) else None,
                'timestamp': latest.name,
                'strategy': self.name,
                'parameters': {
                    'adr': float(latest['ADR']) if 'ADR' in latest else None,
                    'range_pct': float(latest['range_pct']) if 'range_pct' in latest else None,
                    'swingline': int(latest['swingline']) if 'swingline' in latest else None
                }
            }
            
            # Add momentum indicator info
            if self.parameters['use_williams_r']:
                signal['parameters']['williams_r'] = float(latest['williams_r'])
            else:
                signal['parameters']['rsi'] = float(latest['rsi'])
            
            signals.append(signal)
            
            # Log signal
            direction_str = "BUY" if signal['direction'] == 1 else "SELL"
            logger.info(f"Generated {direction_str} signal for {symbol} at {signal['timestamp']} "
                       f"price={signal['price']}, sl={signal['stop_loss']}, tp={signal['take_profit']}")
        
        return signals
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on ADR, momentum indicators, and swingline.
        
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
            self.parameters['adr_period'],
            self.parameters['tick_size'],
            1.0  # We'll calculate our own stop loss
        )
        
        # Add ADR data to the dataframe
        df = pd.concat([df, adr_data[['ADR', 'daily_range', 'range_pct']]], axis=1)
        
        # Calculate momentum indicator (RSI or Williams %R)
        if self.parameters['use_williams_r']:
            df['williams_r'] = Indicators.williams_r(df, self.parameters['williams_period'])
            df['overbought'] = df['williams_r'] > self.parameters['williams_overbought']
            df['oversold'] = df['williams_r'] < self.parameters['williams_oversold']
        else:
            df['rsi'] = Indicators.rsi(df, self.parameters['rsi_period'])
            df['overbought'] = df['rsi'] > self.parameters['rsi_overbought']
            df['oversold'] = df['rsi'] < self.parameters['rsi_oversold']
        
        # Calculate Swingline
        df['swingline'] = Indicators.swingline(df)
        
        # Calculate Swingline changes
        df['swingline_change'] = df['swingline'].diff()
        
        # Initialize signal columns
        df['signal'] = 0
        df['sl_price'] = np.nan
        df['tp_price'] = np.nan
        
        # Generate signals
        for i in range(self.parameters['swingline_lookback'] + 1, len(df)):
            # Check if current range exceeds threshold
            if df['range_pct'].iloc[i] > self.parameters['range_threshold']:
                # Check for BUY signal
                if (df['Close'].iloc[i] < df['Open'].iloc[i] and  # Price moved down today
                    df['oversold'].iloc[i]):  # Momentum indicator is oversold
                    
                    # Check for swingline confirmation if required
                    swingline_confirmed = True
                    if self.parameters['require_swingline_confirmation']:
                        # Check if swingline changed to up within the lookback period
                        lookback_start = max(0, i - self.parameters['swingline_lookback'])
                        swingline_window = df['swingline_change'].iloc[lookback_start:i+1]
                        swingline_confirmed = (swingline_window == 2).any()  # Change from -1 to 1 is a value of 2
                    
                    if swingline_confirmed:
                        df.loc[df.index[i], 'signal'] = 1
                        
                        # Calculate stop loss and take profit
                        sl, tp = self._calculate_sl_tp(
                            float(df['Close'].iloc[i]),
                            float(df['ADR'].iloc[i]),
                            is_buy=True
                        )
                        df.loc[df.index[i], 'sl_price'] = sl
                        df.loc[df.index[i], 'tp_price'] = tp
                
                # Check for SELL signal
                elif (df['Close'].iloc[i] > df['Open'].iloc[i] and  # Price moved up today
                      df['overbought'].iloc[i]):  # Momentum indicator is overbought
                    
                    # Check for swingline confirmation if required
                    swingline_confirmed = True
                    if self.parameters['require_swingline_confirmation']:
                        # Check if swingline changed to down within the lookback period
                        lookback_start = max(0, i - self.parameters['swingline_lookback'])
                        swingline_window = df['swingline_change'].iloc[lookback_start:i+1]
                        swingline_confirmed = (swingline_window == -2).any()  # Change from 1 to -1 is a value of -2
                    
                    if swingline_confirmed:
                        df.loc[df.index[i], 'signal'] = -1
                        
                        # Calculate stop loss and take profit
                        sl, tp = self._calculate_sl_tp(
                            float(df['Close'].iloc[i]),
                            float(df['ADR'].iloc[i]),
                            is_buy=False
                        )
                        df.loc[df.index[i], 'sl_price'] = sl
                        df.loc[df.index[i], 'tp_price'] = tp
        
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
        adr_price = adr * self.parameters['tick_size']
        
        # Calculate stop loss distance
        sl_distance = adr_price * self.parameters['stop_loss_adr_multiplier']
        
        # Calculate take profit distance based on risk-reward ratio
        tp_distance = sl_distance * self.parameters['risk_reward_ratio']
        
        if is_buy:
            sl_price = price - sl_distance
            tp_price = price + tp_distance
        else:
            sl_price = price + sl_distance
            tp_price = price - tp_distance
        
        # Round to tick size
        sl_price = round(sl_price / self.parameters['tick_size']) * self.parameters['tick_size']
        tp_price = round(tp_price / self.parameters['tick_size']) * self.parameters['tick_size']
        
        return sl_price, tp_price
    
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
                    if sl_price is not None and float(signals.loc[curr_idx, 'Low']) <= float(sl_price):
                        # Stop loss hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = sl_price
                        signals.loc[curr_idx, 'exit_type'] = 'sl'
                        signals.loc[curr_idx, 'pnl'] = (float(sl_price) - float(entry_price)) / float(entry_price) * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Stop loss hit at {curr_idx}, exit_price={sl_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                    
                    elif tp_price is not None and float(signals.loc[curr_idx, 'High']) >= float(tp_price):
                        # Take profit hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = tp_price
                        signals.loc[curr_idx, 'exit_type'] = 'tp'
                        signals.loc[curr_idx, 'pnl'] = (float(tp_price) - float(entry_price)) / float(entry_price) * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Take profit hit at {curr_idx}, exit_price={tp_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                
                elif position == -1:  # Short position
                    if sl_price is not None and float(signals.loc[curr_idx, 'High']) >= float(sl_price):
                        # Stop loss hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = sl_price
                        signals.loc[curr_idx, 'exit_type'] = 'sl'
                        signals.loc[curr_idx, 'pnl'] = (float(entry_price) - float(sl_price)) / float(entry_price) * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Stop loss hit at {curr_idx}, exit_price={sl_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
                    
                    elif tp_price is not None and float(signals.loc[curr_idx, 'Low']) <= float(tp_price):
                        # Take profit hit
                        signals.loc[curr_idx, 'position'] = 0
                        signals.loc[curr_idx, 'exit_price'] = tp_price
                        signals.loc[curr_idx, 'exit_type'] = 'tp'
                        signals.loc[curr_idx, 'pnl'] = (float(entry_price) - float(tp_price)) / float(entry_price) * 100
                        
                        # Reset position
                        position = 0
                        logger.info(f"Take profit hit at {curr_idx}, exit_price={tp_price}, pnl={signals.loc[curr_idx, 'pnl']:.2f}%")
            
            # Check for new signal if we don't have an open position
            if position == 0 and signals.loc[prev_idx, 'signal'] != 0:
                position = int(signals.loc[prev_idx, 'signal'])
                entry_price = float(signals.loc[curr_idx, 'Open'])  # Enter on next bar open
                entry_index = curr_idx
                
                # Get stop loss and take profit prices, ensuring they are valid floats
                sl_price = signals.loc[prev_idx, 'sl_price']
                tp_price = signals.loc[prev_idx, 'tp_price']
                
                # Check if sl_price and tp_price are valid (not NaN)
                if pd.isna(sl_price):
                    sl_price = None
                if pd.isna(tp_price):
                    tp_price = None
                
                signals.loc[curr_idx, 'position'] = position
                signals.loc[curr_idx, 'entry_price'] = entry_price
                
                direction_str = "LONG" if position == 1 else "SHORT"
                logger.info(f"Entered {direction_str} position at {curr_idx}, entry_price={entry_price}, sl={sl_price}, tp={tp_price}")
        
        # Close any open position at the end of the backtest
        if position != 0:
            last_idx = signals.index[-1]
            exit_price = float(signals.loc[last_idx, 'Close'])
            
            signals.loc[last_idx, 'position'] = 0
            signals.loc[last_idx, 'exit_price'] = exit_price
            signals.loc[last_idx, 'exit_type'] = 'close'
            
            if position == 1:
                signals.loc[last_idx, 'pnl'] = (exit_price - float(entry_price)) / float(entry_price) * 100
            else:
                signals.loc[last_idx, 'pnl'] = (float(entry_price) - exit_price) / float(entry_price) * 100
            
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
                   f"profit_factor: {profit_factor:.2f}, total_return: {total_return:.2f}%")
        
        return signals 