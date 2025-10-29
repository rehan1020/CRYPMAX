# bot/notifications.py
import asyncio
import logging
from typing import Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

# Add colorama imports for colored console output
try:
    from colorama import init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

from core.config import BotConfig

class NotificationManager:
    """Handle notifications via email and Telegram"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = logging.getLogger('NotificationManager')

        # Telegram setup
        self.telegram_enabled = bool(config.telegram_bot_token and config.telegram_chat_id)
        if self.telegram_enabled:
            self.telegram_base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"

        # Email setup
        self.email_enabled = bool(config.email_smtp_server and config.email_username and config.email_password)

    async def send_trade_alert(self, trade_data: Dict[str, Any]):
        """Send trade execution alert"""
        symbol = trade_data['symbol']
        side = trade_data['side'].upper()
        amount = trade_data['amount']
        price = trade_data['price']
        value = trade_data['value']
        exchange = trade_data['exchange']

        # Add color coding for console output
        if COLORAMA_AVAILABLE:
            try:
                from colorama import Fore, Style
                if side == 'BUY':
                    side_colored = f"{Fore.GREEN + Style.BRIGHT}{side}{Style.RESET_ALL}"
                    emoji = "🚀"
                else:  # SELL
                    side_colored = f"{Fore.RED + Style.BRIGHT}{side}{Style.RESET_ALL}"
                    emoji = "🔻"
            except ImportError:
                side_colored = side
                emoji = "🚀" if side == 'BUY' else "🔻"
        else:
            side_colored = side
            emoji = "🚀" if side == 'BUY' else "🔻"

        message = f"""
{emoji} TRADE EXECUTED {emoji}

Symbol: {symbol}
Action: {side_colored}
Amount: {amount:.6f}
Price: ${price:.2f}
Value: ${value:.2f}
Exchange: {exchange}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        subject = f"Trade Alert: {side} {symbol}"

        await self._send_notification(message, subject)

    async def send_analysis_alert(self, symbol: str, decision: str, confidence: float):
        """Send market analysis alert"""
        # Add color coding for console output
        if COLORAMA_AVAILABLE:
            try:
                from colorama import Fore, Style
                if decision == 'BUY':
                    decision_colored = f"{Fore.GREEN + Style.BRIGHT}{decision}{Style.RESET_ALL}"
                    emoji = "📈"
                elif decision == 'SELL':
                    decision_colored = f"{Fore.RED + Style.BRIGHT}{decision}{Style.RESET_ALL}"
                    emoji = "📉"
                else:
                    decision_colored = decision
                    emoji = "📊"
            except ImportError:
                decision_colored = decision
                emoji = "📊"
        else:
            decision_colored = decision
            emoji = "📊"

        message = f"""
{emoji} MARKET ANALYSIS {emoji}

Symbol: {symbol}
Decision: {decision_colored}
Confidence: {confidence:.1%}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        subject = f"Analysis Alert: {decision} {symbol}"

        await self._send_notification(message, subject)

    async def send_system_alert(self, alert_type: str, message: str):
        """Send system status alerts"""
        # Add color coding for console output
        if COLORAMA_AVAILABLE:
            try:
                from colorama import Fore, Style
                alert_colored = f"{Fore.YELLOW + Style.BRIGHT}{alert_type}{Style.RESET_ALL}"
                emoji = "⚠️"
            except ImportError:
                alert_colored = alert_type
                emoji = "⚠️"
        else:
            alert_colored = alert_type
            emoji = "⚠️"

        full_message = f"""
{emoji} SYSTEM ALERT {emoji}

Type: {alert_colored}
Message: {message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        subject = f"System Alert: {alert_type}"

        await self._send_notification(full_message, subject)

    async def send_daily_report(self, stats: Dict[str, Any]):
        """Send daily performance report"""
        total_trades = stats.get('total_trades', 0)
        win_rate = stats.get('win_rate', 0)
        total_pnl = stats.get('total_pnl', 0)
        avg_trade = stats.get('avg_trade', 0)

        # Format total_pnl with commas
        total_pnl_formatted = f"{total_pnl:,.2f}"

        message = f"""
📈 DAILY REPORT 📈

Total Trades: {total_trades}
Win Rate: {win_rate:.1f}%
Total P&L: ${total_pnl_formatted}
Average Trade: ${avg_trade:.2f}
Date: {datetime.now().strftime('%Y-%m-%d')}

Keep trading smart! 🤖
        """.strip()

        subject = f"Daily Report: {total_trades} trades, {win_rate:.1f}% win rate"

        await self._send_notification(message, subject)

    async def _send_notification(self, message: str, subject: str):
        """Send notification via all enabled channels"""
        tasks = []

        if self.telegram_enabled:
            tasks.append(self._send_telegram(message))

        if self.email_enabled:
            tasks.append(self._send_email(message, subject))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        else:
            self.logger.warning("No notification channels configured")

    async def _send_telegram(self, message: str):
        """Send message via Telegram"""
        try:
            # Only send if credentials are configured
            if not self.config.telegram_bot_token or not self.config.telegram_chat_id or self.config.telegram_bot_token == 'your_telegram_bot_token_here':
                return
                
            url = f"{self.telegram_base_url}/sendMessage"
            data = {
                'chat_id': self.config.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            self.logger.info("Telegram notification sent successfully")

        except Exception as e:
            self.logger.warning(f"Failed to send Telegram notification: {str(e)}")

    async def _send_email(self, message: str, subject: str):
        """Send email notification"""
        try:
            # Only send if credentials are configured
            if not self.config.email_username or not self.config.email_password or self.config.email_username == 'your_email@gmail.com':
                return
                
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_username or ""  # type: ignore
            msg['To'] = self.config.email_username or ""  # Send to self, or configure recipient
            msg['Subject'] = subject

            # Add body
            msg.attach(MIMEText(message, 'plain'))

            # Create SMTP session
            with smtplib.SMTP(self.config.email_smtp_server or "localhost", self.config.email_smtp_port) as server:
                server.starttls()
                server.login(self.config.email_username or "", self.config.email_password or "")

                # Send email
                text = msg.as_string()
                server.sendmail(self.config.email_username or "", self.config.email_username or "", text)

            self.logger.info("Email notification sent successfully")

        except Exception as e:
            self.logger.warning(f"Failed to send email notification: {str(e)}")

    async def send_alert(self, message: str):
        """Send a simple alert message"""
        await self.send_system_alert("ALERT", message)

    async def test_notifications(self):
        """Test all notification channels"""
        test_message = f"""
🧪 NOTIFICATION TEST 🧪

This is a test message to verify notification channels are working correctly.

If you received this, notifications are properly configured!

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()

        self.logger.info("Testing notification channels...")
        await self._send_notification(test_message, "Notification Test")

        # Wait a moment for delivery
        await asyncio.sleep(2)
        self.logger.info("Notification test completed")

class NewsFilter:
    """Filter and analyze financial news for trading signals"""

    def __init__(self):
        self.news_sources = [
            'https://finance.yahoo.com/news',
            'https://www.coindesk.com/news',
            'https://cointelegraph.com/news',
            'https://www.reuters.com/markets/currencies/',
        ]
        self.sentiment_keywords = {
            'positive': ['bullish', 'surge', 'rally', 'breakthrough', 'adoption', 'partnership', 'upgrade'],
            'negative': ['bearish', 'crash', 'dump', 'sell-off', 'hack', 'scam', 'ban', 'regulation'],
            'neutral': ['stable', 'sideways', 'consolidation', 'holding']
        }

    async def analyze_news_impact(self, symbol: str) -> Dict[str, Any]:
        """Analyze recent news for potential market impact"""
        # This is a simplified implementation
        # In a real bot, you'd integrate with news APIs

        try:
            # Simulate news analysis (replace with actual news API calls)
            sentiment_score = 0.0  # -1 to 1 scale
            news_volume = 0
            relevant_articles = []

            # Mock analysis - in reality, fetch and analyze news
            analysis = {
                'symbol': symbol,
                'sentiment_score': sentiment_score,
                'news_volume': news_volume,
                'should_trade': True,  # Default to allowing trade for mock implementation
                'relevant_articles': relevant_articles,
                'last_updated': datetime.now()
            }

            return analysis

        except Exception as e:
            logging.error(f"News analysis failed for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'sentiment_score': 0.0,
                'news_volume': 0,
                'should_trade': True,  # Default to allowing trade
                'error': str(e)
            }

import pandas as pd

class VolumeSpikeFilter:
    """Detect and filter volume spikes"""

    def __init__(self, spike_threshold: float = 2.5):
        self.spike_threshold = spike_threshold

    def detect_spike(self, df: pd.DataFrame) -> bool:
        """Detect if current volume is a spike"""
        if len(df) < 20:
            return False

        recent_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-20:-1].mean()
        std_volume = df['volume'].iloc[-20:-1].std()

        if std_volume == 0:
            # If no variation, check if recent volume is significantly higher than average
            return bool(recent_volume > avg_volume * 2)

        z_score = (recent_volume - avg_volume) / std_volume
        return bool(z_score > self.spike_threshold)

class SpreadChecker:
    """Check bid-ask spread for trading viability"""

    def __init__(self, max_spread_bps: int = 10):
        self.max_spread_bps = max_spread_bps

    async def check_spread(self, exchange, symbol: str) -> Dict[str, Any]:
        """Check if spread is acceptable for trading"""
        try:
            ticker = await exchange.fetch_ticker(symbol)

            if 'bid' not in ticker or 'ask' not in ticker:
                return {'acceptable': False, 'reason': 'No bid/ask data'}

            bid = ticker['bid']
            ask = ticker['ask']
            spread = ask - bid
            spread_bps = (spread / bid) * 10000  # Basis points

            return {
                'acceptable': spread_bps <= self.max_spread_bps,
                'spread_bps': spread_bps,
                'bid': bid,
                'ask': ask
            }

        except Exception as e:
            return {'acceptable': False, 'reason': str(e)}
