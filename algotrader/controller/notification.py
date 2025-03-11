"""
Notification and alert management module.
"""
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from ..config.settings import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class NotificationManager:
    """Manages notifications and alerts through various channels."""
    
    def __init__(self):
        """Initialize the notification manager."""
        self.config = get_config()
        self.telegram_config = self.config['telegram']
        self.bot = Bot(self.telegram_config['bot_token'])
        self.chat_id = self.telegram_config['chat_id']
        
        # Message templates
        self.templates = {
            'trade_opened': (
                "🔔 Trade Opened\n"
                "Symbol: {symbol}\n"
                "Type: {type}\n"
                "Entry: {entry:.5f}\n"
                "Stop Loss: {sl:.5f}\n"
                "Take Profit: {tp:.5f}\n"
                "Volume: {volume:.2f}\n"
                "Time: {time}"
            ),
            'trade_closed': (
                "🔔 Trade Closed\n"
                "Symbol: {symbol}\n"
                "Type: {type}\n"
                "Entry: {entry:.5f}\n"
                "Exit: {exit:.5f}\n"
                "Profit: {profit:.2f} ({profit_pips:.1f} pips)\n"
                "Time: {time}"
            ),
            'error': (
                "⚠️ Error\n"
                "Type: {type}\n"
                "Message: {message}\n"
                "Time: {time}"
            ),
            'signal': (
                "📊 Trading Signal\n"
                "Symbol: {symbol}\n"
                "Strategy: {strategy}\n"
                "Action: {action}\n"
                "Price: {price:.5f}\n"
                "Time: {time}"
            ),
            'system': (
                "🔧 System Message\n"
                "Type: {type}\n"
                "Message: {message}\n"
                "Time: {time}"
            )
        }
    
    async def send_telegram_message(
        self,
        message: str,
        parse_mode: Optional[str] = None,
        disable_notification: bool = False
    ) -> bool:
        """
        Send a message via Telegram.
        
        Args:
            message (str): Message text
            parse_mode (Optional[str]): Message parse mode (HTML, Markdown)
            disable_notification (bool): Whether to send silently
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        # Message validation
        if not message or not isinstance(message, str):
            logger.error("Invalid message format: message must be a non-empty string")
            return False
            
        if parse_mode and parse_mode not in ["HTML", "Markdown", "MarkdownV2"]:
            logger.warning(f"Invalid parse_mode: {parse_mode}. Using default.")
            parse_mode = None
            
        # Retry configuration
        max_retries = self.config.get('notification', {}).get('max_retries', 3)
        retry_delay = self.config.get('notification', {}).get('retry_delay', 2)
        
        # Attempt to send message with retry mechanism
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending Telegram message (attempt {attempt+1}/{max_retries})")
                
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification
                )
                
                logger.info(f"Telegram message sent successfully")
                return True
                
            except TelegramError as e:
                logger.error(f"Telegram error on attempt {attempt+1}/{max_retries}: {str(e)}")
                
                # Check if we should retry based on error type
                if "retry after" in str(e).lower():
                    # Rate limit error, extract wait time if possible
                    try:
                        wait_time = int(str(e).split("retry after ")[1].split(" seconds")[0])
                        retry_delay = max(wait_time, retry_delay)
                    except (IndexError, ValueError):
                        pass
                
                # Don't retry for certain errors
                if "chat not found" in str(e).lower() or "bot was blocked" in str(e).lower():
                    logger.error(f"Fatal Telegram error, not retrying: {str(e)}")
                    return False
                    
                # Last attempt failed
                if attempt == max_retries - 1:
                    logger.error(f"Failed to send Telegram message after {max_retries} attempts")
                    return False
                    
                # Wait before retrying
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                
            except Exception as e:
                logger.exception(f"Unexpected error sending Telegram message: {str(e)}")
                return False
                
        return False
    
    async def send_trade_notification(
        self,
        trade_type: str,
        trade_data: Dict[str, Union[str, float, datetime]]
    ) -> bool:
        """
        Send a trade-related notification.
        
        Args:
            trade_type (str): Type of trade notification
            trade_data (Dict[str, Union[str, float, datetime]]): Trade data
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        # Trade type validation
        valid_trade_types = ['trade_opened', 'trade_closed', 'trade_modified']
        if trade_type not in valid_trade_types:
            logger.error(f"Invalid trade notification type: {trade_type}")
            return False
            
        # Trade data validation
        required_fields = {
            'trade_opened': ['symbol', 'type', 'entry', 'sl', 'tp', 'volume'],
            'trade_closed': ['symbol', 'type', 'entry', 'exit', 'profit', 'profit_pips'],
            'trade_modified': ['symbol', 'type', 'changes']
        }
        
        # Check for required fields
        for field in required_fields.get(trade_type, []):
            if field not in trade_data:
                logger.error(f"Missing required field '{field}' for {trade_type} notification")
                return False
                
        # Format notification based on priority
        priority = self.config.get('notification', {}).get('priority', {}).get('trade', 'normal')
        disable_notification = priority.lower() != 'high'
        
        # Format the message using the appropriate template
        message = self.format_message(trade_type, trade_data)
        if not message:
            logger.error(f"Failed to format {trade_type} notification")
            return False
            
        # Send the notification
        logger.info(f"Sending {trade_type} notification")
        return await self.send_telegram_message(
            message=message,
            parse_mode="HTML",
            disable_notification=disable_notification
        )
    
    async def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        error_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an error notification.
        
        Args:
            error_type (str): Type of error
            error_message (str): Error message
            error_data (Optional[Dict[str, Any]]): Additional error data
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        # Error validation
        if not error_type or not error_message:
            logger.error("Invalid error notification: type and message are required")
            return False
            
        # Error categorization
        error_categories = {
            'critical': ['system_failure', 'database_failure', 'api_failure', 'authentication_failure'],
            'high': ['trade_execution_failure', 'data_acquisition_failure', 'strategy_failure'],
            'medium': ['connection_issue', 'rate_limit', 'timeout'],
            'low': ['warning', 'info', 'debug']
        }
        
        # Determine error priority
        error_priority = 'medium'  # Default priority
        for priority, categories in error_categories.items():
            if any(category in error_type.lower() for category in categories):
                error_priority = priority
                break
                
        # Prepare notification data
        notification_data = {
            'type': error_type,
            'message': error_message,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add additional error data if provided
        if error_data:
            # Add only essential error data to avoid cluttering the message
            for key, value in error_data.items():
                if key not in notification_data:
                    notification_data[key] = value
                    
        # Track error in log with full details
        log_message = f"Error: {error_type} - {error_message}"
        if error_data:
            log_message += f" - Details: {error_data}"
            
        if error_priority == 'critical':
            logger.critical(log_message)
        elif error_priority == 'high':
            logger.error(log_message)
        elif error_priority == 'medium':
            logger.warning(log_message)
        else:
            logger.info(log_message)
            
        # Format the message
        message = self.format_message('error', notification_data)
        if not message:
            logger.error(f"Failed to format error notification")
            return False
            
        # Determine notification settings based on priority
        disable_notification = error_priority.lower() in ['low', 'medium']
        
        # Send the notification
        logger.info(f"Sending {error_priority} priority error notification")
        return await self.send_telegram_message(
            message=message,
            parse_mode="HTML",
            disable_notification=disable_notification
        )
    
    async def send_signal_notification(
        self,
        strategy_name: str,
        signal_data: Dict[str, Union[str, float, datetime]]
    ) -> bool:
        """
        Send a trading signal notification.
        
        Args:
            strategy_name (str): Name of the strategy
            signal_data (Dict[str, Union[str, float, datetime]]): Signal data
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        # Signal validation
        if not strategy_name:
            logger.error("Invalid signal notification: strategy name is required")
            return False
            
        # Required signal data fields
        required_fields = ['symbol', 'action', 'price']
        for field in required_fields:
            if field not in signal_data:
                logger.error(f"Missing required field '{field}' for signal notification")
                return False
                
        # Validate action type
        valid_actions = ['buy', 'sell', 'buy_limit', 'sell_limit', 'buy_stop', 'sell_stop', 'close']
        if 'action' in signal_data:
            action = signal_data['action']
            if isinstance(action, str) and action.lower() not in [a.lower() for a in valid_actions]:
                logger.warning(f"Unusual signal action: {action}")
            elif not isinstance(action, str):
                logger.warning(f"Invalid action type: expected string, got {type(action).__name__}")
            
        # Add strategy name to signal data
        signal_data['strategy'] = strategy_name
        
        # Check for signal aggregation
        should_aggregate = self.config.get('notification', {}).get('aggregate_signals', False)
        if should_aggregate:
            # In a real implementation, we would store signals and send them in batches
            # For now, we'll just log that aggregation would happen
            logger.info(f"Signal from {strategy_name} would be aggregated (not implemented)")
            
        # Format the message
        message = self.format_message('signal', signal_data)
        if not message:
            logger.error(f"Failed to format signal notification")
            return False
            
        # Determine notification settings
        priority = self.config.get('notification', {}).get('priority', {}).get('signal', 'normal')
        disable_notification = priority.lower() != 'high' if isinstance(priority, str) else True
        
        # Send the notification
        logger.info(f"Sending signal notification from strategy {strategy_name}")
        return await self.send_telegram_message(
            message=message,
            parse_mode="HTML",
            disable_notification=disable_notification
        )
    
    async def send_system_notification(
        self,
        notification_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a system notification.
        
        Args:
            notification_type (str): Type of system notification
            message (str): Notification message
            data (Optional[Dict[str, Any]]): Additional data
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        # Notification validation
        if not notification_type or not message:
            logger.error("Invalid system notification: type and message are required")
            return False
            
        # Notification categorization
        system_categories = {
            'high': ['startup', 'shutdown', 'restart', 'update', 'maintenance'],
            'medium': ['status', 'performance', 'resource'],
            'low': ['info', 'debug', 'log']
        }
        
        # Determine notification priority
        notification_priority = 'medium'  # Default priority
        for priority, categories in system_categories.items():
            if any(category in notification_type.lower() for category in categories):
                notification_priority = priority
                break
                
        # Prepare notification data
        notification_data = {
            'type': notification_type,
            'message': message,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add additional data if provided
        if data:
            for key, value in data.items():
                if key not in notification_data:
                    notification_data[key] = value
                    
        # Check if notification should be scheduled
        scheduled_time = data.get('scheduled_time') if data else None
        if scheduled_time and isinstance(scheduled_time, datetime) and scheduled_time > datetime.now():
            # In a real implementation, we would schedule this notification
            # For now, we'll just log that scheduling would happen
            delay = (scheduled_time - datetime.now()).total_seconds()
            logger.info(f"System notification would be scheduled for {scheduled_time} ({delay:.1f}s from now)")
            # In a real implementation, we would use asyncio.create_task with asyncio.sleep
            
        # Format the message
        message = self.format_message('system', notification_data)
        if not message:
            logger.error(f"Failed to format system notification")
            return False
            
        # Determine notification settings
        disable_notification = notification_priority.lower() != 'high'
        
        # Send the notification
        logger.info(f"Sending {notification_priority} priority system notification")
        return await self.send_telegram_message(
            message=message,
            parse_mode="HTML",
            disable_notification=disable_notification
        )
    
    def format_message(
        self,
        template_name: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Format a message using a template.
        
        Args:
            template_name (str): Name of the template to use
            data (Dict[str, Any]): Data to format the template with
            
        Returns:
            str: Formatted message
        """
        # Template validation
        if not template_name or not isinstance(template_name, str):
            logger.error(f"Invalid template name: {template_name}")
            return ""
            
        # Check if template exists
        template = self.templates.get(template_name)
        if not template:
            logger.error(f"Template not found: {template_name}")
            return ""
            
        # Check for custom template override
        custom_templates = self.config.get('notification', {}).get('custom_templates', {})
        if template_name in custom_templates:
            template = custom_templates[template_name]
            logger.debug(f"Using custom template for {template_name}")
            
        # Data validation
        if not data or not isinstance(data, dict):
            logger.error(f"Invalid data for template {template_name}: {data}")
            return ""
            
        try:
            # Format the template with the provided data
            # Add default timestamp if not provided
            if 'time' not in data and '{time}' in template:
                data['time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            # Format the message
            formatted_message = template.format(**data)
            return formatted_message
            
        except KeyError as e:
            logger.error(f"Missing required data for template {template_name}: {e}")
            return ""
            
        except ValueError as e:
            logger.error(f"Error formatting template {template_name}: {e}")
            return ""
            
        except Exception as e:
            logger.exception(f"Unexpected error formatting message with template {template_name}: {e}")
            return ""
    
    async def send_batch_notifications(
        self,
        notifications: List[Dict[str, Any]]
    ) -> Dict[int, bool]:
        """
        Send multiple notifications in batch.
        
        Args:
            notifications (List[Dict[str, Any]]): List of notifications to send
            
        Returns:
            Dict[int, bool]: Dictionary of notification indices and their success status
        """
        # Batch validation
        if not notifications or not isinstance(notifications, list):
            logger.error("Invalid batch notifications: must be a non-empty list")
            return {}
            
        # Prepare results dictionary
        results = {}
        
        # Check if batch optimization is enabled
        should_optimize = self.config.get('notification', {}).get('optimize_batch', True)
        if should_optimize:
            # Group notifications by type for optimization
            grouped_notifications = {}
            for i, notification in enumerate(notifications):
                notification_type = notification.get('type', 'unknown')
                if notification_type not in grouped_notifications:
                    grouped_notifications[notification_type] = []
                grouped_notifications[notification_type].append((i, notification))
                
            logger.info(f"Optimized batch: grouped {len(notifications)} notifications into {len(grouped_notifications)} types")
            
            # Process each group
            for notification_type, group in grouped_notifications.items():
                logger.debug(f"Processing {len(group)} notifications of type {notification_type}")
                
                # For certain types, we might want to combine them into a single notification
                # This is just a placeholder for that logic
                if notification_type in ['info', 'debug', 'log'] and len(group) > 3:
                    logger.info(f"Combining {len(group)} {notification_type} notifications")
                    # Implementation would go here
        
        # Process notifications in parallel
        # Create tasks for each notification
        tasks = []
        for i, notification in enumerate(notifications):
            # Extract notification parameters
            notification_type = notification.get('type')
            if not notification_type:
                logger.error(f"Notification at index {i} missing required 'type' field")
                results[i] = False
                continue
                
            # Create appropriate task based on notification type
            if notification_type == 'trade':
                trade_type = notification.get('trade_type')
                trade_data = notification.get('data', {})
                if not trade_type or not trade_data:
                    logger.error(f"Invalid trade notification at index {i}")
                    results[i] = False
                    continue
                task = self.send_trade_notification(trade_type, trade_data)
                
            elif notification_type == 'error':
                error_type = notification.get('error_type')
                error_message = notification.get('message')
                error_data = notification.get('data')
                if not error_type or not error_message:
                    logger.error(f"Invalid error notification at index {i}")
                    results[i] = False
                    continue
                task = self.send_error_notification(error_type, error_message, error_data)
                
            elif notification_type == 'signal':
                strategy_name = notification.get('strategy')
                signal_data = notification.get('data', {})
                if not strategy_name or not signal_data:
                    logger.error(f"Invalid signal notification at index {i}")
                    results[i] = False
                    continue
                task = self.send_signal_notification(strategy_name, signal_data)
                
            elif notification_type == 'system':
                system_type = notification.get('system_type')
                message = notification.get('message')
                data = notification.get('data')
                if not system_type or not message:
                    logger.error(f"Invalid system notification at index {i}")
                    results[i] = False
                    continue
                task = self.send_system_notification(system_type, message, data)
                
            else:
                logger.error(f"Unknown notification type at index {i}: {notification_type}")
                results[i] = False
                continue
                
            # Add task to list with its index
            tasks.append((i, task))
            
        # Execute tasks in parallel with monitoring
        if tasks:
            logger.info(f"Executing {len(tasks)} notification tasks in parallel")
            
            # Process tasks in batches to avoid overwhelming the system
            batch_size = self.config.get('notification', {}).get('parallel_batch_size', 5)
            for batch_start in range(0, len(tasks), batch_size):
                batch_end = min(batch_start + batch_size, len(tasks))
                batch = tasks[batch_start:batch_end]
                
                logger.debug(f"Processing batch {batch_start//batch_size + 1}: {batch_start} to {batch_end-1}")
                
                # Create and gather tasks
                batch_tasks = [task for _, task in batch]
                batch_indices = [idx for idx, _ in batch]
                
                # Execute batch
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(batch_results):
                    idx = batch_indices[i]
                    if isinstance(result, Exception):
                        logger.error(f"Exception in notification {idx}: {str(result)}")
                        results[idx] = False
                    else:
                        results[idx] = bool(result)
                        
        # Return results
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"Batch notification complete: {success_count}/{len(notifications)} successful")
        return results
        
    async def notify_event(
        self,
        event_type: str,
        event_name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        category: str = "system"
    ) -> bool:
        """
        Universal method to send notifications for any application event.
        
        This method serves as a central point for all application notifications,
        making it easy to implement consistent notification behavior across the application.
        
        Args:
            event_type (str): Type of event (e.g., 'trade', 'system', 'error', 'signal')
            event_name (str): Specific name of the event (e.g., 'order_placed', 'startup', 'api_error')
            message (str): Human-readable message describing the event
            data (Optional[Dict[str, Any]]): Additional data related to the event
            priority (str): Priority level ('high', 'normal', 'low')
            category (str): Category for grouping similar events
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        logger.info(f"Event notification: {event_type}.{event_name} - {message}")
        
        # Default data if none provided
        if data is None:
            data = {}
            
        # Add metadata to the event data
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'priority': priority,
            **data
        }
        
        # Route to appropriate notification method based on event type
        if event_type.lower() == 'trade':
            # For trade events
            trade_data = {
                'symbol': data.get('symbol', 'UNKNOWN'),
                'type': data.get('type', 'UNKNOWN'),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data
            }
            
            if event_name.lower() in ['opened', 'open', 'new', 'created']:
                return await self.send_trade_notification('trade_opened', trade_data)
            elif event_name.lower() in ['closed', 'close', 'completed']:
                return await self.send_trade_notification('trade_closed', trade_data)
            else:
                # Generic trade notification
                return await self.send_system_notification(
                    f"trade_{event_name}",
                    message,
                    event_data
                )
                
        elif event_type.lower() == 'error':
            # For error events
            return await self.send_error_notification(
                error_type=event_name,
                error_message=message,
                error_data=event_data
            )
            
        elif event_type.lower() == 'signal':
            # For trading signal events
            signal_data = {
                'symbol': data.get('symbol', 'UNKNOWN'),
                'action': data.get('action', 'UNKNOWN'),
                'price': data.get('price', 0.0),
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data
            }
            
            return await self.send_signal_notification(
                strategy_name=data.get('strategy', 'UNKNOWN'),
                signal_data=signal_data
            )
            
        else:
            # For all other event types (system, info, etc.)
            return await self.send_system_notification(
                notification_type=f"{event_type}_{event_name}",
                message=message,
                data=event_data
            )
            
    @classmethod
    def get_instance(cls):
        """
        Get or create a singleton instance of NotificationManager.
        
        This method ensures that only one instance of NotificationManager
        is created throughout the application.
        
        Returns:
            NotificationManager: Singleton instance of NotificationManager
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance 