"""
Configuration manager for MetaApi application.
Handles loading and validation of configuration from various sources.
"""

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from core.exceptions import ConfigurationError

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


@dataclass
class FeatureFlags:
    """Feature flags for enhanced functionality."""
    rate_limiting: bool = True
    request_logging: bool = True
    metrics_collection: bool = True
    input_validation: bool = True
    middleware: bool = True


@dataclass
class AppConfig:
    """Application configuration data class."""
    secret_key: str
    telegram_bot_token: str
    telegram_chat_id: int
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8087
    mt5_path: str = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
    rate_limit_per_minute: int = 300
    request_timeout: int = 30
    log_level: str = "INFO"
    features: FeatureFlags = None
    
    def __post_init__(self):
        if self.features is None:
            self.features = FeatureFlags()


class ConfigManager:
    """Manages application configuration from multiple sources."""
    
    def __init__(self, config_file: str = "config.json", env_file: str = ".env"):
        self.config_file = config_file
        self.env_file = env_file
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """Load configuration from file and environment variables."""
        if self._config is not None:
            return self._config
        
        # Load .env file if available
        self._load_dotenv()
        
        # Load from JSON file
        config_data = self._load_from_file()
        
        # Override with environment variables
        config_data = self._load_from_env(config_data)
        
        # Validate and create config object
        self._config = self._validate_and_create_config(config_data)
        
        return self._config
    
    def _load_dotenv(self):
        """Load environment variables from .env file if available."""
        if DOTENV_AVAILABLE and os.path.exists(self.env_file):
            load_dotenv(self.env_file)
            print(f"Loaded environment variables from {self.env_file}")
        elif os.path.exists(self.env_file):
            print(f"Found {self.env_file} but python-dotenv not installed. Install with: pip install python-dotenv")
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file '{self.config_file}' not found")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
    
    def _load_from_env(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables."""
        env_mappings = {
            'SECRET_KEY': 'secret_key',
            'TELEGRAM_BOT_TOKEN': 'telegram_bot_token',
            'TELEGRAM_CHAT_ID': 'telegram_chat_id',
            'DEBUG': 'debug',
            'HOST': 'host',
            'PORT': 'port',
            'MT5_PATH': 'mt5_path',
            'RATE_LIMIT_PER_MINUTE': 'rate_limit_per_minute',
            'REQUEST_TIMEOUT': 'request_timeout',
            'LOG_LEVEL': 'log_level',
            'RATE_LIMITING': 'features.rate_limiting',
            'REQUEST_LOGGING': 'features.request_logging',
            'METRICS_COLLECTION': 'features.metrics_collection',
            'INPUT_VALIDATION': 'features.input_validation',
            'MIDDLEWARE': 'features.middleware'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Handle nested feature flags
                if config_key.startswith('features.'):
                    if 'features' not in config_data:
                        config_data['features'] = {}
                    feature_key = config_key.split('.')[1]
                    config_data['features'][feature_key] = env_value.lower() in ('true', '1', 'yes')
                # Convert types for other fields
                elif config_key in ['telegram_chat_id', 'port', 'rate_limit_per_minute', 'request_timeout']:
                    try:
                        config_data[config_key] = int(env_value)
                    except ValueError:
                        raise ConfigurationError(f"Invalid integer value for {env_var}: {env_value}")
                elif config_key == 'debug':
                    config_data[config_key] = env_value.lower() in ('true', '1', 'yes')
                else:
                    config_data[config_key] = env_value
        
        return config_data
    
    def _validate_and_create_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """Validate configuration data and create AppConfig object."""
        required_fields = ['secret_key', 'telegram_bot_token', 'telegram_chat_id']
        
        for field in required_fields:
            if not config_data.get(field):
                raise ConfigurationError(f"Required configuration field '{field}' is missing or empty")
        
        try:
            # Handle feature flags
            features_data = config_data.get('features', {})
            features = FeatureFlags(
                rate_limiting=features_data.get('rate_limiting', True),
                request_logging=features_data.get('request_logging', True),
                metrics_collection=features_data.get('metrics_collection', True),
                input_validation=features_data.get('input_validation', True),
                middleware=features_data.get('middleware', True)
            )
            
            return AppConfig(
                secret_key=config_data['secret_key'],
                telegram_bot_token=config_data['telegram_bot_token'],
                telegram_chat_id=int(config_data['telegram_chat_id']),
                debug=config_data.get('debug', False),
                host=config_data.get('host', '0.0.0.0'),
                port=config_data.get('port', 8087),
                mt5_path=config_data.get('mt5_path', 'C:\\Program Files\\MetaTrader 5\\terminal64.exe'),
                rate_limit_per_minute=config_data.get('rate_limit_per_minute', 300),
                request_timeout=config_data.get('request_timeout', 30),
                log_level=config_data.get('log_level', 'INFO'),
                features=features
            )
        except (ValueError, TypeError) as e:
            raise ConfigurationError(f"Invalid configuration values: {e}")
    
    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config


# Global configuration instance
config_manager = ConfigManager()
