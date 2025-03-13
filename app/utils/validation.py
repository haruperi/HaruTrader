import re
import datetime
from typing import Any, Dict, List, Optional, Union, Callable

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class Validator:
    """
    Utility class for validating input data.
    Provides methods for common validation tasks.
    """
    
    @staticmethod
    def validate_required(data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that all required fields are present in the data.
        
        Args:
            data (Dict[str, Any]): Data to validate
            required_fields (List[str]): List of required field names
            
        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    @staticmethod
    def validate_type(value: Any, expected_type: type, field_name: str = "value") -> None:
        """
        Validate that a value is of the expected type.
        
        Args:
            value (Any): Value to validate
            expected_type (type): Expected type
            field_name (str): Name of the field for error messages
            
        Raises:
            ValidationError: If value is not of the expected type
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid type for {field_name}. Expected {expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float], 
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        field_name: str = "value"
    ) -> None:
        """
        Validate that a numeric value is within the specified range.
        
        Args:
            value (Union[int, float]): Value to validate
            min_value (Optional[Union[int, float]]): Minimum allowed value
            max_value (Optional[Union[int, float]]): Maximum allowed value
            field_name (str): Name of the field for error messages
            
        Raises:
            ValidationError: If value is outside the specified range
        """
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field_name} must be a number")
            
        if min_value is not None and value < min_value:
            raise ValidationError(f"{field_name} must be at least {min_value}")
            
        if max_value is not None and value > max_value:
            raise ValidationError(f"{field_name} must be at most {max_value}")
    
    @staticmethod
    def validate_string_pattern(
        value: str, 
        pattern: str,
        field_name: str = "value"
    ) -> None:
        """
        Validate that a string matches the specified regex pattern.
        
        Args:
            value (str): String to validate
            pattern (str): Regex pattern
            field_name (str): Name of the field for error messages
            
        Raises:
            ValidationError: If string doesn't match the pattern
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
            
        if not re.match(pattern, value):
            raise ValidationError(f"{field_name} does not match the required pattern")
    
    @staticmethod
    def validate_date_format(
        value: str,
        format_str: str = "%Y-%m-%d",
        field_name: str = "date"
    ) -> None:
        """
        Validate that a string can be parsed as a date with the specified format.
        
        Args:
            value (str): String to validate
            format_str (str): Date format string
            field_name (str): Name of the field for error messages
            
        Raises:
            ValidationError: If string cannot be parsed as a date
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
            
        try:
            datetime.datetime.strptime(value, format_str)
        except ValueError:
            raise ValidationError(
                f"{field_name} must be in the format {format_str}"
            )
    
    @staticmethod
    def validate_email(email: str) -> None:
        """
        Validate that a string is a valid email address.
        
        Args:
            email (str): Email address to validate
            
        Raises:
            ValidationError: If email is invalid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        Validator.validate_string_pattern(email, pattern, "Email")
    
    @staticmethod
    def validate_custom(
        value: Any,
        validation_func: Callable[[Any], bool],
        error_message: str,
        field_name: str = "value"
    ) -> None:
        """
        Validate a value using a custom validation function.
        
        Args:
            value (Any): Value to validate
            validation_func (Callable[[Any], bool]): Function that returns True if valid
            error_message (str): Error message if validation fails
            field_name (str): Name of the field for error messages
            
        Raises:
            ValidationError: If validation function returns False
        """
        if not validation_func(value):
            raise ValidationError(f"{field_name}: {error_message}")


# Create a singleton instance
validator = Validator() 