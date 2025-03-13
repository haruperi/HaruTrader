"""
Symbol screening functionality module.

This module provides functionality for scanning through a list of symbols
and identifying those that match specific strategy criteria.
"""
from typing import Dict, List, Optional, Union, Tuple, Any, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import concurrent.futures
from functools import partial

from app.utils.logger import get_logger
from app.core.mt5_data import DataAcquisitionManager
from .indicators import Indicators

logger = get_logger(__name__)

class ScreenerCondition:
    """
    Class representing a screening condition.
    
    This class defines a condition that can be used to screen symbols.
    """
    
    def __init__(
        self,
        name: str,
        condition_func: Callable[[pd.DataFrame], bool],
        description: str = "",
        timeframe: str = "H1"
    ):
        """
        Initialize a new screener condition.
        
        Args:
            name (str): Condition name
            condition_func (Callable[[pd.DataFrame], bool]): Function that evaluates the condition
            description (str, optional): Condition description
            timeframe (str, optional): Timeframe for the condition
        """
        self.name = name
        self.condition_func = condition_func
        self.description = description
        self.timeframe = timeframe
        
    def evaluate(self, data: pd.DataFrame) -> bool:
        """
        Evaluate the condition on the given data.
        
        Args:
            data (pd.DataFrame): Market data
            
        Returns:
            bool: True if the condition is met, False otherwise
        """
        try:
            return self.condition_func(data)
        except Exception as e:
            logger.exception(f"Error evaluating condition {self.name}: {str(e)}")
            return False

class Screener:
    """
    Symbol screening class.
    
    This class provides functionality for scanning through a list of symbols
    and identifying those that match specific strategy criteria.
    """
    
    def __init__(
        self,
        symbols: List[str],
        data_manager: DataAcquisitionManager,
        max_workers: int = 4
    ):
        """
        Initialize a new screener.
        
        Args:
            symbols (List[str]): List of symbols to screen
            data_manager (DataAcquisitionManager): Data acquisition manager
            max_workers (int, optional): Maximum number of concurrent workers
        """
        self.symbols = symbols
        self.data_manager = data_manager
        self.max_workers = max_workers
        self.conditions: Dict[str, List[ScreenerCondition]] = {}
        
        logger.info(f"Initialized screener with {len(symbols)} symbols")
        
    def add_condition(self, strategy_name: str, condition: ScreenerCondition) -> None:
        """
        Add a condition to the screener.
        
        Args:
            strategy_name (str): Strategy name
            condition (ScreenerCondition): Condition to add
        """
        if strategy_name not in self.conditions:
            self.conditions[strategy_name] = []
            
        self.conditions[strategy_name].append(condition)
        
        logger.info(f"Added condition '{condition.name}' to strategy '{strategy_name}'")
        
    def add_conditions(self, strategy_name: str, conditions: List[ScreenerCondition]) -> None:
        """
        Add multiple conditions to the screener.
        
        Args:
            strategy_name (str): Strategy name
            conditions (List[ScreenerCondition]): Conditions to add
        """
        for condition in conditions:
            self.add_condition(strategy_name, condition)
            
    def remove_condition(self, strategy_name: str, condition_name: str) -> bool:
        """
        Remove a condition from the screener.
        
        Args:
            strategy_name (str): Strategy name
            condition_name (str): Condition name
            
        Returns:
            bool: True if the condition was removed, False otherwise
        """
        if strategy_name not in self.conditions:
            logger.warning(f"Strategy '{strategy_name}' not found")
            return False
            
        for i, condition in enumerate(self.conditions[strategy_name]):
            if condition.name == condition_name:
                self.conditions[strategy_name].pop(i)
                logger.info(f"Removed condition '{condition_name}' from strategy '{strategy_name}'")
                return True
                
        logger.warning(f"Condition '{condition_name}' not found in strategy '{strategy_name}'")
        return False
        
    def clear_conditions(self, strategy_name: Optional[str] = None) -> None:
        """
        Clear all conditions for a strategy or all strategies.
        
        Args:
            strategy_name (Optional[str], optional): Strategy name, or None to clear all
        """
        if strategy_name is None:
            self.conditions = {}
            logger.info("Cleared all conditions")
        elif strategy_name in self.conditions:
            self.conditions[strategy_name] = []
            logger.info(f"Cleared conditions for strategy '{strategy_name}'")
        else:
            logger.warning(f"Strategy '{strategy_name}' not found")
            
    def get_timeframes(self) -> List[str]:
        """
        Get all unique timeframes used by the conditions.
        
        Returns:
            List[str]: List of unique timeframes
        """
        timeframes = set()
        
        for strategy_conditions in self.conditions.values():
            for condition in strategy_conditions:
                timeframes.add(condition.timeframe)
                
        return list(timeframes)
        
    def _screen_symbol(
        self,
        symbol: str,
        strategy_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[str]]:
        """
        Screen a single symbol against all conditions or conditions for a specific strategy.
        
        Args:
            symbol (str): Symbol to screen
            strategy_name (Optional[str], optional): Strategy name, or None for all strategies
            start_time (Optional[datetime], optional): Start time for data
            end_time (Optional[datetime], optional): End time for data
            
        Returns:
            Dict[str, List[str]]: Dictionary mapping strategy names to lists of matched condition names
        """
        result: Dict[str, List[str]] = {}
        
        # Get all required timeframes
        timeframes = self.get_timeframes()
        
        # Get market data for each timeframe
        market_data = {}
        for timeframe in timeframes:
            data = self.data_manager.get_market_data(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time
            )
            
            if data.empty:
                logger.warning(f"No data for {symbol} on timeframe {timeframe}")
                continue
                
            market_data[timeframe] = data
            
        # If no data is available, return empty result
        if not market_data:
            logger.warning(f"No data available for {symbol}")
            return result
            
        # Evaluate conditions
        strategies_to_check = [strategy_name] if strategy_name else list(self.conditions.keys())
        
        for strategy in strategies_to_check:
            if strategy not in self.conditions:
                continue
                
            matched_conditions = []
            
            for condition in self.conditions[strategy]:
                if condition.timeframe not in market_data:
                    continue
                    
                if condition.evaluate(market_data[condition.timeframe]):
                    matched_conditions.append(condition.name)
                    
            if matched_conditions:
                result[strategy] = matched_conditions
                
        return result
        
    def screen(
        self,
        strategy_name: Optional[str] = None,
        symbols: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_conditions: int = 1
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        Screen symbols against all conditions or conditions for a specific strategy.
        
        Args:
            strategy_name (Optional[str], optional): Strategy name, or None for all strategies
            symbols (Optional[List[str]], optional): Symbols to screen, or None for all symbols
            start_time (Optional[datetime], optional): Start time for data
            end_time (Optional[datetime], optional): End time for data
            min_conditions (int, optional): Minimum number of conditions that must be met
            
        Returns:
            Dict[str, Dict[str, List[str]]]: Dictionary mapping symbols to dictionaries mapping
                strategy names to lists of matched condition names
        """
        symbols_to_check = symbols if symbols else self.symbols
        
        if not symbols_to_check:
            logger.warning("No symbols to screen")
            return {}
            
        if not self.conditions:
            logger.warning("No conditions to check")
            return {}
            
        logger.info(f"Screening {len(symbols_to_check)} symbols against {sum(len(conditions) for conditions in self.conditions.values())} conditions")
        
        # Create a partial function for concurrent execution
        screen_func = partial(
            self._screen_symbol,
            strategy_name=strategy_name,
            start_time=start_time,
            end_time=end_time
        )
        
        # Execute screening in parallel
        results: Dict[str, Dict[str, List[str]]] = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {executor.submit(screen_func, symbol): symbol for symbol in symbols_to_check}
            
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                
                try:
                    symbol_result = future.result()
                    
                    # Check if the symbol meets the minimum number of conditions
                    total_conditions = sum(len(conditions) for conditions in symbol_result.values())
                    
                    if total_conditions >= min_conditions:
                        results[symbol] = symbol_result
                        
                except Exception as e:
                    logger.exception(f"Error screening symbol {symbol}: {str(e)}")
                    
        logger.info(f"Screening complete, found {len(results)} matching symbols")
        return results
        
    def create_summary(self, results: Dict[str, Dict[str, List[str]]]) -> pd.DataFrame:
        """
        Create a summary DataFrame from screening results.
        
        Args:
            results (Dict[str, Dict[str, List[str]]]): Screening results
            
        Returns:
            pd.DataFrame: Summary DataFrame
        """
        if not results:
            return pd.DataFrame()
            
        # Create a list of records
        records = []
        
        for symbol, symbol_results in results.items():
            for strategy, conditions in symbol_results.items():
                records.append({
                    'Symbol': symbol,
                    'Strategy': strategy,
                    'Conditions': ', '.join(conditions),
                    'Count': len(conditions)
                })
                
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Sort by symbol and strategy
        if not df.empty:
            df = df.sort_values(['Symbol', 'Strategy'])
            
        return df
        
    @staticmethod
    def create_common_conditions() -> Dict[str, List[ScreenerCondition]]:
        """
        Create a dictionary of common screening conditions.
        
        Returns:
            Dict[str, List[ScreenerCondition]]: Dictionary mapping strategy names to lists of conditions
        """
        conditions: Dict[str, List[ScreenerCondition]] = {}
        
        # Trend Following Strategy Conditions
        trend_following = []
        
        # EMA Crossover (Fast EMA crosses above Slow EMA)
        trend_following.append(ScreenerCondition(
            name="EMA Crossover",
            condition_func=lambda data: (
                Indicators.ema(data, 20).iloc[-2] <= Indicators.ema(data, 50).iloc[-2] and
                Indicators.ema(data, 20).iloc[-1] > Indicators.ema(data, 50).iloc[-1]
            ),
            description="Fast EMA (20) crosses above Slow EMA (50)",
            timeframe="H4"
        ))
        
        # Strong Trend (ADX > 25)
        trend_following.append(ScreenerCondition(
            name="Strong Trend",
            condition_func=lambda data: Indicators.adx(data).iloc[-1] > 25,
            description="ADX > 25 indicating a strong trend",
            timeframe="H4"
        ))
        
        # Price above 200 EMA
        trend_following.append(ScreenerCondition(
            name="Price Above 200 EMA",
            condition_func=lambda data: data['Close'].iloc[-1] > Indicators.ema(data, 200).iloc[-1],
            description="Price is above the 200 EMA, indicating a bullish trend",
            timeframe="D1"
        ))
        
        conditions["Trend Following"] = trend_following
        
        # Mean Reversion Strategy Conditions
        mean_reversion = []
        
        # Oversold RSI (RSI < 30)
        mean_reversion.append(ScreenerCondition(
            name="Oversold RSI",
            condition_func=lambda data: Indicators.rsi(data).iloc[-1] < 30,
            description="RSI < 30, indicating oversold conditions",
            timeframe="H4"
        ))
        
        # Price below Lower Bollinger Band
        mean_reversion.append(ScreenerCondition(
            name="Price Below Lower BB",
            condition_func=lambda data: (
                data['Close'].iloc[-1] < Indicators.bollinger_bands(data)[2].iloc[-1]
            ),
            description="Price is below the lower Bollinger Band",
            timeframe="H4"
        ))
        
        # Stochastic Oversold (Stochastic %K < 20)
        mean_reversion.append(ScreenerCondition(
            name="Stochastic Oversold",
            condition_func=lambda data: Indicators.stochastic(data)[0].iloc[-1] < 20,
            description="Stochastic %K < 20, indicating oversold conditions",
            timeframe="H4"
        ))
        
        conditions["Mean Reversion"] = mean_reversion
        
        # Breakout Strategy Conditions
        breakout = []
        
        # New 20-day High
        breakout.append(ScreenerCondition(
            name="New 20-day High",
            condition_func=lambda data: (
                data['Close'].iloc[-1] > data['High'].iloc[-21:-1].max()
            ),
            description="Price made a new 20-day high",
            timeframe="D1"
        ))
        
        # Increased Volume
        breakout.append(ScreenerCondition(
            name="Increased Volume",
            condition_func=lambda data: (
                'Volume' in data.columns and
                data['Volume'].iloc[-1] > data['Volume'].iloc[-21:-1].mean() * 1.5
            ),
            description="Volume is 50% higher than the 20-day average",
            timeframe="D1"
        ))
        
        # ADX Rising (ADX increasing over the last 3 periods)
        breakout.append(ScreenerCondition(
            name="ADX Rising",
            condition_func=lambda data: (
                Indicators.adx(data).iloc[-3] < Indicators.adx(data).iloc[-2] < Indicators.adx(data).iloc[-1]
            ),
            description="ADX is rising over the last 3 periods",
            timeframe="H4"
        ))
        
        conditions["Breakout"] = breakout
        
        return conditions 