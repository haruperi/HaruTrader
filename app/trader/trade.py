"""
Trade placement and management module.
"""
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from enum import Enum
import asyncio
import MetaTrader5 as mt5
from app.config.settings import get_config
from app.core.mt5_data import MT5Client
from app.utils.logger import get_logger
from app.core.notification import notify_trade, notify_error
from .risk import RiskManager

logger = get_logger(__name__)

class OrderType(Enum):
    """Order types supported by the system."""
    MARKET_BUY = "market_buy"
    MARKET_SELL = "market_sell"
    LIMIT_BUY = "limit_buy"
    LIMIT_SELL = "limit_sell"
    STOP_BUY = "stop_buy"
    STOP_SELL = "stop_sell"

class OrderStatus(Enum):
    """Order status types."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

class OrderManager:
    """Manages order placement and tracking."""
    
    def __init__(self):
        """Initialize the order manager."""
        self.config = get_config()
        self.mt5_client = MT5Client()
        self.trading_config = self.config['trading']
    
    def place_market_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol (str): Trading symbol
            order_type (OrderType): Type of order
            volume (float): Order volume
            stop_loss (Optional[float]): Stop loss price
            take_profit (Optional[float]): Take profit price
            comment (Optional[str]): Order comment
            
        Returns:
            Dict[str, Any]: Order details if successful
        """
        logger.info(f"Placing market order: {symbol}, {order_type.value}, volume={volume}")
        
        # Validate order parameters
        validation_result = self.validate_order_parameters(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if not all(validation_result.values()):
            invalid_params = [k for k, v in validation_result.items() if not v]
            error_msg = f"Invalid order parameters: {', '.join(invalid_params)}"
            logger.error(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="order_validation_error",
                message=f"Order validation failed for {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "invalid_params": invalid_params
                }
            ))
            
            return {"success": False, "error": error_msg}
        
        # Perform risk checks
        risk_manager = RiskManager()
        risk_check = risk_manager.validate_risk_parameters(
            symbol=symbol,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if not all(risk_check.values()):
            risk_issues = [k for k, v in risk_check.items() if not v]
            error_msg = f"Risk check failed: {', '.join(risk_issues)}"
            logger.error(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="risk_check_error",
                message=f"Risk check failed for {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "risk_issues": risk_issues
                }
            ))
            
            return {"success": False, "error": error_msg}
        
        # Determine MT5 order type
        mt5_order_type = None
        if order_type == OrderType.MARKET_BUY:
            mt5_order_type = mt5.ORDER_TYPE_BUY
        elif order_type == OrderType.MARKET_SELL:
            mt5_order_type = mt5.ORDER_TYPE_SELL
        else:
            error_msg = f"Invalid market order type: {order_type.value}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Get current price
        # Ensure MT5 is connected
        if not self.mt5_client.is_connected():
            connection_result = self.mt5_client.connect()
            if not connection_result:
                error_msg = "Failed to connect to MT5 terminal"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
        # Get symbol information using MT5 API
        try:
            symbol_tick = mt5.symbol_info_tick(symbol)
            if symbol_tick is None:
                error_msg = f"Failed to get tick data for symbol {symbol}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Set price based on order type
            price = symbol_tick.ask if mt5_order_type == mt5.ORDER_TYPE_BUY else symbol_tick.bid
            
        except Exception as e:
            error_msg = f"Error getting symbol information: {str(e)}"
            logger.exception(error_msg)
            return {"success": False, "error": error_msg}
        
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": self.trading_config.get("price_deviation", 10),
            "magic": self.trading_config.get("magic_number", 123456),
            "comment": comment or f"Market {order_type.value}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request["sl"] = stop_loss
        
        if take_profit is not None:
            request["tp"] = take_profit
        
        # Send order to MT5
        try:
            # Execute the order using MT5 API
            order_result = mt5.order_send(request)
            
            if order_result is None:
                error_msg = "Failed to send order, check MT5 connection"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            if order_result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Market order placed successfully: ticket={order_result.order}")
                
                # Return order details
                order_details = {
                    "success": True,
                    "order_id": order_result.order,
                    "symbol": symbol,
                    "type": order_type.value,
                    "volume": volume,
                    "price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "comment": comment,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Send trade notification
                asyncio.create_task(notify_trade(
                    trade_action="opened",
                    message=f"New {order_type.value} order placed for {symbol}",
                    trade_data={
                        "symbol": symbol,
                        "type": order_type.value,
                        "entry": price,
                        "sl": stop_loss if stop_loss is not None else 0.0,
                        "tp": take_profit if take_profit is not None else 0.0,
                        "volume": volume,
                        "time": datetime.now().isoformat(),
                        "order_id": order_result.order
                    },
                    priority="high"
                ))
                
                return order_details
            else:
                error_msg = f"Order failed with error code: {order_result.retcode}, {order_result.comment}"
                logger.error(error_msg)
                
                # Send error notification
                asyncio.create_task(notify_error(
                    error_type="order_execution_error",
                    message=f"Order execution failed for {symbol}",
                    error_data={
                        "symbol": symbol,
                        "order_type": order_type.value,
                        "volume": volume,
                        "error_code": order_result.retcode,
                        "error_message": order_result.comment
                    }
                ))
                
                return {"success": False, "error": error_msg, "retcode": order_result.retcode}
                
        except Exception as e:
            error_msg = f"Exception occurred while placing market order: {str(e)}"
            logger.exception(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="order_exception",
                message=f"Exception while placing order for {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "exception": str(e)
                }
            ))
            
            return {"success": False, "error": error_msg}
    
    def place_pending_order(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        price: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        expiry: Optional[datetime] = None,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Place a pending order.
        
        Args:
            symbol (str): Trading symbol
            order_type (OrderType): Type of order
            volume (float): Order volume
            price (float): Order price
            stop_loss (Optional[float]): Stop loss price
            take_profit (Optional[float]): Take profit price
            expiry (Optional[datetime]): Order expiry time
            comment (Optional[str]): Order comment
            
        Returns:
            Dict[str, Any]: Order details if successful
        """
        logger.info(f"Placing pending order: {symbol}, {order_type.value}, volume={volume}, price={price}")
        
        # Validate order parameters
        validation_result = self.validate_order_parameters(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if not all(validation_result.values()):
            invalid_params = [k for k, v in validation_result.items() if not v]
            error_msg = f"Invalid order parameters: {', '.join(invalid_params)}"
            logger.error(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="order_validation_error",
                message=f"Pending order validation failed for {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "price": price,
                    "invalid_params": invalid_params
                }
            ))
            
            return {"success": False, "error": error_msg}
        
        # Perform risk checks
        risk_manager = RiskManager()
        risk_check = risk_manager.validate_risk_parameters(
            symbol=symbol,
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        if not all(risk_check.values()):
            risk_issues = [k for k, v in risk_check.items() if not v]
            error_msg = f"Risk check failed: {', '.join(risk_issues)}"
            logger.error(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="risk_check_error",
                message=f"Risk check failed for pending order on {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "price": price,
                    "risk_issues": risk_issues
                }
            ))
            
            return {"success": False, "error": error_msg}
        
        # Determine MT5 order type
        mt5_order_type = None
        if order_type == OrderType.LIMIT_BUY:
            mt5_order_type = mt5.ORDER_TYPE_BUY_LIMIT
        elif order_type == OrderType.LIMIT_SELL:
            mt5_order_type = mt5.ORDER_TYPE_SELL_LIMIT
        elif order_type == OrderType.STOP_BUY:
            mt5_order_type = mt5.ORDER_TYPE_BUY_STOP
        elif order_type == OrderType.STOP_SELL:
            mt5_order_type = mt5.ORDER_TYPE_SELL_STOP
        else:
            error_msg = f"Invalid pending order type: {order_type.value}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Ensure MT5 is connected
        if not self.mt5_client.is_connected():
            connection_result = self.mt5_client.connect()
            if not connection_result:
                error_msg = "Failed to connect to MT5 terminal"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
        
        # Validate price against current market price
        try:
            symbol_tick = mt5.symbol_info_tick(symbol)
            if symbol_tick is None:
                error_msg = f"Failed to get tick data for symbol {symbol}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            current_ask = symbol_tick.ask
            current_bid = symbol_tick.bid
            
            # Validate price based on order type
            if (order_type == OrderType.LIMIT_BUY and price >= current_ask) or \
               (order_type == OrderType.STOP_BUY and price <= current_ask) or \
               (order_type == OrderType.LIMIT_SELL and price <= current_bid) or \
               (order_type == OrderType.STOP_SELL and price >= current_bid):
                error_msg = f"Invalid price {price} for {order_type.value} order. Current ask: {current_ask}, bid: {current_bid}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"Error validating price: {str(e)}"
            logger.exception(error_msg)
            return {"success": False, "error": error_msg}
        
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": mt5_order_type,
            "price": price,
            "deviation": self.trading_config.get("price_deviation", 10),
            "magic": self.trading_config.get("magic_number", 123456),
            "comment": comment or f"Pending {order_type.value}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request["sl"] = stop_loss
        
        if take_profit is not None:
            request["tp"] = take_profit
        
        # Add expiry if provided
        if expiry is not None:
            # Validate expiry time is in the future
            if expiry <= datetime.now():
                error_msg = "Expiry time must be in the future"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
            
            # Convert datetime to timestamp (seconds since epoch)
            expiry_timestamp = int(expiry.timestamp())
            logger.debug(f"Setting expiry time: {expiry} (timestamp: {expiry_timestamp})")
            
            request["type_time"] = mt5.ORDER_TIME_SPECIFIED
            request["expiration"] = expiry_timestamp
        
        # Send order to MT5
        try:
            # Log the request for debugging
            logger.debug(f"Sending pending order request: {request}")
            
            # Execute the order using MT5 API
            order_result = mt5.order_send(request)
            
            # Log the result for debugging
            if order_result is not None:
                logger.debug(f"Order result: {order_result}")
                logger.debug(f"Order retcode: {order_result.retcode}")
            
            if order_result is None:
                error = mt5.last_error()
                error_msg = f"Failed to send pending order, check MT5 connection. Error: {error[0]} - {error[1]}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
            # Check if the order was successful (retcode 10009 is TRADE_RETCODE_DONE)
            if order_result.retcode == 10009:  # mt5.TRADE_RETCODE_DONE
                logger.info(f"Pending order placed successfully: ticket={order_result.order}")
                
                # Return order details
                order_details = {
                    "success": True,
                    "order_id": order_result.order,
                    "symbol": symbol,
                    "type": order_type.value,
                    "volume": volume,
                    "price": price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "expiry": expiry.isoformat() if expiry else None,
                    "comment": comment,
                    "timestamp": datetime.now().isoformat(),
                    "status": OrderStatus.PENDING.value
                }
                
                # Send trade notification
                asyncio.create_task(notify_trade(
                    trade_action="pending",
                    message=f"New {order_type.value} pending order placed for {symbol}",
                    trade_data={
                        "symbol": symbol,
                        "type": order_type.value,
                        "price": price,
                        "sl": stop_loss if stop_loss is not None else 0.0,
                        "tp": take_profit if take_profit is not None else 0.0,
                        "volume": volume,
                        "expiry": expiry.isoformat() if expiry else None,
                        "time": datetime.now().isoformat(),
                        "order_id": order_result.order
                    },
                    priority="medium"
                ))
                
                return order_details
            else:
                error_msg = f"Pending order failed with error code: {order_result.retcode}, {order_result.comment}"
                logger.error(error_msg)
                
                # Send error notification
                asyncio.create_task(notify_error(
                    error_type="order_execution_error",
                    message=f"Pending order execution failed for {symbol}",
                    error_data={
                        "symbol": symbol,
                        "order_type": order_type.value,
                        "volume": volume,
                        "price": price,
                        "error_code": order_result.retcode,
                        "error_message": order_result.comment
                    }
                ))
                
                return {"success": False, "error": error_msg, "retcode": order_result.retcode}
                
        except Exception as e:
            error_msg = f"Exception occurred while placing pending order: {str(e)}"
            logger.exception(error_msg)
            
            # Send error notification
            asyncio.create_task(notify_error(
                error_type="order_exception",
                message=f"Exception while placing pending order for {symbol}",
                error_data={
                    "symbol": symbol,
                    "order_type": order_type.value,
                    "volume": volume,
                    "price": price,
                    "exception": str(e)
                }
            ))
            
            return {"success": False, "error": error_msg}
    
    def modify_order(
        self,
        order_id: int,
        new_price: Optional[float] = None,
        new_stop_loss: Optional[float] = None,
        new_take_profit: Optional[float] = None,
        new_expiry: Optional[datetime] = None
    ) -> bool:
        """
        Modify an existing order.
        
        Args:
            order_id (int): Order identifier
            new_price (Optional[float]): New order price
            new_stop_loss (Optional[float]): New stop loss price
            new_take_profit (Optional[float]): New take profit price
            new_expiry (Optional[datetime]): New expiry time
            
        Returns:
            bool: True if modification successful
        """
        # TODO: Implement order modification
        # TODO: Add modification validation
        # TODO: Add partial modifications
        # TODO: Add modification history
        return False
    
    def cancel_order(
        self,
        order_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id (int): Order identifier
            reason (Optional[str]): Cancellation reason
            
        Returns:
            bool: True if cancellation successful
        """
        # TODO: Implement order cancellation
        # TODO: Add cancellation validation
        # TODO: Add cancellation history
        # TODO: Add cleanup tasks
        return False
    
    def get_order_status(
        self,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Get the current status of an order.
        
        Args:
            order_id (int): Order identifier
            
        Returns:
            Dict[str, Any]: Order status and details
        """
        # TODO: Implement order status check
        # TODO: Add status history
        # TODO: Add status notifications
        # TODO: Add status tracking
        return {}
    
    def get_pending_orders(
        self,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all pending orders.
        
        Args:
            symbol (Optional[str]): Filter by symbol
            
        Returns:
            List[Dict[str, Any]]: List of pending orders
        """
        # TODO: Implement pending orders retrieval
        # TODO: Add order filtering
        # TODO: Add order sorting
        # TODO: Add order grouping
        return []
    
    def calculate_position_size(
        self,
        symbol: str,
        risk_amount: float,
        stop_loss_pips: float
    ) -> float:
        """
        Calculate appropriate position size based on risk parameters.
        
        Args:
            symbol (str): Trading symbol
            risk_amount (float): Amount to risk
            stop_loss_pips (float): Stop loss in pips
            
        Returns:
            float: Calculated position size
        """
        # TODO: Implement position size calculation
        # TODO: Add risk validation
        # TODO: Add margin checks
        # TODO: Add position limits
        return 0.0
    
    def validate_order_parameters(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Dict[str, bool]:
        """
        Validate order parameters before placement.
        
        Args:
            symbol (str): Trading symbol
            order_type (OrderType): Type of order
            volume (float): Order volume
            price (Optional[float]): Order price
            stop_loss (Optional[float]): Stop loss price
            take_profit (Optional[float]): Take profit price
            
        Returns:
            Dict[str, bool]: Validation results for each parameter
        """
        logger.info(f"Validating order parameters: {symbol}, {order_type.value}, volume={volume}")
        
        validation_results = {
            "symbol_valid": True,
            "order_type_valid": True,
            "volume_valid": True,
            "price_valid": True,
            "stop_loss_valid": True,
            "take_profit_valid": True
        }
        
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            validation_results["symbol_valid"] = False
            logger.warning(f"Invalid symbol: {symbol}")
        
        # Validate order type
        if not isinstance(order_type, OrderType):
            validation_results["order_type_valid"] = False
            logger.warning(f"Invalid order type: {order_type}")
        
        # Validate volume
        if volume <= 0:
            validation_results["volume_valid"] = False
            logger.warning(f"Volume must be positive, got {volume}")
        
        # Validate price for pending orders
        if order_type in [OrderType.LIMIT_BUY, OrderType.LIMIT_SELL, OrderType.STOP_BUY, OrderType.STOP_SELL]:
            if price is None or price <= 0:
                validation_results["price_valid"] = False
                logger.warning(f"Price must be specified and positive for pending orders, got {price}")
        
        # Validate stop loss
        if stop_loss is not None and stop_loss <= 0:
            validation_results["stop_loss_valid"] = False
            logger.warning(f"Stop loss must be positive, got {stop_loss}")
        
        # Validate take profit
        if take_profit is not None and take_profit <= 0:
            validation_results["take_profit_valid"] = False
            logger.warning(f"Take profit must be positive, got {take_profit}")
        
        logger.info(f"Order parameter validation results: {validation_results}")
        return validation_results 