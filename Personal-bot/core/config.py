# bot/config.py
import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json

@dataclass
class BotConfig:
    """Main configuration for the crypto trading bot"""

    # Trading parameters
    supported_pairs: Optional[List[str]] = None
    base_currency: str = "USDT"
    min_investment: float = 1.0
    max_daily_trades: float = 1000000.0
    cooldown_minutes: int = 1
    refresh_interval_seconds: int = 60

    # Timeframes for analysis
    trading_timeframe: str = "5m"  # Changed from 3m to 5m for Bitget compatibility
    analysis_timeframes: Optional[List[str]] = None

    # Risk management
    max_loss_percent: float = 0.0  # User configurable, 0 = no limit
    daily_profit_target_percent: float = float('inf')  # User configurable

    # ML/AI settings
    ml_model_path: str = "models/enhanced_trading_model.pkl"
    use_ml_prediction: bool = True

    # Exchange settings - Bitget only
    supported_exchanges: Optional[List[str]] = None

    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: Optional[str] = None

    # Notification settings
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None

    # Caching/Rate limit settings
    redis_url: Optional[str] = None

    # Sandbox mode for demo trading
    sandbox_mode: bool = False

    def __post_init__(self):
        if self.supported_pairs is None:
            self.supported_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "DOGE/USDT", "ADA/USDT", "XRP/USDT"]

        if self.analysis_timeframes is None:
            self.analysis_timeframes = ["15m", "30m", "1h"]

        # Updated to only support Bitget
        if self.supported_exchanges is None:
            self.supported_exchanges = ["bitget"]

        if self.secret_key is None:
            self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")

        if self.telegram_bot_token is None:
            self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")  # type: ignore

        if self.telegram_chat_id is None:
            self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")  # type: ignore

        if self.email_smtp_server is None:
            self.email_smtp_server = os.getenv("EMAIL_SMTP_SERVER")  # type: ignore

        if self.email_smtp_port is None:
            self.email_smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))

        if self.email_username is None:
            self.email_username = os.getenv("EMAIL_USERNAME")  # type: ignore

        if self.email_password is None:
            self.email_password = os.getenv("EMAIL_PASSWORD")  # type: ignore

        if self.redis_url is None:
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.sandbox_mode = os.getenv("SANDBOX_MODE", "false").lower() == "true"

        # Load from environment or config file
        self._load_from_env()

    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'API_HOST': 'api_host',
            'API_PORT': 'api_port',
            'SECRET_KEY': 'secret_key',
            'TELEGRAM_BOT_TOKEN': 'telegram_bot_token',
            'TELEGRAM_CHAT_ID': 'telegram_chat_id',
            'EMAIL_SMTP_SERVER': 'email_smtp_server',
            'EMAIL_SMTP_PORT': 'email_smtp_port',
            'EMAIL_USERNAME': 'email_username',
            'EMAIL_PASSWORD': 'email_password',
            'MAX_DAILY_TRADES': 'max_daily_trades',
            'MIN_INVESTMENT': 'min_investment',
            'MAX_LOSS_PERCENT': 'max_loss_percent',
            'DAILY_PROFIT_TARGET_PERCENT': 'daily_profit_target_percent',
            'SUPPORTED_PAIRS': 'supported_pairs',
            'ML_MODEL_PATH': 'ml_model_path'
        }

        for env_var, attr in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if attr in ['api_port', 'email_smtp_port']:
                        setattr(self, attr, int(value))
                    elif attr in ['max_daily_trades', 'min_investment', 'max_loss_percent', 'daily_profit_target_percent']:
                        setattr(self, attr, float(value))
                    elif attr == 'supported_pairs':
                        setattr(self, attr, [p.strip() for p in value.split(',')])
                    else:
                        setattr(self, attr, value)
                except (ValueError, TypeError):
                    # Skip invalid values, keep defaults
                    pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for JSON serialization"""
        return {
            'supported_pairs': self.supported_pairs,
            'base_currency': self.base_currency,
            'min_investment': self.min_investment,
            'max_daily_trades': self.max_daily_trades,
            'cooldown_minutes': self.cooldown_minutes,
            'refresh_interval_seconds': self.refresh_interval_seconds,
            'trading_timeframe': self.trading_timeframe,
            'analysis_timeframes': self.analysis_timeframes,
            'max_loss_percent': self.max_loss_percent,
            'daily_profit_target_percent': self.daily_profit_target_percent,
            'ml_model_path': self.ml_model_path,
            'use_ml_prediction': self.use_ml_prediction,
            'supported_exchanges': self.supported_exchanges,
            'api_host': self.api_host,
            'api_port': self.api_port,
            'redis_url': self.redis_url
        }

    def save_to_file(self, filepath: str = "config.json"):
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def get_exchange_credentials(self) -> Dict[str, Dict[str, str]]:
        """Get exchange API credentials from environment variables - Bitget only"""
        credentials = {}
        # Only support Bitget
        bitget_keys = ('BITGET_API_KEY', 'BITGET_SECRET', 'BITGET_PASSPHRASE')
        api_key = os.getenv(bitget_keys[0])
        secret = os.getenv(bitget_keys[1])
        passphrase = os.getenv(bitget_keys[2])
        
        if api_key and secret and passphrase:
            credentials['bitget'] = {
                'api_key': api_key,
                'secret': secret,
                'passphrase': passphrase
            }

        return credentials

    @classmethod
    def load_from_file(cls, filepath: str = "config.json") -> 'BotConfig':
        """Load configuration from JSON file"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                config = cls()
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                return config
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Return default config if file is malformed
                print(f"Warning: Could not load config from {filepath}: {e}")
                return cls()
        return cls()
config = BotConfig()