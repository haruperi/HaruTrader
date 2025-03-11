import os
import json
import yaml
import configparser
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv

from algotrader.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigUtils:
    """
    Utility class for handling configuration files and environment variables.
    Supports loading from .env, JSON, YAML, and INI files.
    """
    
    @staticmethod
    def load_env_file(env_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
        """
        Load environment variables from .env file.
        
        Args:
            env_path (Optional[Union[str, Path]]): Path to .env file
            
        Returns:
            Dict[str, str]: Dictionary of environment variables
        """
        # Load environment variables from .env file
        if env_path:
            load_dotenv(env_path)
        else:
            # Try to load from default locations
            for path in ['.env', '../.env', '../../.env']:
                if os.path.exists(path):
                    load_dotenv(path)
                    break
        
        # Return a dictionary of all environment variables
        return dict(os.environ)
    
    @staticmethod
    def get_env_var(
        var_name: str,
        default: Optional[Any] = None,
        required: bool = False,
        var_type: Optional[type] = None
    ) -> Any:
        """
        Get environment variable with type conversion.
        
        Args:
            var_name (str): Environment variable name
            default (Optional[Any]): Default value if not found
            required (bool): Whether the variable is required
            var_type (Optional[type]): Type to convert the value to
            
        Returns:
            Any: Environment variable value
            
        Raises:
            ValueError: If required variable is not found
        """
        value = os.environ.get(var_name)
        
        if value is None:
            if required:
                raise ValueError(f"Required environment variable {var_name} not found")
            return default
            
        # Convert to specified type
        if var_type is not None:
            try:
                if var_type == bool:
                    # Handle boolean conversion
                    return value.lower() in ('true', 'yes', '1', 'y')
                elif var_type == list:
                    # Handle list conversion (comma-separated)
                    return [item.strip() for item in value.split(',')]
                elif var_type == dict:
                    # Handle dict conversion (JSON string)
                    return json.loads(value)
                else:
                    # Handle other types
                    return var_type(value)
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.warning(
                    f"Failed to convert {var_name} to {var_type.__name__}: {e}"
                )
                return default
                
        return value
    
    @staticmethod
    def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from JSON file.
        
        Args:
            file_path (Union[str, Path]): Path to JSON file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
            
        Raises:
            FileNotFoundError: If file not found
            json.JSONDecodeError: If JSON parsing fails
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON config: {e}")
            raise
    
    @staticmethod
    def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            file_path (Union[str, Path]): Path to YAML file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
            
        Raises:
            FileNotFoundError: If file not found
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config: {e}")
            raise
    
    @staticmethod
    def load_ini_config(file_path: Union[str, Path]) -> Dict[str, Dict[str, str]]:
        """
        Load configuration from INI file.
        
        Args:
            file_path (Union[str, Path]): Path to INI file
            
        Returns:
            Dict[str, Dict[str, str]]: Configuration dictionary
            
        Raises:
            FileNotFoundError: If file not found
            configparser.Error: If INI parsing fails
        """
        try:
            config = configparser.ConfigParser()
            config.read(file_path)
            
            # Convert to dictionary
            return {
                section: dict(config[section]) for section in config.sections()
            }
        except FileNotFoundError:
            logger.error(f"Config file not found: {file_path}")
            raise
        except configparser.Error as e:
            logger.error(f"Failed to parse INI config: {e}")
            raise
    
    @staticmethod
    def save_json_config(
        config: Dict[str, Any],
        file_path: Union[str, Path],
        indent: int = 4
    ) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            file_path (Union[str, Path]): Path to JSON file
            indent (int): JSON indentation
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=indent)
        except IOError as e:
            logger.error(f"Failed to write JSON config: {e}")
            raise
    
    @staticmethod
    def save_yaml_config(
        config: Dict[str, Any],
        file_path: Union[str, Path]
    ) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
            file_path (Union[str, Path]): Path to YAML file
            
        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(file_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        except IOError as e:
            logger.error(f"Failed to write YAML config: {e}")
            raise
    
    @staticmethod
    def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries.
        Later configs override earlier ones.
        
        Args:
            *configs: Configuration dictionaries
            
        Returns:
            Dict[str, Any]: Merged configuration dictionary
        """
        result = {}
        for config in configs:
            ConfigUtils._deep_update(result, config)
        return result
    
    @staticmethod
    def _deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep update target dict with source.
        For nested dictionaries, update recursively rather than replacing.
        
        Args:
            target (Dict[str, Any]): Target dictionary to update
            source (Dict[str, Any]): Source dictionary with updates
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                ConfigUtils._deep_update(target[key], value)
            else:
                target[key] = value


# Create a singleton instance
config_utils = ConfigUtils() 