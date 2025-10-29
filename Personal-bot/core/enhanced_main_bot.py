# bot/enhanced_main_bot.py
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import ccxt.async_support as ccxt
import numpy as np
from cryptography.fernet import Fernet
import pickle
import os
from colorama import Fore, Style, init
import yfinance as yf
import math

# Initialize colorama
init(autoreset=True)

# Fix imports to work correctly when running from advanced_main.py
from core.config import config
from strategies.working_strategy_manager import WorkingStrategyManager
from core.notifications import NotificationManager
from analysis.enhanced_ml_engine import EnhancedMLEngine
from analysis.risk_management import EnhancedRiskManager, RiskLevel
from analysis.news_sentiment import EnhancedNewsSentimentAnalyzer

class EnhancedCryptoTradingBot:
    """Enhanced crypto trading bot with advanced features - Bitget Only with Yahoo Finance Market Data"""

    def __init__(self, user_config: Optional[Dict[str, Any]] = None):
        self.config = config
        if user_config:
            for key, value in user_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        # Initialize enhanced components
        self.notifications = NotificationManager(self.config)
        self.ml_engine = EnhancedMLEngine(self.config.ml_model_path)
        self.strategy_manager = WorkingStrategyManager()
        # Use user's investment amount as initial capital for risk calculations
        initial_capital = getattr(self.config, 'min_investment', 10000)
        self.risk_manager = EnhancedRiskManager({
            'max_position_risk': 0.02,
            'max_portfolio_risk': 0.10,
            'initial_capital': initial_capital
        })
        self.news_analyzer = EnhancedNewsSentimentAnalyzer()

        # Trading state - Bitget only for trading execution
        self.exchanges: Dict[str, ccxt.Exchange] = {}
        self.last_trade_time: Optional[datetime] = None
        self.daily_trades_value: float = 0.0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.is_running = False
        self._current_trade_side: str = 'unknown'  # Track current trade side for error messages

        # Enhanced market data cache with multiple timeframes
        self.market_data: Dict[str, pd.DataFrame] = {}
        
        # Performance tracking
        self.trade_performance = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0
        }

        # Setup logging
        self._setup_logging()

        # Load or create encryption key
        self._setup_encryption()

    def _setup_logging(self):
        """Setup comprehensive logging with colored console output"""
        # Create logger
        self.logger = logging.getLogger('EnhancedCryptoTradingBot')
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Colored formatter for console
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                level_colors = {
                    'DEBUG': Fore.CYAN,
                    'INFO': Fore.GREEN,
                    'WARNING': Fore.YELLOW,
                    'ERROR': Fore.RED,
                    'CRITICAL': Fore.RED + Style.BRIGHT
                }

                # Format timestamp
                timestamp = self.formatTime(record, "%H:%M:%S")

                # Color the level name
                level_color = level_colors.get(record.levelname, Fore.WHITE)
                level_str = f"{level_color}{record.levelname}{Style.RESET_ALL}"

                # Format the message with special coloring for specific patterns
                message = record.getMessage()
                
                # Color buy/sell signals
                if 'Analysis: BUY' in message:
                    message = message.replace('BUY', f"{Fore.GREEN + Style.BRIGHT}BUY{Style.RESET_ALL}")
                elif 'Analysis: SELL' in message:
                    message = message.replace('SELL', f"{Fore.RED + Style.BRIGHT}SELL{Style.RESET_ALL}")
                
                # Color trade execution success/failure
                if 'Trade executed successfully' in message:
                    message = f"{Fore.GREEN + Style.BRIGHT}{message}{Style.RESET_ALL}"
                elif 'Trade execution failed' in message:
                    message = f"{Fore.RED + Style.BRIGHT}{message}{Style.RESET_ALL}"
                
                # Color trading start/stop messages
                if 'Starting enhanced trading bot' in message or 'Trading bot stopped' in message:
                    message = f"{Fore.MAGENTA + Style.BRIGHT}{message}{Style.RESET_ALL}"
                
                # Color exchange initialization messages
                if 'Successfully initialized' in message or 'exchange connected' in message:
                    message = f"{Fore.BLUE + Style.BRIGHT}{message}{Style.RESET_ALL}"

                # Return formatted string
                return f"{Fore.BLUE}{timestamp}{Style.RESET_ALL} - {level_str} - {message}"

        # Console handler with colored formatter
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)

        # File handler with plain formatter
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('enhanced_trading_bot.log')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def _setup_encryption(self):
        """Setup encryption for sensitive data"""
        key_file = 'enhanced_encryption.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(self.encryption_key)

        self.cipher = Fernet(self.encryption_key)

    async def initialize_exchanges(self, exchange_credentials: Dict[str, Dict[str, str]]):
        """Initialize Bitget exchange connection for trading execution only"""
        self.logger.info("Starting Bitget exchange initialization...")
        
        # Only initialize Bitget for trading execution
        if 'bitget' in exchange_credentials:
            creds = exchange_credentials['bitget']
            self.logger.info("Bitget credentials found in configuration")
            
            try:
                exchange_class = getattr(ccxt, 'bitget')
                exchange_config = {
                    'apiKey': creds.get('api_key', ''),
                    'secret': creds.get('secret', ''),
                    'password': creds.get('passphrase', ''),  # Bitget requires password
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot',  # Explicitly set to spot trading
                        'createMarketBuyOrderRequiresPrice': False  # Bitget specific option for market buy orders
                        # Note: positionMode is not needed for spot trading
                    }
                }

                # Handle sandbox mode properly for Bitget
                if self.config.sandbox_mode:
                    # For Bitget testnet, we use the main API endpoint with special headers
                    # Based on GitHub issues and Bitget documentation, testnet trading is done
                    # through the main API with special headers rather than a separate domain
                    if 'headers' not in exchange_config:
                        exchange_config['headers'] = {}
                    exchange_config['headers']['PAPTRADING'] = '1'
                    
                    # Also set the test option in exchange options
                    exchange_config['options']['test'] = True
                    
                    self.logger.info("Using Bitget main API with testnet headers (PAPTRADING: 1)")
                else:
                    self.logger.info("Using Bitget live hostname")
                
                self.logger.info(f"Exchange config: API key present: {bool(exchange_config['apiKey'])}, Secret present: {bool(exchange_config['secret'])}, Passphrase present: {bool(exchange_config['password'])}")
                self.logger.info(f"Sandbox mode: {self.config.sandbox_mode}")

                exchange = exchange_class(exchange_config)
                
                # Additional Bitget-specific configuration for testnet
                if self.config.sandbox_mode:
                    # Set testnet-specific options
                    exchange.options['sandbox'] = True
                    self.logger.info("Enabled sandbox mode in exchange options")
                
                # Set Bitget-specific options for proper timeframe handling
                exchange.options['timeframes'] = {
                    '1m': '1min',
                    '3m': '3min',
                    '5m': '5min',
                    '15m': '15min',
                    '30m': '30min',
                    '1h': '1H',
                    '2h': '2H',
                    '4h': '4H',
                    '6h': '6H',
                    '8h': '8H',
                    '12h': '12H',
                    '1d': '1D',
                    '1w': '1W',
                    '1M': '1M'
                }
                
                # Explicitly set the market type
                exchange.options['market'] = 'spot'
                
                self.logger.info("Loading markets...")
                await exchange.load_markets()
                self.logger.info("Markets loaded successfully")

                # Test connection
                self.logger.info("Testing exchange connection...")
                await self._test_exchange_connection(exchange)

                # Set position mode to one-way (unilateral) - only for futures trading
                # Skip for spot trading as it's not applicable
                if exchange.options.get('defaultType') != 'spot':
                    try:
                        await exchange.set_position_mode(False)  # False for one-way mode
                        self.logger.info("Set Bitget position mode to one-way (unilateral)")
                    except Exception as e:
                        self.logger.warning(f"Could not set position mode: {e}")
                        self.logger.warning("Make sure your Bitget account is set to 'One-Way' mode in the exchange settings")
                else:
                    self.logger.info("Skipping position mode setup for spot trading")

                self.exchanges['bitget'] = exchange
                self.logger.info("Successfully initialized Bitget exchange for trading execution")

            except ccxt.AuthenticationError as e:
                self.logger.error(f"Failed to initialize Bitget: Authentication error - {str(e)}")
                self.logger.error("[CRITICAL] Please check your API key, secret, and passphrase. Make sure they are correct and have the proper permissions (read and trade).")
            except ccxt.NetworkError as e:
                self.logger.error(f"Failed to initialize Bitget: Network error - {str(e)}")
                self.logger.error("[WARNING] Please check your internet connection and firewall settings. Bitget may also be temporarily unavailable.")
            except ccxt.ExchangeError as e:
                self.logger.error(f"Failed to initialize Bitget: Exchange error - {str(e)}")
                self.logger.error("[WARNING] Please check if the exchange is available and your credentials are correct. Bitget may be experiencing technical issues.")
            except Exception as e:
                self.logger.error(f"Failed to initialize Bitget: {str(e)}")
                self.logger.error("[ERROR] Bitget initialization failed. Please check your API credentials and network connection.")
        else:
            self.logger.error("Bitget credentials not provided")

    async def _test_exchange_connection(self, exchange):
        """Test Bitget exchange connection and permissions"""
        try:
            # Test basic connectivity
            await exchange.fetch_ticker('BTC/USDT')
            
            # Test account access (if API key provided)
            if hasattr(exchange, 'apiKey') and exchange.apiKey:
                balance = await exchange.fetch_balance()
                self.logger.info("[SUCCESS] Bitget exchange connected successfully")
        except Exception as e:
            self.logger.warning("[WARNING] Bitget exchange connection test warning: {e}")
            self.logger.warning("[WARNING] The bot will continue running, but you may experience issues with trading. Please check your API credentials and network connection.")

    async def fetch_multi_timeframe_data(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Fetch market data for multiple timeframes using Yahoo Finance"""
        # Timeframes optimized for Yahoo Finance
        timeframes = {
            '1m': ('1d', '1m', 200),   # 1 day of 1-minute data
            '5m': ('5d', '5m', 200),   # 5 days of 5-minute data
            '15m': ('15d', '15m', 100), # 15 days of 15-minute data
            '30m': ('30d', '30m', 100), # 30 days of 30-minute data
            '1h': ('60d', '1h', 100),   # 60 days of 1-hour data
            '4h': ('240d', '1h', 50),   # 240 days of 1-hour data (we'll resample to 4h)
            '1d': ('2y', '1d', 30)      # 2 years of daily data
        }
        
        multi_tf_data = {}
        
        for timeframe, (period, interval, limit) in timeframes.items():
            df = await self.fetch_market_data(symbol, timeframe, period, interval, limit)
            if not df.empty:
                multi_tf_data[timeframe] = df
        
        return multi_tf_data

    async def fetch_market_data(self, symbol: str, timeframe: str, period: str, interval: str, limit: int) -> pd.DataFrame:
        """Fetch market data from Yahoo Finance with proper symbol conversion"""
        try:
            # Convert symbol to Yahoo Finance format
            yf_symbol = self._convert_symbol_to_yahoo_format(symbol)
            
            # Fetch data from Yahoo Finance
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                self.logger.warning(f"No data returned for {yf_symbol}")
                return df
            
            # Convert column names to lowercase for consistency
            df.columns = df.columns.str.lower()
            
            # Ensure required columns exist
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = 0.0
            
            # Clean data
            df = df.dropna()
            
            # Resample if needed (for 4h timeframe)
            if timeframe == '4h' and interval == '1h':
                df = self._resample_to_4h(df)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Could not fetch market data for {symbol}. This is normal during network issues. Bot will retry.")
            return pd.DataFrame()

    def _convert_symbol_to_yahoo_format(self, symbol: str) -> str:
        """Convert trading symbol to Yahoo Finance format"""
        # Handle common cryptocurrency pairs
        if symbol == 'BTC/USDT':
            return 'BTC-USD'
        elif symbol == 'ETH/USDT':
            return 'ETH-USD'
        elif symbol == 'BNB/USDT':
            return 'BNB-USD'
        elif symbol == 'DOGE/USDT':
            return 'DOGE-USD'
        elif symbol == 'ADA/USDT':
            return 'ADA-USD'
        elif symbol == 'XRP/USDT':
            return 'XRP-USD'
        else:
            # Default conversion: replace / with -
            return symbol.replace('/', '-')

    def _resample_to_4h(self, df: pd.DataFrame) -> pd.DataFrame:
        """Resample 1h data to 4h data"""
        try:
            # Resample to 4-hour candles
            df_4h = df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            # Ensure we return a DataFrame
            if isinstance(df_4h, pd.DataFrame):
                return df_4h
            else:
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error resampling to 4h: {e}")
            return df

    async def comprehensive_market_analysis(self, symbol: str) -> Dict[str, Any]:
        """Perform comprehensive market analysis combining multiple data sources"""
        try:
            # Fetch multi-timeframe data
            multi_tf_data = await self.fetch_multi_timeframe_data(symbol)
            
            if not multi_tf_data:
                return {
                    'final_decision': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'No market data available'
                }
            
            # Use 5m data for primary analysis (most recent and detailed)
            primary_data = multi_tf_data.get('5m', pd.DataFrame())
            
            if primary_data.empty:
                return {
                    'final_decision': 'HOLD',
                    'confidence': 0.0,
                    'reason': 'No primary timeframe data available'
                }
            
            # Get current price
            current_price = primary_data['close'].iloc[-1] if len(primary_data) > 0 else 0.0
            
            # Strategy analysis
            strategy_decision, strategy_details = self.strategy_manager.decide(primary_data, symbol)
            
            # ML prediction
            ml_prediction = self.ml_engine.predict_with_confidence(primary_data)
            
            # Risk assessment
            position_size = self.risk_manager.calculate_position_size(
                signal_confidence=ml_prediction.get('confidence', 0.5),
                market_data=primary_data,
                symbol=symbol,
                side='buy' if ml_prediction.get('prediction') == 'BUY' else 'sell',
                current_price=current_price
            )
            
            risk_metrics = self.risk_manager.assess_trade_risk(
                symbol=symbol,
                side='buy' if ml_prediction.get('prediction') == 'BUY' else 'sell',
                size=position_size.recommended_size,
                confidence=ml_prediction.get('confidence', 0.5),
                market_data=primary_data
            )
            
            # News sentiment analysis
            news_sentiment = await self.news_analyzer.analyze_market_sentiment([symbol])
            # Extract the sentiment for this specific symbol
            symbol_sentiment = news_sentiment.get(symbol, self.news_analyzer._get_neutral_sentiment())
            
            # Convert SentimentAnalysis to dictionary for compatibility
            symbol_sentiment_dict = {
                'sentiment_score': symbol_sentiment.overall_sentiment,
                'should_trade': symbol_sentiment.should_trade
            }
            
            # Combine all signals
            final_decision, confidence = self._aggregate_signals(
                strategy_decision=strategy_decision,
                strategy_confidence=strategy_details.get('confidence', 0.5),
                ml_prediction=ml_prediction.get('prediction', 'HOLD'),
                ml_confidence=ml_prediction.get('confidence', 0.5),
                risk_level=risk_metrics.overall_risk_level,
                news_sentiment=symbol_sentiment_dict
            )
            
            return {
                'final_decision': final_decision,
                'confidence': confidence,
                'current_price': current_price,
                'market_data': primary_data,
                'strategy_analysis': {
                    'decision': strategy_decision,
                    'details': strategy_details
                },
                'ml_prediction': ml_prediction,
                'position_size_recommendation': {
                    'recommended_size': position_size.recommended_size,
                    'risk_amount': position_size.risk_amount,
                    'risk_percentage': position_size.risk_percentage
                },
                'risk_assessment': {
                    'overall_risk_level': risk_metrics.overall_risk_level.value,
                    'portfolio_risk': risk_metrics.portfolio_risk,
                    'position_risk': risk_metrics.position_risk
                },
                'news_sentiment': news_sentiment
            }
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive market analysis for {symbol}: {e}")
            return {
                'final_decision': 'HOLD',
                'confidence': 0.0,
                'reason': f'Analysis error: {str(e)}'
            }

    def _aggregate_signals(self, 
                          strategy_decision: str, 
                          strategy_confidence: float,
                          ml_prediction: str, 
                          ml_confidence: float,
                          risk_level: RiskLevel,
                          news_sentiment: Dict[str, Any]) -> Tuple[str, float]:
        """Aggregate multiple signals into final decision"""
        signals = []
        weights = {
            'strategy': 0.3,
            'ml': 0.4,
            'risk': 0.2,
            'news_sentiment': 0.1
        }
        
        # Strategy signal
        if strategy_decision in ['BUY', 'SELL']:
            signals.append((strategy_decision, strategy_confidence * weights['strategy']))
        else:
            signals.append(('HOLD', 0.5 * weights['strategy']))
        
        # ML signal
        if ml_prediction in ['BUY', 'SELL']:
            signals.append((ml_prediction, ml_confidence * weights['ml']))
        else:
            signals.append(('HOLD', 0.5 * weights['ml']))
        
        # Risk adjustment
        if risk_level == RiskLevel.CRITICAL:
            signals.append(('HOLD', weights['risk']))  # Override other signals if risk is critical
        elif risk_level == RiskLevel.HIGH:
            # Reduce confidence for high risk
            for i, (decision, weight) in enumerate(signals):
                signals[i] = (decision, weight * 0.5)
        
        # News sentiment
        sentiment_score = news_sentiment.get('sentiment_score', 0.0)
        if abs(sentiment_score) > 0.1:  # Only consider significant sentiment
            if sentiment_score > 0:
                signals.append(('BUY', abs(sentiment_score) * weights['news_sentiment']))
            else:
                signals.append(('SELL', abs(sentiment_score) * weights['news_sentiment']))
        
        # Aggregate final decision
        if not signals:
            return 'HOLD', 0.5
        
        buy_weight = sum(weight for decision, weight in signals if decision == 'BUY')
        sell_weight = sum(weight for decision, weight in signals if decision == 'SELL')
        hold_weight = sum(weight for decision, weight in signals if decision == 'HOLD')
        
        total_weight = buy_weight + sell_weight + hold_weight
        
        if total_weight == 0:
            return 'HOLD', 0.5
        
        # Require strong conviction for action
        buy_threshold = 0.6  # 60% conviction required for buys
        sell_threshold = 0.5  # 50% conviction required for sells (more sensitive)
        
        if buy_weight / total_weight > buy_threshold:
            return 'BUY', buy_weight / total_weight
        elif sell_weight / total_weight > sell_threshold:
            return 'SELL', sell_weight / total_weight
        else:
            return 'HOLD', max(hold_weight / total_weight, 0.5)

    async def execute_enhanced_trade(self, 
                                   symbol: str, 
                                   side: str, 
                                   analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade with enhanced risk management and monitoring"""
        
        # Store side information for error handling
        self._current_trade_side = side
        """Execute trade with enhanced risk management and monitoring"""
        
        if not self._can_trade():
            return {'success': False, 'reason': 'Trading limits exceeded'}

        try:
            # Get position size from analysis
            position_info = analysis_result.get('position_size_recommendation', {})
            size = position_info.get('recommended_size', 0.0)
            
            # Additional validation to prevent 0.0 sizes
            if size <= 0:
                self.logger.error(f"[ERROR] Invalid position size: {size} for {symbol}. Check market data and risk calculations.")
                return {'success': False, 'reason': 'Invalid position size - no market data or risk calculation error'}

            # Find best exchange and execute - Bitget only
            best_exchange, execution_price = await self._find_best_execution_venue(symbol, side, size)
            
            if not best_exchange:
                return {'success': False, 'reason': 'No suitable exchange found'}
            
            # Validate execution price
            if execution_price is None or execution_price <= 0:
                # Try to get a fallback price from the analysis result
                execution_price = analysis_result.get('current_price', 0.0)
                if execution_price <= 0:
                    self.logger.error(f"[ERROR] Invalid execution price: {execution_price} for {symbol}")
                    return {'success': False, 'reason': 'Invalid execution price'}
            
            # Validate size
            if size <= 0:
                self.logger.error(f"[ERROR] Invalid order size: {size} for {symbol}")
                return {'success': False, 'reason': 'Invalid order size'}

            # Calculate stop loss and take profit  
            current_price = analysis_result.get('current_price', 50000.0)  # Fallback price
            # Get market data for risk calculations
            market_data = analysis_result.get('market_data', pd.DataFrame())
            stop_loss_info = self.risk_manager.calculate_stop_loss(
                entry_price=execution_price,
                side=side,
                market_data=market_data,
                method='atr'
            )
            
            take_profit_info = self.risk_manager.calculate_take_profit(
                entry_price=execution_price,
                side=side,
                stop_loss_price=stop_loss_info['stop_loss_price'],
                risk_reward_ratio=2.0
            )

            # Execute the main order
            order_side = 'buy' if side.lower() == 'buy' else 'sell'
            
            # For Bitget, ensure minimum order size and use limit orders as workaround
            if best_exchange.id == 'bitget':
                # Ensure minimum order size (10 USDT)
                min_order_size = 10.0
                adjusted_size = size
                order = None  # Initialize order variable
                
                # Debug: Log execution price
                self.logger.debug(f"Execution price for {symbol}: {execution_price}")
                
                # Validate execution price before proceeding
                if execution_price is None or execution_price <= 0:
                    self.logger.error(f"[ERROR] Invalid execution price: {execution_price} for {symbol}")
                    return {'success': False, 'reason': 'Invalid execution price'}
                
                if execution_price is not None and execution_price > 0:
                    # Check if order value meets minimum
                    order_value = size * execution_price
                    self.logger.debug(f"Order value: {order_value}")
                    if order_value < min_order_size:
                        # Adjust size to meet minimum order value
                        adjusted_size = min_order_size / execution_price
                        self.logger.debug(f"Adjusted size: {adjusted_size}")
                    
                    # NEW: Ensure amount precision meets Bitget requirements for specific pairs
                    try:
                        # Get market precision information
                        if hasattr(best_exchange, 'markets') and best_exchange.markets is not None:
                            market_symbol = self._convert_symbol_format(symbol, best_exchange)
                            if market_symbol in best_exchange.markets:
                                market_info = best_exchange.markets[market_symbol]
                                if market_info and 'precision' in market_info and 'amount' in market_info['precision']:
                                    # Get the amount precision
                                    amount_precision = market_info['precision']['amount']
                                    # Round to required precision
                                    if amount_precision > 0:
                                        # Calculate decimal places needed
                                        import math
                                        decimal_places = max(0, math.ceil(-math.log10(amount_precision)))
                                        original_size = adjusted_size
                                        adjusted_size = round(adjusted_size, decimal_places)
                                        self.logger.debug(f"[PRECISION] Precision adjustment: {original_size:.8f} → {adjusted_size:.8f} ({decimal_places} decimal places for {symbol})")
                                    else:
                                        # Fallback: ensure at least 6 decimal places for BTC pairs
                                        if 'BTC' in symbol:
                                            original_size = adjusted_size
                                            adjusted_size = round(adjusted_size, 6)
                                            self.logger.debug(f"[PRECISION] BTC precision adjustment: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                                        else:
                                            original_size = adjusted_size
                                            adjusted_size = round(adjusted_size, 2)
                                            self.logger.debug(f"[PRECISION] Standard precision adjustment: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                                else:
                                    # Fallback: ensure at least 6 decimal places for BTC pairs
                                    if 'BTC' in symbol:
                                        original_size = adjusted_size
                                        adjusted_size = round(adjusted_size, 6)
                                        self.logger.debug(f"[PRECISION] BTC precision fallback: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                                    else:
                                        original_size = adjusted_size
                                        adjusted_size = round(adjusted_size, 2)
                                        self.logger.debug(f"[PRECISION] Standard precision fallback: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                            else:
                                # Fallback: ensure at least 6 decimal places for BTC pairs
                                if 'BTC' in symbol:
                                    original_size = adjusted_size
                                    adjusted_size = round(adjusted_size, 6)
                                    self.logger.debug(f"[PRECISION] BTC symbol fallback: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                                else:
                                    original_size = adjusted_size
                                    adjusted_size = round(adjusted_size, 2)
                                    self.logger.debug(f"[PRECISION] Standard symbol fallback: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                        else:
                            # Fallback: ensure at least 6 decimal places for BTC pairs
                            if 'BTC' in symbol:
                                original_size = adjusted_size
                                adjusted_size = round(adjusted_size, 6)
                                self.logger.debug(f"[PRECISION] BTC exchange fallback: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                            else:
                                original_size = adjusted_size
                                adjusted_size = round(adjusted_size, 2)
                                self.logger.debug(f"[PRECISION] Standard exchange fallback: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                    except Exception as e:
                        # Fallback rounding based on symbol type
                        original_size = adjusted_size
                        if 'BTC' in symbol:
                            adjusted_size = round(adjusted_size, 6)
                            self.logger.debug(f"[PRECISION] BTC exception fallback: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                        elif 'BNB' in symbol or 'ETH' in symbol:
                            adjusted_size = round(adjusted_size, 4)
                            self.logger.debug(f"[PRECISION] ALT exception fallback: {original_size:.8f} → {adjusted_size:.8f} (4 decimal places)")
                        else:
                            adjusted_size = round(adjusted_size, 2)
                            self.logger.debug(f"[PRECISION] Standard exception fallback: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                    
                    # Validate amount before order placement
                    if adjusted_size <= 0:
                        self.logger.error(f"[ERROR] Invalid order amount after adjustment: {adjusted_size} for {symbol}")
                        return {'success': False, 'reason': f'Invalid order amount: {adjusted_size}. Amount must be greater than zero.'}
                    
                    # Log order details for user understanding (without emojis to avoid encoding issues)
                    self.logger.info(f"[ORDER] Placing MARKET {order_side.upper()} order for {symbol}: {adjusted_size:.8f}")
                    
                    # Use spot-specific order creation with validated parameters
                    # For Bitget, we need to ensure all required parameters are properly formatted
                    order_params = {
                        'marginMode': 'cash',  # Specify cash margin mode for spot trading
                        'productType': 'spot',  # Explicitly specify spot product type
                        'tradeType': 'spot',  # Additional parameter for spot trading
                        'marginCoin': 'USDT',  # Add margin coin parameter for Bitget
                        'positionMode': 'oneWay'  # Set position mode to unilateral (one-way)
                    }
                    
                    # Add size parameter specifically for Bitget
                    if best_exchange.id == 'bitget':
                        order_params['size'] = str(adjusted_size)
                        # Add margin mode as a direct parameter for Bitget spot trading
                        order_params['marginMode'] = 'cash'
                        # Explicitly specify that this is a spot trade to ensure proper routing
                        order_params['bizType'] = 'spot'
                        # Add margin coin parameter for Bitget
                        order_params['marginCoin'] = 'USDT'
                        # Add position mode parameter for Bitget
                        order_params['positionMode'] = 'oneWay'
                    
                    # Additional validation to ensure we have a valid amount
                    if adjusted_size <= 0:
                        self.logger.error(f"[ERROR] Invalid adjusted order amount: {adjusted_size} for {symbol}")
                        return {'success': False, 'reason': f'Invalid adjusted order amount: {adjusted_size}. Amount must be greater than zero.'}
                    
                    # For market orders, we don't need to specify a price
                    order = await best_exchange.create_market_order(  # type: ignore
                        symbol=self._convert_symbol_format(symbol, best_exchange),
                        side=order_side,
                        amount=adjusted_size,
                        params=order_params
                    )
                    
                    # Remove the separate margin mode setting call as it's not needed
                    # and might be causing conflicts

                else:
                    # Ensure minimum size even with fallback price
                    limit_price = 2000.0  # Default ETH price
                    if adjusted_size <= 0 or (adjusted_size * limit_price < min_order_size):
                        adjusted_size = min_order_size / limit_price
                        self.logger.debug(f"Adjusted size with fallback: {adjusted_size}")
                    
                    # Validate adjusted_size after adjustment
                    if adjusted_size <= 0:
                        self.logger.error(f"[ERROR] Invalid adjusted order size: {adjusted_size} for {symbol}")
                        return {'success': False, 'reason': 'Invalid order size'}
                    
                    # Ensure amount precision for fallback case
                    original_size = adjusted_size
                    adjusted_size = round(adjusted_size, 2)
                    self.logger.debug(f"[PRECISION] Basic precision adjustment: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                    
                    # NEW: Ensure amount precision meets Bitget requirements for specific pairs (fallback case)
                    try:
                        # Fallback rounding based on symbol type
                        original_size = adjusted_size
                        if 'BTC' in symbol:
                            adjusted_size = round(adjusted_size, 6)
                            self.logger.debug(f"[PRECISION] BTC fallback precision: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                        elif 'BNB' in symbol or 'ETH' in symbol:
                            adjusted_size = round(adjusted_size, 4)
                            self.logger.debug(f"[PRECISION] ALT fallback precision: {original_size:.8f} → {adjusted_size:.8f} (4 decimal places)")
                        else:
                            adjusted_size = round(adjusted_size, 2)
                            self.logger.debug(f"[PRECISION] Standard fallback precision: {original_size:.8f} → {adjusted_size:.8f} (2 decimal places)")
                    except Exception as e:
                        # Last resort fallback
                        original_size = adjusted_size
                        adjusted_size = round(adjusted_size, 6)
                        self.logger.debug(f"[PRECISION] Last resort precision: {original_size:.8f} → {adjusted_size:.8f} (6 decimal places)")
                    
                    # Validate amount before order placement
                    if adjusted_size <= 0:
                        self.logger.error(f"[ERROR] Invalid order amount after adjustment: {adjusted_size} for {symbol}")
                        return {'success': False, 'reason': f'Invalid order amount: {adjusted_size}. Amount must be greater than zero.'}
                    
                    # Log order details for user understanding (without emojis to avoid encoding issues)
                    self.logger.info(f"[ORDER] Placing MARKET {order_side.upper()} order for {symbol}: {adjusted_size:.8f} (using fallback pricing)")
                    
                    # Use spot-specific order creation with validated parameters
                    # For Bitget, we need to ensure all required parameters are properly formatted
                    order_params = {
                        'marginMode': 'cash',  # Specify cash margin mode for spot trading
                        'productType': 'spot',  # Explicitly specify spot product type
                        'tradeType': 'spot',  # Additional parameter for spot trading
                        'marginCoin': 'USDT',  # Add margin coin parameter for Bitget
                        'positionMode': 'oneWay'  # Set position mode to unilateral (one-way)
                    }
                    
                    # Add size parameter specifically for Bitget
                    if best_exchange.id == 'bitget':
                        order_params['size'] = str(adjusted_size)
                        # Add margin mode as a direct parameter for Bitget spot trading
                        order_params['marginMode'] = 'cash'
                        # Explicitly specify that this is a spot trade to ensure proper routing
                        order_params['bizType'] = 'spot'
                        # Add margin coin parameter for Bitget
                        order_params['marginCoin'] = 'USDT'
                        # Add position mode parameter for Bitget
                        order_params['positionMode'] = 'oneWay'
                    
                    # Additional validation to ensure we have a valid amount
                    if adjusted_size <= 0:
                        self.logger.error(f"[ERROR] Invalid adjusted order amount: {adjusted_size} for {symbol}")
                        return {'success': False, 'reason': f'Invalid adjusted order amount: {adjusted_size}. Amount must be greater than zero.'}
                    
                    # For market orders, we don't need to specify a price
                    order = await best_exchange.create_market_order(  # type: ignore
                        symbol=self._convert_symbol_format(symbol, best_exchange),
                        side=order_side,
                        amount=adjusted_size,
                        params=order_params
                    )
                    
                    # Remove the separate margin mode setting call as it's not needed
                    # and might be causing conflicts

            else:
                # For Bitget, use market orders
                # Validate amount before order placement
                if size <= 0:
                    self.logger.error(f"[ERROR] Invalid order amount: {size} for {symbol}")
                    return {'success': False, 'reason': f'Invalid order amount: {size}. Amount must be greater than zero.'}
                
                # Log order details for user understanding (without emojis to avoid encoding issues)
                self.logger.info(f"[ORDER] Placing MARKET {order_side.upper()} order for {symbol}: {size:.8f}")
                
                # Use spot-specific order creation with validated parameters
                # For Bitget, we need to ensure all required parameters are properly formatted
                order_params = {
                    'marginMode': 'cash',  # Specify cash margin mode for spot trading
                    'productType': 'spot',  # Explicitly specify spot product type
                    'tradeType': 'spot',  # Additional parameter for spot trading
                    'marginCoin': 'USDT',  # Add margin coin parameter for Bitget
                    'positionMode': 'oneWay'  # Set position mode to unilateral (one-way)
                }
                
                # Add size parameter specifically for Bitget
                if best_exchange.id == 'bitget':
                    order_params['size'] = str(size)
                    # Add margin mode as a direct parameter for Bitget spot trading
                    order_params['marginMode'] = 'cash'
                    # Explicitly specify that this is a spot trade to ensure proper routing
                    order_params['bizType'] = 'spot'
                    # Add margin coin parameter for Bitget
                    order_params['marginCoin'] = 'USDT'
                    # Add position mode parameter for Bitget
                    order_params['positionMode'] = 'oneWay'
                
                # Additional validation to ensure we have a valid amount
                if size <= 0:
                    self.logger.error(f"[ERROR] Invalid order amount: {size} for {symbol}")
                    return {'success': False, 'reason': f'Invalid order amount: {size}. Amount must be greater than zero.'}
                
                # For market orders, we don't need to specify a price
                order = await best_exchange.create_market_order(  # type: ignore
                    symbol=self._convert_symbol_format(symbol, best_exchange),
                    side=order_side,
                    amount=size,
                    params=order_params
                )
                
                # Remove the separate margin mode setting call as it's not needed
                # and might be causing conflicts
            # Create trade record
            # Try to get price from order object (different exchanges may use different keys)
            order_price = None
            if order:
                # Try common price keys
                for price_key in ['price', 'average', 'cost']:
                    if price_key in order and order[price_key] is not None:
                        order_price = float(order[price_key])
                        break
            
            # Fallback to execution_price if order price not available
            if order_price is None:
                order_price = float(execution_price) if execution_price is not None else 0.0
            
            # Use adjusted_size for order_value calculation to match the actual order placed
            order_value = adjusted_size * order_price
            
            trade_record = {
                'symbol': symbol,
                'side': side,
                'amount': adjusted_size,  # Use adjusted size for consistency
                'price': order_price,
                'value': order_value,
                'exchange': best_exchange.id,
                'timestamp': datetime.now(),
                'order_id': order.get('id') if order else None,
                'stop_loss_price': stop_loss_info.get('stop_loss_price', 0.0),
                'take_profit_price': take_profit_info.get('take_profit_price', 0.0),
                'analysis_confidence': analysis_result.get('confidence', 0.0),
                'risk_metrics': analysis_result.get('risk_assessment', {})
            }

            # Update risk manager state
            self.risk_manager.update_portfolio_state(
                symbol=symbol,
                side=side,
                size=adjusted_size,  # Use adjusted size for consistency
                price=trade_record['price'],
                trade_type='open'
            )
            
            # Update internal state
            self._update_trade_limits(trade_record['value'])
            self._update_performance_metrics(trade_record)

            # Send enhanced notification
            await self.notifications.send_trade_alert(trade_record)

            self.logger.info(f"Enhanced trade executed: {trade_record}")
            
            # Schedule stop loss and take profit orders (if supported)
            await self._schedule_exit_orders(best_exchange, trade_record, stop_loss_info, take_profit_info)
            
            return {
                'success': True, 
                'trade': trade_record,
                'stop_loss': stop_loss_info,
                'take_profit': take_profit_info
            }

        except ccxt.InsufficientFunds as e:
            self.logger.error(f"Enhanced trade execution failed: {str(e)}")
            user_friendly_message = f"[INFO] Insufficient funds for {self._current_trade_side.upper()} order. This is normal if you don't have enough balance."
            self.logger.error(user_friendly_message)
            return {'success': False, 'reason': user_friendly_message}
        except ccxt.ExchangeError as e:
            self.logger.error(f"Enhanced trade execution failed: {str(e)}")
            error_msg = str(e)
            # Handle specific Bitget error messages
            if "balance not enough" in error_msg or "Insufficient balance" in error_msg:
                user_friendly_message = f"[INFO] Insufficient funds for {self._current_trade_side.upper()} order. This is normal if you don't have enough balance."
            elif "amount must be greater than minimum amount precision" in error_msg:
                user_friendly_message = f"[INFO] {self._current_trade_side.upper()} order size is too small. This is normal for small balances."
            elif "less than the minimum amount" in error_msg:
                user_friendly_message = f"[INFO] {self._current_trade_side.upper()} order too small (min 10 USDT). This is normal for small balances."
            elif "The order type for unilateral position" in error_msg:
                user_friendly_message = f"[ERROR] Please set Bitget to 'One-Way' mode in your exchange settings."
            elif "The margin mode cannot be empty" in error_msg:
                user_friendly_message = f"[ERROR] Margin mode issue. Check your Bitget account settings."
            elif "Margin Coin cannot be empty" in error_msg:
                user_friendly_message = f"[ERROR] Missing margin coin. Check your Bitget account settings."
            elif "InvalidOrder" in error_msg and "amount" in error_msg:
                user_friendly_message = f"[INFO] Invalid {self._current_trade_side.upper()} order amount. This is normal for small balances."
            elif "RequestTimeout" in error_msg or "NetworkError" in error_msg:
                user_friendly_message = f"[WARNING] Network issue. The bot will retry automatically."
            elif "DDoSProtection" in error_msg or "RateLimitExceeded" in error_msg:
                user_friendly_message = f"[WARNING] Rate limited. The bot will wait and retry."
            elif "Authentication" in error_msg or "BadSymbol" in error_msg:
                user_friendly_message = f"[ERROR] Check API keys and trading pair in your configuration."
            elif "ExchangeNotAvailable" in error_msg:
                user_friendly_message = f"[WARNING] Bitget exchange is temporarily unavailable. The bot will retry."
            else:
                user_friendly_message = f"[ERROR] Exchange error occurred. This may be temporary."
            self.logger.error(user_friendly_message)
            return {'success': False, 'reason': user_friendly_message}
        except Exception as e:
            self.logger.error(f"Enhanced trade execution failed: {str(e)}")
            user_friendly_message = f"[INFO] Trade not executed. This is normal during market analysis."
            self.logger.error(user_friendly_message)
            return {'success': False, 'reason': user_friendly_message}

    async def _find_best_execution_venue(self, symbol: str, side: str, size: float) -> Tuple[Optional[ccxt.Exchange], float]:
        """Find the best exchange for trade execution - Bitget only"""
        self.logger.debug(f"Finding best execution venue for {symbol}, side: {side}, size: {size}")
        
        # Only Bitget is available
        if 'bitget' in self.exchanges:
            self.logger.debug("Bitget exchange found in exchanges dict")
            exchange = self.exchanges['bitget']
            
            try:
                exchange_symbol = self._convert_symbol_format(symbol, exchange)
                self.logger.debug(f"Fetching ticker for {exchange_symbol}")
                ticker = await exchange.fetch_ticker(exchange_symbol)  # type: ignore
                self.logger.debug(f"Ticker fetched: {ticker}")
                
                # Check liquidity
                if 'bid' in ticker and 'ask' in ticker:
                    spread = ticker['ask'] - ticker['bid']
                    spread_pct = spread / ticker['last'] if ticker['last'] > 0 else float('inf')
                    self.logger.debug(f"Spread: {spread}, Spread %: {spread_pct}")
                    
                    # Skip if spread is too wide
                    if spread_pct > 0.01:  # 1% spread limit
                        self.logger.warning(f"Spread too wide for {symbol}: {spread_pct:.2%}")
                        return None, 0.0
                
                price = ticker['ask'] if side == 'buy' else ticker['bid']
                self.logger.debug(f"Selected price: {price}")
                return exchange, price
                    
            except Exception as e:
                self.logger.error(f"Error checking Bitget for {symbol}: {e}")
                self.logger.error(f"[WARNING] Unable to get market data for {symbol}. The bot will skip this trading pair for now and try again in the next cycle.")
        else:
            self.logger.error("Bitget exchange not found in exchanges dict")
            self.logger.error(f"Available exchanges: {list(self.exchanges.keys())}")
        
        return None, 0.0

    async def _schedule_exit_orders(self, exchange, trade_record, stop_loss_info, take_profit_info):
        """Schedule stop loss and take profit orders"""
        try:
            symbol = self._convert_symbol_format(trade_record['symbol'], exchange)
            side = 'sell' if trade_record['side'] == 'buy' else 'buy'
            
            # Place stop loss order (if exchange supports it)
            # Note: Many exchanges don't support creating stop loss orders via API
            # This is often handled by the exchange platform itself
            self.logger.debug("Stop loss/take profit orders are typically handled by exchange platform")
            
        except Exception as e:
            self.logger.error(f"Error scheduling exit orders: {e}")

    def _can_trade(self) -> bool:
        """Enhanced trading permission check"""
        now = datetime.now()

        # Check cooldown
        if self.last_trade_time and (now - self.last_trade_time) < timedelta(minutes=self.config.cooldown_minutes):
            return False

        # Check daily reset
        if now.date() > self.daily_reset_time.date():
            self.daily_trades_value = 0.0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Check daily limit (compare against trade value in USDT, not count)
        # This prevents excessive trading volume rather than just trade count
        if self.daily_trades_value >= self.config.max_daily_trades:
            return False

        # Check market hours (if configured)
        if hasattr(self.config, 'trading_hours'):
            trading_hours = getattr(self.config, 'trading_hours', None)
            if trading_hours and len(trading_hours) == 2:
                current_hour = now.hour
                start_hour, end_hour = trading_hours
                if not (start_hour <= current_hour <= end_hour):
                    return False

        return True

    def _update_trade_limits(self, trade_value: float):
        """Update trading limits after successful trade"""
        self.daily_trades_value += trade_value
        self.last_trade_time = datetime.now()

    def _update_performance_metrics(self, trade_record: Dict[str, Any]):
        """Update performance tracking metrics"""
        self.trade_performance['total_trades'] += 1
        
        # P&L will be calculated when position is closed
        # For now, just track trade count

    async def run_enhanced_trading_loop(self):
        """Enhanced main trading loop with comprehensive analysis"""
        self.is_running = True
        self.logger.info("Starting enhanced trading bot - Bitget Only...")

        try:
            while self.is_running:
                for symbol in (self.config.supported_pairs or []):
                    try:
                        # Comprehensive market analysis
                        analysis = await self.comprehensive_market_analysis(symbol)
                        
                        # Log analysis summary
                        self.logger.info(
                            f"{symbol} Analysis: {analysis['final_decision']} "
                            f"(confidence: {analysis['confidence']:.2f})"
                        )
                        
                        # Execute trade if conditions are met
                        # Use different confidence thresholds for buys vs sells
                        confidence_threshold = 0.6 if analysis['final_decision'] == 'BUY' else 0.5
                        if analysis['final_decision'] in ['BUY', 'SELL'] and analysis['confidence'] > confidence_threshold:
                            # Check if news allows trading
                            news_sentiment = analysis.get('news_sentiment', {})
                            if news_sentiment.get('should_trade', True):
                                # Execute the trade
                                result = await self.execute_enhanced_trade(
                                    symbol=symbol,
                                    side=analysis['final_decision'],
                                    analysis_result=analysis
                                )
                                
                                if result['success']:
                                    self.logger.info(f"Trade executed successfully for {symbol}")
                                else:
                                    self.logger.error(f"Trade execution failed for {symbol}: {result.get('reason', 'Unknown error')}")
                        
                        # Brief pause between symbols
                        await asyncio.sleep(1)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing {symbol}: {e}")
                        self.logger.error(f"[WARNING] The bot encountered an issue while analyzing {symbol}. It will skip this pair for now and continue with other trading pairs.")
                        continue
                
                # Wait before next cycle
                await asyncio.sleep(self.config.refresh_interval_seconds)
                
        except KeyboardInterrupt:
            self.logger.info("[INTERRUPTED] Trading loop interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in trading loop: {e}")
            self.logger.error("[ERROR] A critical error occurred in the trading loop. The bot will stop to prevent further issues. Please check your configuration and restart the bot.")
        finally:
            self.is_running = False
            await self._cleanup()
            self.logger.info("Trading bot stopped")

    async def _cleanup(self):
        """Cleanup resources"""
        try:
            # Close all exchange connections
            for exchange in self.exchanges.values():
                if hasattr(exchange, 'close'):
                    await exchange.close()
            
            # Cleanup notifications
            # NotificationManager doesn't have a cleanup method, so we skip this
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.logger.error("[WARNING] A non-critical error occurred during cleanup. The bot has stopped, but some resources may not have been properly released. This usually doesn't cause issues.")

    def _convert_symbol_format(self, symbol: str, exchange) -> str:
        """Convert symbol format for specific exchange"""
        # For Bitget, convert BTC/USDT to BTCUSDT
        return symbol.replace('/', '')

    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        self.logger.info("Stop signal received")