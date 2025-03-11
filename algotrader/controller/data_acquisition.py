"""
Market data acquisition and processing module.
"""
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import MetaTrader5 as mt5
from ..config.settings import get_config
from ..integrations.mt5.client import MT5Client
from ..integrations.external_data.investpy import InvestpyClient
from ..integrations.external_data.forex_factory import ForexFactoryClient
from ..integrations.external_data.social_media import SocialMediaClient
from ..utils.logger import get_logger
from ..utils.data_transformations import DataTransformer
from ..utils.validation import Validator, ValidationError

logger = get_logger(__name__)

class DataAcquisitionManager:
    """Manages market data acquisition from multiple sources."""
    
    def __init__(self):
        """Initialize the data acquisition manager."""
        self.config = get_config()
        self.mt5_client = MT5Client()
        self.investpy_client = InvestpyClient()
        self.forex_factory_client = ForexFactoryClient()
        self.social_media_client = SocialMediaClient()
        self.data_transformer = DataTransformer()
        
        # Initialize MT5 client
        if not self.mt5_client.initialize():
            logger.warning("Failed to initialize MT5 client during DataAcquisitionManager initialization")
    
    def get_market_data(
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
        # Log appropriate message based on retrieval method
        if start_pos is not None:
            end_pos_str = f" to {end_pos}" if end_pos is not None else ""
            logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}, from position: {start_pos}{end_pos_str}")
        else:
            time_range = f"from: {start_time} to: {end_time}" if start_time else f"last 30 days to: {end_time or 'now'}"
            logger.info(f"Retrieving market data for {symbol}, timeframe: {timeframe}, {time_range}")
        
        try:
            # Validate input parameters
            self._validate_market_data_params(symbol, timeframe, start_time, end_time, start_pos, end_pos)
            
            # Ensure MT5 client is connected
            if not self.mt5_client.is_connected() and not self.mt5_client.connect():
                logger.error("Failed to connect to MT5")
                return pd.DataFrame()
            
            # Retrieve market data from MT5
            df = self.mt5_client.get_rates(
                symbol=symbol, 
                timeframe=timeframe, 
                start_time=start_time, 
                end_time=end_time,
                start_pos=start_pos,
                end_pos=end_pos,
                include_volume=include_volume
            )
            
            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
                
            # Clean the data
            df = self._clean_market_data(df)
            
            # Handle missing values
            df = self._handle_missing_values(df)
            
            # Normalize data if needed
            # Note: Normalization is typically done during strategy execution, not during data acquisition
            
            logger.info(f"Successfully retrieved {len(df)} records for {symbol}")
            return df
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            logger.exception(f"Error retrieving market data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _validate_market_data_params(
        self, 
        symbol: str, 
        timeframe: str, 
        start_time: Optional[datetime], 
        end_time: Optional[datetime],
        start_pos: Optional[int],
        end_pos: Optional[int]
    ) -> None:
        """
        Validate market data parameters.
        
        Args:
            symbol (str): Trading symbol
            timeframe (str): Timeframe
            start_time (Optional[datetime]): Start time
            end_time (Optional[datetime]): End time
            start_pos (Optional[int]): Start position
            end_pos (Optional[int]): End position
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
            
        # Validate timeframe
        valid_timeframes = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M10', 'M12', 'M15', 
                           'M20', 'M30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12', 
                           'D1', 'W1', 'MN1']
        if timeframe.upper() not in valid_timeframes:
            raise ValidationError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")
            
        # Validate start_time
        if start_time is not None and not isinstance(start_time, datetime):
            raise ValidationError("start_time must be a datetime object")
            
        # Validate end_time if provided
        if end_time is not None and not isinstance(end_time, datetime):
            raise ValidationError("end_time must be a datetime object")
                
        # Validate time range if both start_time and end_time are provided
        if end_time is not None and start_time is not None:
            if end_time <= start_time:
                raise ValidationError("end_time must be after start_time")
                
            # Validate time range is not too large
            time_diff = end_time - start_time
            max_days = 365  # Maximum allowed range in days
            if time_diff.days > max_days:
                raise ValidationError(f"Time range too large. Maximum allowed is {max_days} days")
        
        # Validate start_pos and end_pos
        if start_pos is not None and not isinstance(start_pos, int):
            raise ValidationError("start_pos must be an integer")
        if end_pos is not None and not isinstance(end_pos, int):
            raise ValidationError("end_pos must be an integer")
        
        if start_pos is not None and end_pos is not None:
            if start_pos > end_pos:
                raise ValidationError("start_pos must be less than or equal to end_pos")
            
        # Ensure either time-based or position-based parameters are provided
        if start_time is None and end_time is None and start_pos is None:
            raise ValidationError("Either start_time/end_time or start_pos/end_pos must be provided")
    
    def _clean_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean market data.
        
        Args:
            df (pd.DataFrame): Market data DataFrame
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by datetime
        df = df.sort_index()
        
        # Remove rows with negative or zero prices
        for col in ['Open', 'High', 'Low', 'Close']:
            if col in df.columns:
                df = df[df[col] > 0]
                
        # Ensure High is the highest price
        if all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
            price_cols = ['Open', 'High', 'Low', 'Close']
            df['High'] = df[price_cols].max(axis=1)
            
            # Ensure Low is the lowest price
            df['Low'] = df[price_cols].min(axis=1)
            
            # Ensure High >= Open, Close and Low <= Open, Close
            df['High'] = df[['High', 'Open', 'Close']].max(axis=1)
            df['Low'] = df[['Low', 'Open', 'Close']].min(axis=1)
        
        # Remove rows with abnormal volume if Volume column exists
        if 'Volume' in df.columns:
            # Remove zero or negative volume
            df = df[df['Volume'] > 0]
            
            # Remove outliers (e.g., volume > 3 standard deviations from mean)
            mean_volume = df['Volume'].mean()
            std_volume = df['Volume'].std()
            df = df[df['Volume'] <= mean_volume + 3 * std_volume]
            
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in market data.
        
        Args:
            df (pd.DataFrame): Market data DataFrame
            
        Returns:
            pd.DataFrame: DataFrame with handled missing values
        """
        if df.empty:
            return df
            
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Check for missing values
        if not df.isna().any().any():
            return df
            
        # Fill missing values in OHLC columns with forward fill then backward fill
        ohlc_cols = [col for col in ['Open', 'High', 'Low', 'Close'] if col in df.columns]
        if ohlc_cols:
            # Handle each column individually to avoid linter errors
            for col in ohlc_cols:
                # Forward fill first
                df[col] = df[col].ffill()
                # Then backward fill any remaining NaNs
                df[col] = df[col].bfill()
            
        # Fill missing values in Volume column with zeros
        if 'Volume' in df.columns and df['Volume'].isna().any():
            df['Volume'] = df['Volume'].fillna(0)
            
        return df
    
    def get_fundamental_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        data_sources: Optional[List[str]] = None,
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve fundamental data for a symbol from multiple sources.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (Optional[datetime]): End date (defaults to current date if None)
            data_sources (Optional[List[str]]): List of data sources to use
                Options: 'investpy', 'forex_factory', 'social_media', 'all'
            include_sentiment (bool): Whether to include sentiment data
            
        Returns:
            Dict[str, Any]: Fundamental data including:
                - company_info: Company information (if available)
                - economic_events: Economic calendar events affecting the symbol
                - sentiment: Social media sentiment data (if include_sentiment is True)
                - market_sentiment: Market sentiment data from trading platforms
                - source_metadata: Information about data sources used
        """
        logger.info(f"Retrieving fundamental data for {symbol} from {start_date} to {end_date or datetime.now()}")
        
        # Set default end_date if not provided
        if end_date is None:
            end_date = datetime.now()
            
        # Validate inputs
        self._validate_fundamental_data_params(symbol, start_date, end_date)
        
        # Determine which data sources to use
        available_sources = ['investpy', 'forex_factory', 'social_media']
        if data_sources is None or 'all' in data_sources:
            data_sources = available_sources
        else:
            # Filter to only include valid sources
            data_sources = [source for source in data_sources if source in available_sources]
            
        if not data_sources:
            logger.warning("No valid data sources specified for fundamental data retrieval")
            return {}
            
        logger.info(f"Using data sources: {', '.join(data_sources)}")
        
        # Initialize result dictionary
        result = {
            'company_info': {},
            'economic_events': pd.DataFrame(),
            'sentiment': {},
            'market_sentiment': {},
            'source_metadata': {
                'sources_used': data_sources,
                'retrieval_time': datetime.now(),
                'time_range': {
                    'start': start_date,
                    'end': end_date
                }
            }
        }
        
        # Retrieve data from each source
        if 'investpy' in data_sources:
            self._get_investpy_data(symbol, start_date, end_date, result)
            
        if 'forex_factory' in data_sources:
            self._get_forex_factory_data(symbol, start_date, end_date, result)
            
        if 'social_media' in data_sources and include_sentiment:
            self._get_social_media_data(symbol, start_date, end_date, result)
            
        # Aggregate and verify data
        self._aggregate_fundamental_data(result)
        self._verify_fundamental_data(result)
        
        return result
        
    def _validate_fundamental_data_params(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """
        Validate parameters for fundamental data retrieval.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            
        Raises:
            ValidationError: If parameters are invalid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Symbol must be a non-empty string")
            
        # Validate dates
        if not isinstance(start_date, datetime):
            raise ValidationError("Start date must be a datetime object")
            
        if not isinstance(end_date, datetime):
            raise ValidationError("End date must be a datetime object")
            
        if end_date < start_date:
            raise ValidationError("End date must be after start date")
            
        # Check if date range is too large (e.g., more than 1 year)
        max_days = 365
        if (end_date - start_date).days > max_days:
            raise ValidationError(f"Date range exceeds maximum of {max_days} days")
    
    def _get_investpy_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from Investpy and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving Investpy data for {symbol}")
        
        try:
            # Get company information
            company_info = self.investpy_client.get_company_info(symbol)
            if company_info:
                result['company_info'].update(company_info)
                
            # Get economic calendar events
            calendar_data = self.investpy_client.get_economic_calendar(
                start_date=start_date,
                end_date=end_date
            )
            
            if not calendar_data.empty:
                # Filter events that might affect this symbol
                # This is a simplified approach - in a real implementation,
                # you would need more sophisticated filtering
                if 'USD' in symbol:
                    calendar_data = calendar_data[calendar_data['country'] == 'United States']
                elif 'EUR' in symbol:
                    calendar_data = calendar_data[calendar_data['country'].isin(['Eurozone', 'Germany', 'France'])]
                # Add more currency filters as needed
                
                result['economic_events'] = pd.concat([result['economic_events'], calendar_data])
                
        except Exception as e:
            logger.error(f"Error retrieving Investpy data: {str(e)}")
    
    def _get_forex_factory_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from Forex Factory and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving Forex Factory data for {symbol}")
        
        try:
            # Extract currencies from symbol (assuming format like 'EURUSD')
            currencies = []
            if len(symbol) >= 6:
                base_currency = symbol[0:3]
                quote_currency = symbol[3:6]
                currencies = [base_currency, quote_currency]
            
            # Get calendar events
            if currencies:
                calendar_data = self.forex_factory_client.get_calendar(
                    start_date=start_date,
                    end_date=end_date,
                    currencies=currencies
                )
                
                if not calendar_data.empty:
                    result['economic_events'] = pd.concat([result['economic_events'], calendar_data])
            
            # Get market sentiment
            if len(symbol) >= 6:
                # Format symbol for sentiment query (e.g., 'EUR/USD')
                formatted_symbol = f"{symbol[0:3]}/{symbol[3:6]}"
                sentiment_data = self.forex_factory_client.get_market_sentiment(formatted_symbol)
                
                if sentiment_data:
                    result['market_sentiment'].update({
                        'forex_factory': sentiment_data
                    })
                    
        except Exception as e:
            logger.error(f"Error retrieving Forex Factory data: {str(e)}")
    
    def _get_social_media_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        result: Dict[str, Any]
    ) -> None:
        """
        Retrieve data from social media and add to result.
        
        Args:
            symbol (str): Trading symbol
            start_date (datetime): Start date
            end_date (datetime): End date
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info(f"Retrieving social media data for {symbol}")
        
        try:
            # Calculate lookback days from start_date to end_date
            lookback_days = (end_date - start_date).days
            lookback_days = max(1, lookback_days)  # Ensure at least 1 day
            
            # Get sentiment data
            sentiment_data = self.social_media_client.get_sentiment(
                symbol=symbol,
                lookback_days=lookback_days
            )
            
            if sentiment_data:
                result['sentiment'].update({
                    'social_media': sentiment_data
                })
                
            # Get mentions history
            mentions_data = self.social_media_client.get_mentions_history(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not mentions_data.empty:
                result['sentiment']['mentions_history'] = mentions_data
                
        except Exception as e:
            logger.error(f"Error retrieving social media data: {str(e)}")
    
    def _aggregate_fundamental_data(self, result: Dict[str, Any]) -> None:
        """
        Aggregate fundamental data from multiple sources.
        
        Args:
            result (Dict[str, Any]): Result dictionary to update
        """
        logger.info("Aggregating fundamental data from multiple sources")
        
        # Deduplicate economic events
        if not result['economic_events'].empty:
            # Sort by date and importance
            result['economic_events'] = result['economic_events'].sort_values(
                by=['date', 'importance'],
                ascending=[True, False]
            )
            
            # Remove duplicates, keeping the first occurrence (highest importance)
            if 'event' in result['economic_events'].columns:
                result['economic_events'] = result['economic_events'].drop_duplicates(
                    subset=['date', 'event'],
                    keep='first'
                )
                
        # Aggregate sentiment data
        if result['sentiment'] and 'social_media' in result['sentiment']:
            # Calculate overall sentiment score (simplified example)
            social_sentiment = result['sentiment']['social_media']
            market_sentiment = result['market_sentiment'].get('forex_factory', {})
            
            # Only calculate if we have both sources
            if social_sentiment and market_sentiment:
                # Simple weighted average (adjust weights as needed)
                result['sentiment']['aggregated'] = {
                    'bullish': (social_sentiment.get('bullish', 0) * 0.7 + 
                               market_sentiment.get('bullish', 0) * 0.3),
                    'bearish': (social_sentiment.get('bearish', 0) * 0.7 + 
                               market_sentiment.get('bearish', 0) * 0.3),
                    'neutral': (social_sentiment.get('neutral', 0) * 0.7 + 
                               market_sentiment.get('neutral', 0) * 0.3)
                }
    
    def _verify_fundamental_data(self, result: Dict[str, Any]) -> None:
        """
        Verify fundamental data for consistency and quality.
        
        Args:
            result (Dict[str, Any]): Result dictionary to verify
        """
        logger.info("Verifying fundamental data quality")
        
        # Check if we have any data
        has_company_info = bool(result['company_info'])
        has_economic_events = not result['economic_events'].empty
        has_sentiment = bool(result['sentiment'])
        has_market_sentiment = bool(result['market_sentiment'])
        
        # Add data quality metrics
        result['source_metadata']['data_quality'] = {
            'has_company_info': has_company_info,
            'has_economic_events': has_economic_events,
            'has_sentiment': has_sentiment,
            'has_market_sentiment': has_market_sentiment,
            'completeness_score': sum([
                has_company_info,
                has_economic_events,
                has_sentiment,
                has_market_sentiment
            ]) / 4.0  # Simple completeness score
        }
        
        # Log data quality
        logger.info(f"Fundamental data quality score: {result['source_metadata']['data_quality']['completeness_score']:.2f}")
        
        # Add warnings for missing data
        warnings = []
        if not has_company_info:
            warnings.append("Company information is missing")
        if not has_economic_events:
            warnings.append("Economic events data is missing")
        if not has_sentiment:
            warnings.append("Sentiment data is missing")
        if not has_market_sentiment:
            warnings.append("Market sentiment data is missing")
            
        if warnings:
            result['source_metadata']['warnings'] = warnings
            logger.warning(f"Fundamental data warnings: {', '.join(warnings)}")
    
    def get_economic_calendar(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        currencies: Optional[List[str]] = None,
        importance: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve economic calendar events.
        
        Args:
            start_date (datetime): Start date
            end_date (Optional[datetime]): End date
            currencies (Optional[List[str]]): List of currencies to filter
            importance (Optional[str]): Event importance level
            
        Returns:
            pd.DataFrame: Economic calendar events
        """
        # TODO: Implement economic calendar retrieval
        # TODO: Add event filtering
        # TODO: Add event categorization
        # TODO: Add event impact analysis
        return pd.DataFrame()
    
    def get_sentiment_data(
        self,
        symbol: str,
        lookback_days: int = 7
    ) -> Dict[str, float]:
        """
        Retrieve market sentiment data.
        
        Args:
            symbol (str): Trading symbol
            lookback_days (int): Number of days to look back
            
        Returns:
            Dict[str, float]: Sentiment scores
        """
        # TODO: Implement sentiment data retrieval
        # TODO: Add sentiment analysis
        # TODO: Add sentiment aggregation
        # TODO: Add sentiment validation
        return {}
    
    def get_tick_data(
        self,
        symbol: str,
        num_ticks: int = 1000
    ) -> pd.DataFrame:
        """
        Retrieve latest tick data.
        
        Args:
            symbol (str): Trading symbol
            num_ticks (int): Number of ticks to retrieve
            
        Returns:
            pd.DataFrame: Tick data
        """
        # TODO: Implement tick data retrieval
        # TODO: Add tick validation
        # TODO: Add tick processing
        # TODO: Add tick aggregation
        return pd.DataFrame()
    
    def get_order_book(
        self,
        symbol: str,
        depth: int = 20
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieve order book data.
        
        Args:
            symbol (str): Trading symbol
            depth (int): Order book depth
            
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: Bid and ask order books
        """
        # TODO: Implement order book retrieval
        # TODO: Add order book validation
        # TODO: Add order book analysis
        # TODO: Add order book visualization
        return pd.DataFrame(), pd.DataFrame()
    
    def subscribe_to_market_data(
        self,
        symbols: List[str],
        callback: Callable
    ) -> bool:
        """
        Subscribe to real-time market data.
        
        Args:
            symbols (List[str]): List of symbols
            callback (Callable): Callback function for data updates
            
        Returns:
            bool: True if subscription successful, False otherwise
        """
        # TODO: Implement market data subscription
        # TODO: Add subscription management
        # TODO: Add data streaming
        # TODO: Add connection monitoring
        return False
    
    def unsubscribe_from_market_data(
        self,
        symbols: Optional[List[str]] = None
    ) -> bool:
        """
        Unsubscribe from market data.
        
        Args:
            symbols (Optional[List[str]]): List of symbols to unsubscribe
            
        Returns:
            bool: True if unsubscription successful, False otherwise
        """
        # TODO: Implement market data unsubscription
        # TODO: Add subscription cleanup
        # TODO: Add connection cleanup
        return False 