# bot/exchange_manager.py
import asyncio
import logging
import ccxt.async_support as ccxt
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
import json
import time

# Updated imports to use absolute paths instead of relative imports
from core import config


class ExchangeCredentialManager:
    """Manages secure exchange credentials with validation and testing"""
    
    def __init__(self):
        self.logger = logging.getLogger('ExchangeCredentialManager')
        self.supported_exchanges = getattr(config, 'supported_exchanges', ['bitget'])
        
        # Exchange-specific configuration - only include supported exchanges
        self.exchange_configs = {
            'bitget': {
                'class': 'bitget',
                'required_fields': ['api_key', 'secret', 'passphrase'],
                'optional_fields': ['sandbox'],
                'testnet_available': True,
                'default_type': 'spot'
            }
        }
    
    async def validate_credentials(self, exchange_name: str, credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Validate exchange credentials by testing connection"""
        try:
            if exchange_name not in self.supported_exchanges:
                return False, f"Unsupported exchange: {exchange_name}"
            
            exchange_config = self.exchange_configs.get(exchange_name)
            if not exchange_config:
                return False, f"No configuration found for {exchange_name}"
            
            # Check required fields
            required_fields = exchange_config['required_fields']
            missing_fields = [field for field in required_fields if not credentials.get(field)]
            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"
            
            # Create exchange instance
            exchange_class = getattr(ccxt, exchange_config['class'])
            exchange_params = {
                'apiKey': credentials.get('api_key'),
                'secret': credentials.get('secret'),
                'enableRateLimit': True,
                'options': {'defaultType': exchange_config['default_type']}
            }
            
            # Add passphrase if required
            if 'passphrase' in required_fields:
                exchange_params['passphrase'] = credentials.get('passphrase')
            
            # Enable sandbox if specified
            if credentials.get('sandbox', False):
                exchange_params['sandbox'] = True
            
            exchange = exchange_class(exchange_params)
            
            # Test basic connectivity with retry logic
            await self._test_exchange_connection(exchange, exchange_name)
            
            return True, "Credentials validated successfully"
            
        except Exception as e:
            self.logger.error(f"Credential validation failed for {exchange_name}: {str(e)}")
            return False, f"Validation failed: {str(e)}"
    
    async def _test_exchange_connection(self, exchange, exchange_name: str):
        """Test exchange connection and basic functionality with retry logic"""
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Test 1: Fetch markets with retry logic
                markets = None
                market_retry_count = 0
                max_market_retries = 3
                
                while market_retry_count < max_market_retries:
                    try:
                        markets = await exchange.load_markets()
                        if markets:
                            break
                        else:
                            raise Exception("No markets available")
                    except Exception as e:
                        market_retry_count += 1
                        if market_retry_count < max_market_retries and self._is_retryable_error(e):
                            self.logger.warning(f"Market fetch failed (attempt {market_retry_count}): {str(e)}. Retrying in {retry_delay} seconds...")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            raise
                
                if not markets:
                    raise Exception("No markets available")
                
                # Test 2: Fetch ticker for a common pair with retry logic
                test_symbols = ['BTC/USDT', 'BTC/USD', 'ETH/USDT', 'ETH/USD']
                ticker_found = False
                
                for symbol in test_symbols:
                    if symbol in markets:
                        ticker_retry_count = 0
                        max_ticker_retries = 3
                        
                        while ticker_retry_count < max_ticker_retries:
                            try:
                                ticker = await exchange.fetch_ticker(symbol)
                                if ticker and 'last' in ticker:
                                    ticker_found = True
                                    break
                            except Exception as e:
                                ticker_retry_count += 1
                                if ticker_retry_count < max_ticker_retries and self._is_retryable_error(e):
                                    self.logger.warning(f"Ticker fetch failed for {symbol} (attempt {ticker_retry_count}): {str(e)}. Retrying in {retry_delay} seconds...")
                                    await asyncio.sleep(retry_delay)
                                    retry_delay *= 2  # Exponential backoff
                                else:
                                    # Continue to next symbol if this one fails
                                    break
                        if ticker_found:
                            break
                
                if not ticker_found:
                    raise Exception("Unable to fetch ticker data")
                
                # Test 3: Check account access (if possible)
                try:
                    balance = await exchange.fetch_balance()
                    self.logger.info(f"Account access confirmed for {exchange_name}")
                except Exception as e:
                    # Some APIs might not allow balance access without specific permissions
                    self.logger.warning(f"Account access test failed for {exchange_name}: {e}")
                
                self.logger.info(f"Exchange connection test passed for {exchange_name}")
                return  # Success, exit the retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:  # Not the last attempt
                    if self._is_retryable_error(e):
                        self.logger.warning(f"Exchange connection test failed for {exchange_name} (attempt {attempt + 1}): {str(e)}. Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        self.logger.error(f"Non-retryable error in exchange connection test for {exchange_name}: {str(e)}")
                        raise
                else:
                    # Last attempt, re-raise the exception
                    raise Exception(f"Connection test failed after {max_retries} attempts: {str(e)}")
            finally:
                # Always close the exchange
                if hasattr(exchange, 'close'):
                    await exchange.close()
    
    def _is_retryable_error(self, error) -> bool:
        """Determine if an error is retryable"""
        # Check if it's a CCXT error
        if hasattr(error, '__class__'):
            error_class_name = error.__class__.__name__
            retryable_errors = [
                'RateLimitExceeded',
                'RequestTimeout',
                'NetworkError',
                'DDoSProtection',
                'ExchangeNotAvailable'
            ]
            return any(retryable_error in error_class_name for retryable_error in retryable_errors)
        
        # Check if it's a string error message
        error_str = str(error).lower()
        retryable_messages = [
            'too many requests',
            'connection timeout',
            'network error',
            'service unavailable',
            'rate limit'
        ]
        return any(retryable_message in error_str for retryable_message in retryable_messages)
    
    async def store_credentials(self, user_id: int, exchange_name: str, credentials: Dict[str, str]) -> bool:
        """Store encrypted exchange credentials for a user"""
        try:
            # Validate credentials first
            is_valid, validation_message = await self.validate_credentials(exchange_name, credentials)
            if not is_valid:
                self.logger.error(f"Cannot store invalid credentials for user {user_id}, {exchange_name}: {validation_message}")
                return False
            
            # For a personal bot, we don't need to store credentials in a database
            # Instead, we can just return True to indicate validation was successful
            self.logger.info(f"Credentials validated for {exchange_name} (not stored in database for personal bot)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing credentials for user {user_id}, {exchange_name}: {str(e)}")
            return False
    
    async def get_user_credentials(self, user_id: int, exchange_name: str) -> Optional[Dict[str, str]]:
        """Retrieve user exchange credentials - for personal bot, this would come from config"""
        # For a personal bot, credentials would be loaded from environment variables or config
        # This method is kept for interface compatibility but would not be used in personal bot
        self.logger.warning("get_user_credentials called but not implemented for personal bot")
        return None
    
    async def delete_user_credentials(self, user_id: int, exchange_name: str) -> bool:
        """Delete user exchange credentials - for personal bot, this is a no-op"""
        # For a personal bot, we don't store credentials in a database to delete
        self.logger.info(f"delete_user_credentials called for personal bot (no-op)")
        return True
    
    def get_exchange_requirements(self, exchange_name: str) -> Dict[str, Any]:
        """Get requirements and information for an exchange"""
        if exchange_name not in self.supported_exchanges:
            return {}
        
        config = self.exchange_configs.get(exchange_name, {})
        
        return {
            'exchange_name': exchange_name,
            'required_fields': config.get('required_fields', []),
            'optional_fields': config.get('optional_fields', []),
            'testnet_available': config.get('testnet_available', False),
            'description': self._get_exchange_description(exchange_name),
            'setup_instructions': self._get_setup_instructions(exchange_name)
        }
    
    def _get_exchange_description(self, exchange_name: str) -> str:
        """Get description for an exchange"""
        descriptions = {
            'bitget': 'Bitget - Leading cryptocurrency derivatives exchange'
        }
        return descriptions.get(exchange_name, f'{exchange_name} - Cryptocurrency exchange')
    
    def _get_setup_instructions(self, exchange_name: str) -> List[str]:
        """Get setup instructions for an exchange"""
        instructions = {
            'bitget': [
                '1. Log in to your Bitget account',
                '2. Go to API Management',
                '3. Click "Create API Key"',
                '4. Enable required permissions',
                '5. Enter your API key, secret, and passphrase'
            ]
        }
        return instructions.get(exchange_name, [f'Please refer to {exchange_name} documentation for API key setup'])
    
    def get_all_supported_exchanges(self) -> List[Dict[str, Any]]:
        """Get information for all supported exchanges"""
        exchanges_info = []
        
        for exchange_name in self.supported_exchanges:
            exchange_info = self.get_exchange_requirements(exchange_name)
            exchanges_info.append(exchange_info)
        
        return exchanges_info


class SimpleExchangeManager:
    """Simplified exchange manager for personal trading bots"""
    
    def __init__(self, exchange_credentials: Dict[str, Dict[str, str]]):
        self.logger = logging.getLogger('SimpleExchangeManager')
        self.exchanges = {}
        self.exchange_health = {}
        self.credentials = exchange_credentials
    
    async def initialize_exchanges(self) -> Dict[str, bool]:
        """Initialize all configured exchanges for personal use"""
        results = {}
        
        # Initialize each exchange from provided credentials
        for exchange_name, creds in self.credentials.items():
            try:
                # Only support Bitget for personal bot
                if exchange_name != 'bitget':
                    results[exchange_name] = False
                    self.logger.warning(f"Unsupported exchange {exchange_name} for personal bot")
                    continue
                
                # Create exchange instance
                exchange_class = getattr(ccxt, 'bitget')
                exchange_params = {
                    'apiKey': creds.get('api_key'),
                    'secret': creds.get('secret'),
                    'password': creds.get('passphrase'),  # Bitget requires password
                    'enableRateLimit': True,
                    'options': {'defaultType': 'spot'}
                }
                
                # Enable sandbox if specified
                if creds.get('sandbox', False):
                    exchange_params['sandbox'] = True
                
                exchange = exchange_class(exchange_params)
                
                # Test connectivity
                await exchange.load_markets()
                
                # Store active exchange
                self.exchanges[exchange_name] = exchange
                self.exchange_health[exchange_name] = {
                    'status': 'healthy',
                    'last_check': datetime.now(),
                    'success_count': 0,
                    'failure_count': 0
                }
                
                results[exchange_name] = True
                self.logger.info(f"Exchange {exchange_name} initialized successfully")
                
            except Exception as e:
                results[exchange_name] = False
                self.logger.error(f"Failed to initialize exchange {exchange_name}: {str(e)}")
                # Store health info even for failed exchanges
                self.exchange_health[exchange_name] = {
                    'status': 'unhealthy',
                    'last_check': datetime.now(),
                    'success_count': 0,
                    'failure_count': 1,
                    'last_error': str(e)
                }
        
        return results
    
    async def get_exchange_for_symbol(self, symbol: str) -> Optional[Tuple[str, Any]]:
        """Get the exchange for trading a specific symbol"""
        if not self.exchanges:
            await self.initialize_exchanges()
        
        # For personal bot, we only have Bitget
        if 'bitget' in self.exchanges:
            exchange = self.exchanges['bitget']
            try:
                # Check if symbol is available
                markets = await exchange.load_markets()
                if symbol in markets:
                    return ('bitget', exchange)
            except Exception as e:
                self.logger.error(f"Error checking symbol {symbol} on Bitget: {str(e)}")
        
        return None
    
    async def execute_trade(self, symbol: str, side: str, amount: float, price: Optional[float] = None) -> Dict[str, Any]:
        """Execute a trade on Bitget exchange"""
        exchange_name = 'bitget'
        try:
            # Get exchange for this symbol
            exchange_info = await self.get_exchange_for_symbol(symbol)
            if not exchange_info:
                return {
                    'success': False,
                    'error': 'Bitget exchange not available for this symbol'
                }
            
            exchange_name, exchange = exchange_info
            
            # Execute the trade
            if price:
                # Limit order
                order = await exchange.create_limit_order(symbol, side, amount, price)
            else:
                # Market order
                order = await exchange.create_market_order(symbol, side, amount)
            
            # Update health status
            if exchange_name in self.exchange_health:
                health = self.exchange_health[exchange_name]
                health['success_count'] = health.get('success_count', 0) + 1
                health['last_check'] = datetime.now()
                if health['failure_count'] > 0:
                    health['failure_count'] = max(0, health['failure_count'] - 1)  # Reduce failure count on success
            
            return {
                'success': True,
                'exchange': exchange_name,
                'order': order
            }
            
        except Exception as e:
            # Update health status
            if exchange_name in self.exchange_health:
                health = self.exchange_health[exchange_name]
                health['failure_count'] = health.get('failure_count', 0) + 1
                health['last_error'] = str(e)
                health['last_check'] = datetime.now()
                if health['failure_count'] > 5:
                    health['status'] = 'unhealthy'
            
            self.logger.error(f"Failed to execute trade on {exchange_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def close_all_exchanges(self):
        """Close all active exchange connections"""
        for exchange_name, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, 'close'):
                    await exchange.close()
                self.logger.info(f"Closed connection to {exchange_name}")
            except Exception as e:
                self.logger.error(f"Error closing connection to {exchange_name}: {str(e)}")
        
        self.exchanges.clear()
        self.logger.info("All exchange connections closed")
    
    def get_exchange_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all exchanges"""
        return self.exchange_health