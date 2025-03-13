"""
Technical indicators implementation module.

This module provides a collection of technical indicators commonly used in trading strategies.
It uses the ta package for technical analysis indicators.
"""
from typing import Dict, List, Optional, Union, Tuple, Any
import pandas as pd
import numpy as np

# Import ta package for technical indicators
import ta
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator, WilliamsRIndicator
from ta.volatility import  AverageTrueRange
from ta.volume import VolumeWeightedAveragePrice

from ..utils.logger import get_logger

logger = get_logger(__name__)

class Indicators:
    """
    Technical indicators implementation.
    
    This class provides methods for calculating various technical indicators
    used in trading strategies. It uses the ta package for technical analysis.
    """
    
    @staticmethod
    def moving_average(data: pd.DataFrame, period: int, price_col: str = 'Close', ma_type: str = 'sma') -> pd.Series:
        """
        Calculate moving average.
        
        Args:
            data (pd.DataFrame): Price data
            period (int): MA period
            price_col (str, optional): Price column to use
            ma_type (str, optional): Moving average type (default: SMA)
                Options: 'sma', 'ema'
                
        Returns:
            pd.Series: Moving average values
        """
        try:
            if price_col not in data.columns:
                logger.warning(f"Column {price_col} not found in data")
                return pd.Series(index=data.index)
                
            if ma_type.lower() == 'sma':
                indicator = SMAIndicator(data[price_col], window=period)
                ma = indicator.sma_indicator()
            elif ma_type.lower() == 'ema':
                indicator = EMAIndicator(data[price_col], window=period)
                ma = indicator.ema_indicator()
            else:
                logger.warning(f"Unsupported MA type: {ma_type}, using SMA")
                indicator = SMAIndicator(data[price_col], window=period)
                ma = indicator.sma_indicator()
                
            return ma
            
        except Exception as e:
            logger.exception(f"Error calculating moving average: {str(e)}")
            return pd.Series(index=data.index)
    
    
    @staticmethod
    def rsi(data: pd.DataFrame, period: int = 14, price_col: str = 'Close') -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            data (pd.DataFrame): Price data
            period (int, optional): RSI period
            price_col (str, optional): Price column to use
            
        Returns:
            pd.Series: RSI values
        """
        try:
            if price_col not in data.columns:
                logger.warning(f"Column {price_col} not found in data")
                return pd.Series(index=data.index)
                
            indicator = RSIIndicator(data[price_col], window=period)
            rsi = indicator.rsi()
            
            return rsi
            
        except Exception as e:
            logger.exception(f"Error calculating RSI: {str(e)}")
            return pd.Series(index=data.index)
    
    @staticmethod
    def williams_r(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Williams Percent Range (%R).
        
        The Williams %R is a momentum indicator that measures overbought and oversold levels.
        It ranges from 0 to -100, with readings from 0 to -20 considered overbought,
        and readings from -80 to -100 considered oversold.
        
        Args:
            data (pd.DataFrame): Price data
            period (int, optional): Lookback period
            
        Returns:
            pd.Series: Williams %R values
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low', 'Close']):
                logger.warning("High, Low, or Close columns not found in data")
                return pd.Series(index=data.index)
                
            indicator = WilliamsRIndicator(
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                lbp=period
            )
            
            williams_r = indicator.williams_r()
            
            return williams_r
            
        except Exception as e:
            logger.exception(f"Error calculating Williams %R: {str(e)}")
            return pd.Series(index=data.index)

    
    @staticmethod
    def atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR).
        
        Args:
            data (pd.DataFrame): Price data
            period (int, optional): ATR period
            
        Returns:
            pd.Series: ATR values
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low', 'Close']):
                logger.warning("High, Low, or Close columns not found in data")
                return pd.Series(index=data.index)
                
            indicator = AverageTrueRange(
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                window=period
            )
            
            atr = indicator.average_true_range()
            
            return atr
            
        except Exception as e:
            logger.exception(f"Error calculating ATR: {str(e)}")
            return pd.Series(index=data.index)
    
    
    @staticmethod
    def fibonacci_retracement(
        data: pd.DataFrame,
        period: int = 100,
        levels: List[float] = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    ) -> Dict[float, pd.Series]:
        """
        Calculate Fibonacci Retracement levels.
        
        Args:
            data (pd.DataFrame): Price data
            period (int, optional): Period to calculate high and low
            levels (List[float], optional): Fibonacci levels to calculate
            
        Returns:
            Dict[float, pd.Series]: Dictionary containing Fibonacci levels
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low']):
                logger.warning("High or Low columns not found in data")
                return {level: pd.Series(index=data.index) for level in levels}
                
            # Calculate high and low over the period
            high = data['High'].rolling(window=period).max()
            low = data['Low'].rolling(window=period).min()
            
            # Calculate retracement levels
            retracement = {}
            for level in levels:
                retracement[level] = low + (high - low) * level
                
            return retracement
            
        except Exception as e:
            logger.exception(f"Error calculating Fibonacci Retracement: {str(e)}")
            return {level: pd.Series(index=data.index) for level in levels}
    
    @staticmethod
    def pivot_points(data: pd.DataFrame, pivot_type: str = 'standard') -> Dict[str, pd.Series]:
        """
        Calculate Pivot Points.
        
        Args:
            data (pd.DataFrame): Price data (must be in daily timeframe)
            pivot_type (str, optional): Pivot point type
                Options: 'standard', 'fibonacci', 'woodie', 'camarilla', 'demark'
            
        Returns:
            Dict[str, pd.Series]: Dictionary containing pivot points
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low', 'Close']):
                logger.warning("High, Low, or Close columns not found in data")
                return {
                    'pivot': pd.Series(index=data.index),
                    'r1': pd.Series(index=data.index),
                    'r2': pd.Series(index=data.index),
                    'r3': pd.Series(index=data.index),
                    's1': pd.Series(index=data.index),
                    's2': pd.Series(index=data.index),
                    's3': pd.Series(index=data.index)
                }
                
            # Get previous day's data
            prev_high = data['High'].shift(1)
            prev_low = data['Low'].shift(1)
            prev_close = data['Close'].shift(1)
            prev_open = data['Open'].shift(1) if 'Open' in data.columns else None
            
            # Calculate pivot points based on type
            if pivot_type == 'standard':
                pivot = (prev_high + prev_low + prev_close) / 3
                r1 = (2 * pivot) - prev_low
                s1 = (2 * pivot) - prev_high
                r2 = pivot + (prev_high - prev_low)
                s2 = pivot - (prev_high - prev_low)
                r3 = r1 + (prev_high - prev_low)
                s3 = s1 - (prev_high - prev_low)
                
            elif pivot_type == 'fibonacci':
                pivot = (prev_high + prev_low + prev_close) / 3
                r1 = pivot + 0.382 * (prev_high - prev_low)
                s1 = pivot - 0.382 * (prev_high - prev_low)
                r2 = pivot + 0.618 * (prev_high - prev_low)
                s2 = pivot - 0.618 * (prev_high - prev_low)
                r3 = pivot + 1.0 * (prev_high - prev_low)
                s3 = pivot - 1.0 * (prev_high - prev_low)
                
            elif pivot_type == 'woodie':
                pivot = (prev_high + prev_low + 2 * prev_close) / 4
                r1 = (2 * pivot) - prev_low
                s1 = (2 * pivot) - prev_high
                r2 = pivot + (prev_high - prev_low)
                s2 = pivot - (prev_high - prev_low)
                r3 = r1 + (prev_high - prev_low)
                s3 = s1 - (prev_high - prev_low)
                
            elif pivot_type == 'camarilla':
                pivot = (prev_high + prev_low + prev_close) / 3
                r1 = prev_close + 1.1 * (prev_high - prev_low) / 12
                s1 = prev_close - 1.1 * (prev_high - prev_low) / 12
                r2 = prev_close + 1.1 * (prev_high - prev_low) / 6
                s2 = prev_close - 1.1 * (prev_high - prev_low) / 6
                r3 = prev_close + 1.1 * (prev_high - prev_low) / 4
                s3 = prev_close - 1.1 * (prev_high - prev_low) / 4
                
            elif pivot_type == 'demark':
                if prev_open is None:
                    logger.warning("Open price required for Demark pivot points")
                    return {
                        'pivot': pd.Series(index=data.index),
                        'r1': pd.Series(index=data.index),
                        's1': pd.Series(index=data.index)
                    }
                
                if prev_close < prev_open:
                    pivot = prev_high + (2 * prev_low) + prev_close
                elif prev_close > prev_open:
                    pivot = (2 * prev_high) + prev_low + prev_close
                else:
                    pivot = prev_high + prev_low + (2 * prev_close)
                    
                pivot = pivot / 4
                r1 = (2 * pivot) - prev_low
                s1 = (2 * pivot) - prev_high
                
                # Demark only has R1 and S1
                return {
                    'pivot': pivot,
                    'r1': r1,
                    's1': s1
                }
                
            else:
                logger.warning(f"Invalid pivot point type: {pivot_type}")
                return {
                    'pivot': pd.Series(index=data.index),
                    'r1': pd.Series(index=data.index),
                    'r2': pd.Series(index=data.index),
                    'r3': pd.Series(index=data.index),
                    's1': pd.Series(index=data.index),
                    's2': pd.Series(index=data.index),
                    's3': pd.Series(index=data.index)
                }
                
            return {
                'pivot': pivot,
                'r1': r1,
                'r2': r2,
                'r3': r3,
                's1': s1,
                's2': s2,
                's3': s3
            }
            
        except Exception as e:
            logger.exception(f"Error calculating Pivot Points: {str(e)}")
            return {
                'pivot': pd.Series(index=data.index),
                'r1': pd.Series(index=data.index),
                'r2': pd.Series(index=data.index),
                'r3': pd.Series(index=data.index),
                's1': pd.Series(index=data.index),
                's2': pd.Series(index=data.index),
                's3': pd.Series(index=data.index)
            }
    
    @staticmethod
    def vwap(data: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        Args:
            data (pd.DataFrame): Price data with OHLCV columns
            
        Returns:
            pd.Series: VWAP values
        """
        try:
            if not all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']):
                logger.warning("Required columns not found in data")
                return pd.Series(index=data.index)
                
            indicator = VolumeWeightedAveragePrice(
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                volume=data['Volume']
            )
            
            vwap = indicator.volume_weighted_average_price()
            
            return vwap
            
        except Exception as e:
            logger.exception(f"Error calculating VWAP: {str(e)}")
            return pd.Series(index=data.index)
    
    @staticmethod
    def supertrend(
        data: pd.DataFrame,
        period: int = 10,
        multiplier: float = 3.0
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate SuperTrend indicator.
        
        Args:
            data (pd.DataFrame): Price data
            period (int, optional): ATR period
            multiplier (float, optional): ATR multiplier
            
        Returns:
            Tuple[pd.Series, pd.Series]: SuperTrend values and direction (1 for bullish, -1 for bearish)
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low', 'Close']):
                logger.warning("High, Low, or Close columns not found in data")
                empty_series = pd.Series(index=data.index)
                return empty_series, empty_series
                
            # Calculate ATR
            atr = Indicators.atr(data, period)
            
            # Calculate basic upper and lower bands
            hl2 = (data['High'] + data['Low']) / 2
            basic_upper_band = hl2 + (multiplier * atr)
            basic_lower_band = hl2 - (multiplier * atr)
            
            # Initialize SuperTrend columns
            supertrend = pd.Series(0.0, index=data.index)
            direction = pd.Series(0, index=data.index)
            
            # Calculate SuperTrend
            for i in range(period, len(data)):
                if i == period:
                    supertrend.iloc[i] = basic_upper_band.iloc[i]
                    direction.iloc[i] = 1
                    continue
                    
                if supertrend.iloc[i-1] == basic_upper_band.iloc[i-1]:
                    if data['Close'].iloc[i] > basic_upper_band.iloc[i]:
                        supertrend.iloc[i] = basic_lower_band.iloc[i]
                        direction.iloc[i] = 1
                    else:
                        supertrend.iloc[i] = basic_upper_band.iloc[i]
                        direction.iloc[i] = -1
                        
                elif supertrend.iloc[i-1] == basic_lower_band.iloc[i-1]:
                    if data['Close'].iloc[i] < basic_lower_band.iloc[i]:
                        supertrend.iloc[i] = basic_upper_band.iloc[i]
                        direction.iloc[i] = -1
                    else:
                        supertrend.iloc[i] = basic_lower_band.iloc[i]
                        direction.iloc[i] = 1
            
            return supertrend, direction
            
        except Exception as e:
            logger.exception(f"Error calculating SuperTrend: {str(e)}")
            empty_series = pd.Series(index=data.index)
            return empty_series, empty_series 
    
    @staticmethod
    def average_daily_range(
        data: pd.DataFrame, 
        period: int = 14, 
        tick_size: float = 0.00001,
        stop_loss_ratio: float = 3.0
    ) -> Tuple[pd.DataFrame, float, float, float]:
        """
        Calculate the Average Daily Range (ADR) and related metrics.
        
        The ADR measures the average range of price movement over a specified number of days.
        This is useful for setting stop losses, take profits, and understanding volatility.
        
        Args:
            data (pd.DataFrame): Price data with High, Low, Close columns
            period (int, optional): Number of days to calculate the ADR over
            tick_size (float, optional): The minimum price movement for the instrument
            stop_loss_ratio (float, optional): Ratio to calculate stop loss level from ADR
            
        Returns:
            Tuple[pd.DataFrame, float, float, float]: 
                - DataFrame with ADR calculations
                - Current ADR value
                - Current daily range as percentage of ADR
                - Current stop loss level based on ADR
        """
        try:
            if not all(col in data.columns for col in ['High', 'Low', 'Close']):
                logger.warning("High, Low, or Close columns not found in data")
                return pd.DataFrame(index=data.index), 0.0, 0.0, 0.0
            
            # Create a copy of the data to avoid modifying the original
            df = data.copy()
            
            # Calculate daily ranges in terms of ticks
            df['daily_range'] = (df['High'] - df['Low']) / tick_size / 10
            
            # Calculate ADR (Average Daily Range)
            df['ADR'] = df['daily_range'].rolling(window=period).mean()
            
            # Shift the ADR by one period to make today's ADR based on the previous value
            df['ADR'] = df['ADR'].shift(1)
            
            # Calculate stop loss level based on ADR
            df['SL'] = df['ADR'].apply(lambda x: round(x / stop_loss_ratio) if pd.notnull(x) else np.nan)
            
            # Get current values
            if len(df) > 0:
                current_daily_range = df['daily_range'].iloc[-1]
                current_adr = round(df['ADR'].iloc[-1]) if pd.notnull(df['ADR'].iloc[-1]) else 0.0
                current_sl = df['SL'].iloc[-1] if pd.notnull(df['SL'].iloc[-1]) else 0.0
                
                # Calculate the current daily range as a percentage of ADR
                if current_adr > 0:
                    current_daily_range_percentage = round((current_daily_range / current_adr) * 100)
                else:
                    current_daily_range_percentage = 0.0
            else:
                current_adr = 0.0
                current_daily_range_percentage = 0.0
                current_sl = 0.0
            
            return df, float(current_adr), float(current_daily_range_percentage), float(current_sl)
            
        except Exception as e:
            logger.exception(f"Error calculating Average Daily Range: {str(e)}")
            return pd.DataFrame(index=data.index), 0.0, 0.0, 0.0
    
    @staticmethod
    def swingline(data: pd.DataFrame) -> pd.Series:
        """
        Calculates the swingline direction based on price action.

        The swingline indicates the current trend direction:
        - 1 for upward swing
        - -1 for downward swing

        This indicator helps identify trend changes and potential reversal points.

        Args:
            data (pd.DataFrame): DataFrame containing 'High', 'Low', 'Open', and 'Close' price columns.

        Returns:
            pd.Series: Series containing swingline values (1 for upward swing, -1 for downward swing).
        """
        try:
            # Check required columns
            required_columns = ['High', 'Low', 'Open', 'Close']
            for col in required_columns:
                if col not in data.columns:
                    raise ValueError(f"Required column {col} not found in data")
            
            # Create a copy of the dataframe to avoid modifying the original
            df = data.copy()

            # Initialize swingline column with -1 (starting with downward swing)
            swingline = pd.Series(index=df.index, data=-1)

            # Initialize variables
            highest_high = df['High'].iloc[0]
            lowest_low = df['Low'].iloc[0]
            lowest_high = df['High'].iloc[0]
            highest_low = df['Low'].iloc[0]
            current_swing = -1  # Start with downward swing

            # Iterate through each row to calculate swingline
            for i in range(1, len(df)):
                current_high = df['High'].iloc[i]
                current_low = df['Low'].iloc[i]
                current_open = df['Open'].iloc[i]
                current_close = df['Close'].iloc[i]

                if current_swing == 1:  # If current swing is up
                    # Update highest high and highest low
                    if current_high > highest_high:
                        highest_high = current_high
                    if current_low > highest_low:
                        highest_low = current_low

                    # Check if swing changes to down
                    if (current_high < highest_low and 
                        current_close < current_open and 
                        current_close < df['Low'].iloc[i-1]):
                        current_swing = -1
                        lowest_low = current_low
                        lowest_high = current_high

                elif current_swing == -1:  # If current swing is down
                    # Update lowest low and lowest high
                    if current_low < lowest_low:
                        lowest_low = current_low
                    if current_high < lowest_high:
                        lowest_high = current_high

                    # Check if swing changes to up
                    if (current_low > lowest_high and 
                        current_close > current_open and 
                        current_close > df['High'].iloc[i-1]):
                        current_swing = 1
                        highest_high = current_high
                        highest_low = current_low

                # Assign the current swingline value
                swingline.iloc[i] = current_swing

            return swingline
            
        except Exception as e:
            logger.exception(f"Error calculating Swingline: {str(e)}")
            return pd.Series(index=data.index)
        


        