import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from algotrader.utils.logger import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """
    Utility class for data transformation operations.
    Provides methods for common data processing tasks.
    """
    
    @staticmethod
    def resample_ohlcv(
        df: pd.DataFrame,
        timeframe: str,
        price_col: str = 'close',
        volume_col: Optional[str] = 'volume',
        open_col: Optional[str] = 'open',
        high_col: Optional[str] = 'high',
        low_col: Optional[str] = 'low'
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to a different timeframe.
        
        Args:
            df (pd.DataFrame): DataFrame with datetime index and OHLCV columns
            timeframe (str): Target timeframe (e.g., '1H', '1D', '1W')
            price_col (str): Name of the price column
            volume_col (Optional[str]): Name of the volume column
            open_col (Optional[str]): Name of the open price column
            high_col (Optional[str]): Name of the high price column
            low_col (Optional[str]): Name of the low price column
            
        Returns:
            pd.DataFrame: Resampled DataFrame
        """
        # Ensure DataFrame has datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be a DatetimeIndex")
            
        # Define aggregation functions
        agg_dict = {}
        
        if open_col and open_col in df.columns:
            agg_dict[open_col] = 'first'
            
        if high_col and high_col in df.columns:
            agg_dict[high_col] = 'max'
            
        if low_col and low_col in df.columns:
            agg_dict[low_col] = 'min'
            
        if price_col and price_col in df.columns:
            agg_dict[price_col] = 'last'
            
        if volume_col and volume_col in df.columns:
            agg_dict[volume_col] = 'sum'
            
        if not agg_dict:
            raise ValueError("No valid columns found for resampling")
            
        # Perform resampling
        resampled = df.resample(timeframe).agg(agg_dict)
        return resampled
    
    @staticmethod
    def normalize_data(
        data: Union[np.ndarray, pd.DataFrame, pd.Series],
        method: str = 'minmax',
        feature_range: Tuple[float, float] = (0, 1)
    ) -> Tuple[Union[np.ndarray, pd.DataFrame, pd.Series], Any]:
        """
        Normalize data using specified method.
        
        Args:
            data (Union[np.ndarray, pd.DataFrame, pd.Series]): Data to normalize
            method (str): Normalization method ('minmax' or 'zscore')
            feature_range (Tuple[float, float]): Range for MinMaxScaler
            
        Returns:
            Tuple[Union[np.ndarray, pd.DataFrame, pd.Series], Any]: 
                (Normalized data, Scaler object)
        """
        if method.lower() == 'minmax':
            scaler = MinMaxScaler(feature_range=feature_range)
        elif method.lower() == 'zscore':
            scaler = StandardScaler()
        else:
            raise ValueError(f"Invalid normalization method: {method}")
            
        # Handle different input types
        if isinstance(data, pd.DataFrame):
            normalized_data = pd.DataFrame(
                scaler.fit_transform(data),
                index=data.index,
                columns=data.columns
            )
        elif isinstance(data, pd.Series):
            normalized_data = pd.Series(
                scaler.fit_transform(data.values.reshape(-1, 1)).flatten(),
                index=data.index,
                name=data.name
            )
        else:  # numpy array
            # Ensure 2D for sklearn
            if data.ndim == 1:
                data = data.reshape(-1, 1)
            normalized_data = scaler.fit_transform(data)
            
        return normalized_data, scaler
    
    @staticmethod
    def create_sequences(
        data: Union[np.ndarray, pd.DataFrame, pd.Series],
        sequence_length: int,
        target_column: Optional[Union[str, int]] = None,
        step: int = 1,
        forecast_horizon: int = 1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences for time series forecasting.
        
        Args:
            data (Union[np.ndarray, pd.DataFrame, pd.Series]): Input data
            sequence_length (int): Length of input sequences
            target_column (Optional[Union[str, int]]): Target column for prediction
            step (int): Step size between sequences
            forecast_horizon (int): Number of steps to forecast
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (X sequences, y targets)
        """
        # Convert to numpy array
        if isinstance(data, pd.DataFrame):
            if target_column is not None:
                y_data = data[target_column].values
                X_data = data.values
            else:
                y_data = data.values
                X_data = data.values
        elif isinstance(data, pd.Series):
            y_data = data.values
            X_data = data.values.reshape(-1, 1)
        else:  # numpy array
            X_data = data
            if target_column is not None and data.ndim > 1:
                y_data = data[:, target_column]
            else:
                y_data = data
                
        # Create sequences
        X, y = [], []
        for i in range(0, len(X_data) - sequence_length - forecast_horizon + 1, step):
            X.append(X_data[i:i+sequence_length])
            if forecast_horizon == 1:
                y.append(y_data[i+sequence_length])
            else:
                y.append(y_data[i+sequence_length:i+sequence_length+forecast_horizon])
                
        return np.array(X), np.array(y)
    
    @staticmethod
    def add_technical_indicators(
        df: pd.DataFrame,
        indicators: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Add technical indicators to a DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame with OHLCV data
            indicators (List[Dict[str, Any]]): List of indicator configurations
            
        Returns:
            pd.DataFrame: DataFrame with added indicators
        """
        result_df = df.copy()
        
        for indicator in indicators:
            indicator_type = indicator.get('type', '').lower()
            
            if indicator_type == 'sma':
                # Simple Moving Average
                window = indicator.get('window', 20)
                source = indicator.get('source', 'close')
                name = indicator.get('name', f'sma_{window}')
                
                if source in result_df.columns:
                    result_df[name] = result_df[source].rolling(window=window).mean()
                    
            elif indicator_type == 'ema':
                # Exponential Moving Average
                window = indicator.get('window', 20)
                source = indicator.get('source', 'close')
                name = indicator.get('name', f'ema_{window}')
                
                if source in result_df.columns:
                    result_df[name] = result_df[source].ewm(span=window, adjust=False).mean()
                    
            elif indicator_type == 'rsi':
                # Relative Strength Index
                window = indicator.get('window', 14)
                source = indicator.get('source', 'close')
                name = indicator.get('name', f'rsi_{window}')
                
                if source in result_df.columns:
                    delta = result_df[source].diff()
                    gain = delta.where(delta > 0, 0)
                    loss = -delta.where(delta < 0, 0)
                    
                    avg_gain = gain.rolling(window=window).mean()
                    avg_loss = loss.rolling(window=window).mean()
                    
                    rs = avg_gain / avg_loss
                    result_df[name] = 100 - (100 / (1 + rs))
                    
            elif indicator_type == 'macd':
                # MACD (Moving Average Convergence Divergence)
                fast_period = indicator.get('fast_period', 12)
                slow_period = indicator.get('slow_period', 26)
                signal_period = indicator.get('signal_period', 9)
                source = indicator.get('source', 'close')
                
                if source in result_df.columns:
                    fast_ema = result_df[source].ewm(span=fast_period, adjust=False).mean()
                    slow_ema = result_df[source].ewm(span=slow_period, adjust=False).mean()
                    
                    macd_line = fast_ema - slow_ema
                    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
                    histogram = macd_line - signal_line
                    
                    result_df[f'macd_line'] = macd_line
                    result_df[f'macd_signal'] = signal_line
                    result_df[f'macd_histogram'] = histogram
                    
            elif indicator_type == 'bollinger':
                # Bollinger Bands
                window = indicator.get('window', 20)
                num_std = indicator.get('num_std', 2)
                source = indicator.get('source', 'close')
                
                if source in result_df.columns:
                    middle_band = result_df[source].rolling(window=window).mean()
                    std_dev = result_df[source].rolling(window=window).std()
                    
                    result_df[f'bb_middle'] = middle_band
                    result_df[f'bb_upper'] = middle_band + (std_dev * num_std)
                    result_df[f'bb_lower'] = middle_band - (std_dev * num_std)
                    
            elif indicator_type == 'custom':
                # Custom indicator using provided function
                func = indicator.get('function')
                name = indicator.get('name', 'custom_indicator')
                
                if callable(func):
                    result_df[name] = func(result_df)
                    
        return result_df
    
    @staticmethod
    def handle_missing_values(
        df: pd.DataFrame,
        method: str = 'ffill',
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.
        
        Args:
            df (pd.DataFrame): Input DataFrame
            method (str): Method to handle missing values
                ('ffill', 'bfill', 'interpolate', 'drop', 'value')
            columns (Optional[List[str]]): Columns to process (None for all)
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        result_df = df.copy()
        
        # Select columns to process
        cols_to_process = columns if columns is not None else result_df.columns
        
        if method == 'ffill':
            # Forward fill
            result_df[cols_to_process] = result_df[cols_to_process].fillna(method='ffill')
        elif method == 'bfill':
            # Backward fill
            result_df[cols_to_process] = result_df[cols_to_process].fillna(method='bfill')
        elif method == 'interpolate':
            # Interpolate
            result_df[cols_to_process] = result_df[cols_to_process].interpolate()
        elif method == 'drop':
            # Drop rows with missing values
            result_df = result_df.dropna(subset=cols_to_process)
        elif method.startswith('value:'):
            # Fill with specific value
            try:
                fill_value = float(method.split(':')[1])
                result_df[cols_to_process] = result_df[cols_to_process].fillna(fill_value)
            except (IndexError, ValueError):
                logger.warning(f"Invalid value method: {method}, using 0 instead")
                result_df[cols_to_process] = result_df[cols_to_process].fillna(0)
        else:
            logger.warning(f"Unknown method: {method}, using forward fill")
            result_df[cols_to_process] = result_df[cols_to_process].fillna(method='ffill')
            
        return result_df


# Create a singleton instance
data_transformer = DataTransformer() 