# Crympax Personal Trading Bot - User Guide

This comprehensive guide explains how to set up, configure, and use the Crympax personal cryptocurrency trading bot. The bot is designed for single-user operation with a focus on simplicity and safety.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running the Bot](#running-the-bot)
5. [Trading Strategies](#trading-strategies)
6. [Risk Management](#risk-management)
7. [Stop-Loss System](#stop-loss-system)
8. [Error Handling](#error-handling)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Troubleshooting](#troubleshooting)

## Getting Started

The personal trading bot is a sophisticated yet user-friendly cryptocurrency trading system that:

- Connects to Bitget exchange for live trading
- Uses Yahoo Finance for market data analysis
- Implements multiple trading strategies with machine learning
- Provides comprehensive risk management
- Features automated stop-loss and take-profit mechanisms
- Works in both live and sandbox (testnet) modes

### Key Features

- **Single Exchange Support**: Trade exclusively on Bitget (simpler and safer)
- **Multi-Strategy Analysis**: RSI, MACD, Bollinger Bands, Moving Averages, Volume, and Candlestick Patterns
- **Machine Learning**: AI-powered market predictions
- **Risk Management**: Advanced position sizing and portfolio protection
- **Automated Trading**: Fully automated buy/sell decisions
- **Real-time Monitoring**: Live dashboard with color-coded status updates

## Installation

### Prerequisites

- Python 3.8 or higher
- Bitget exchange account with API keys
- (Optional) Telegram account for notifications

### Setup Steps

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your configuration (see Configuration section)

3. **Verify Installation**:
   ```bash
   python test_components.py
   ```

## Configuration

All bot settings are configured through the `.env` file. Here are the key configuration options:

### Essential Settings

```env
# Exchange API Credentials (required)
BITGET_API_KEY=your_bitget_api_key
BITGET_SECRET=your_bitget_secret
BITGET_PASSPHRASE=your_bitget_passphrase

# Sandbox Mode (recommended for testing)
SANDBOX_MODE=true
```

### Trading Parameters

```env
# Minimum investment per trade (in USDT)
MIN_INVESTMENT=10.0

# Maximum daily trading volume (in USDT)
MAX_DAILY_TRADES=1000000.0

# Supported trading pairs
SUPPORTED_PAIRS=BTC/USDT,ETH/USDT,BNB/USDT,DOGE/USDT,ADA/USDT,XRP/USDT
```

### Risk Management

```env
# Maximum loss percentage per trade (0.0 = no limit)
MAX_LOSS_PERCENT=1.0

# Daily profit target percentage (inf = no limit)
DAILY_PROFIT_TARGET_PERCENT=inf
```

### Notifications (Optional)

```env
# Telegram notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

## Running the Bot

### Simple Mode

Start the basic trading bot:
```bash
python main.py
```

### Advanced Mode

Start the enhanced trading bot with all features:
```bash
python advanced_main.py
```

### Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully. The bot will:
- Cancel any pending orders
- Save current state
- Close exchange connections

## Trading Strategies

The bot uses multiple complementary strategies to make trading decisions:

### 1. RSI Strategy
- Uses Relative Strength Index (14-period)
- Buys when RSI < 30 (oversold)
- Sells when RSI > 70 (overbought)

### 2. MACD Strategy
- Uses Moving Average Convergence Divergence
- Buys on bullish crossovers
- Sells on bearish crossovers

### 3. Bollinger Bands Strategy
- Uses 20-period moving average with 2 standard deviations
- Buys when price touches lower band
- Sells when price touches upper band

### 4. Moving Average Strategy
- Uses 20-period and 50-period moving averages
- Buys on golden cross (20MA crosses above 50MA)
- Sells on death cross (20MA crosses below 50MA)

### 5. Volume Strategy
- Analyzes trading volume patterns
- Buys on high volume with price increases
- Sells on high volume with price decreases

### 6. Candlestick Patterns Strategy
- Recognizes common candlestick patterns
- Includes Doji, Hammer, Shooting Star, and more
- Provides additional confirmation signals

### Signal Aggregation

The bot combines all strategy signals:
- Requires majority agreement for action
- Uses confidence scoring (0-100%)
- Default threshold: 60% for buys, 50% for sells

## Risk Management

The bot implements comprehensive risk management:

### Position Sizing

- **Fixed Fractional**: Maximum 2% of portfolio per trade
- **Volatility Adjusted**: Smaller positions for volatile assets
- **Kelly Criterion**: Mathematically optimal sizing
- **Stop-Loss Based**: Position size based on risk tolerance

### Portfolio Protection

- **Maximum Exposure**: 10% total portfolio risk limit
- **Correlation Management**: Avoids highly correlated positions
- **Concentration Limits**: Maximum 25% in single asset
- **Drawdown Protection**: 15% maximum portfolio drawdown

### Dynamic Risk Adjustment

- Adjusts position sizes based on market volatility
- Reduces trading when portfolio is under stress
- Implements cooldown periods between trades

## Stop-Loss System

The bot automatically calculates and manages stop-loss levels:

### Calculation Methods

1. **ATR Method** (Default):
   - Uses Average True Range (14-period)
   - Sets stop-loss at 2x ATR distance from entry
   - Adapts to current market volatility

2. **Percentage Method**:
   - Fixed percentage stop (typically 3%)
   - Simple and consistent across all assets

3. **Volatility Method**:
   - Based on standard deviation
   - Adjusts to asset-specific volatility

4. **Support/Resistance Method**:
   - Places stop-loss below support (for longs)
   - Places stop-loss above resistance (for shorts)

### Take-Profit System

- Uses risk/reward ratio (default 1:2)
- If stop-loss is 2% risk, take-profit is 4% target
- Automatically calculated based on stop-loss distance

### Monitoring

- The bot continuously monitors open positions
- Automatically closes positions when stop-loss is hit
- Sends notifications for all trade events

## Error Handling

The bot provides user-friendly error messages:

### Common Errors

1. **Insufficient Funds**:
   - Message: "Insufficient funds for BUY/SELL order. This is normal if you don't have enough balance."
   - Solution: Add funds to your exchange account

2. **Order Too Small**:
   - Message: "BUY/SELL order too small (min 10 USDT). This is normal for small balances."
   - Solution: Increase your account balance

3. **Exchange Connection Issues**:
   - Message: "Network issue. The bot will retry automatically."
   - Solution: No action needed - bot retries automatically

4. **API Configuration Errors**:
   - Message: "Check API keys and trading pair in your configuration."
   - Solution: Verify your `.env` file settings

### Error Classification

- **INFO**: Normal conditions (insufficient funds, small orders)
- **WARNING**: Temporary issues (network problems, rate limits)
- **ERROR**: Configuration or system problems requiring attention

## Monitoring and Logging

### Console Output

The bot provides real-time color-coded feedback:
- **Green**: Buy signals and successful trades
- **Red**: Sell signals and errors
- **Blue**: Hold signals and general information
- **Yellow**: Warnings and cautions

### Log Files

- `enhanced_trading_bot.log`: Detailed activity log
- Log rotation to prevent excessive file sizes
- Structured logging for easy analysis

### Performance Tracking

- Trade history and performance metrics
- Profit/loss calculations
- Win/loss ratios
- Risk-adjusted returns

## Troubleshooting

### Common Issues and Solutions

#### 1. "Trading limits exceeded" Error
**Cause**: Daily trading limit reached
**Solution**: 
- Increase `MAX_DAILY_TRADES` in `.env`
- Wait for daily reset (midnight UTC)
- Check your trading history

#### 2. No Trading Activity
**Check**:
- Verify API keys in `.env`
- Confirm supported trading pairs
- Check exchange account balances
- Review log files for errors

#### 3. Exchange Connection Failures
**Check**:
- Internet connectivity
- Exchange API status
- API key permissions
- Firewall settings

#### 4. Invalid Order Amounts
**Cause**: Order size below exchange minimum
**Solution**:
- Increase account balance
- Bot automatically adjusts to minimum sizes

### Testing Your Setup

1. **Component Test**:
   ```bash
   python test_components.py
   ```

2. **Exchange Connection Test**:
   ```bash
   python test_bitget_connection.py
   ```

3. **Full Integration Test**:
   ```bash
   python test_complete_integration.py
   ```

### Safety Recommendations

1. **Start with Sandbox Mode**:
   - Set `SANDBOX_MODE=true` in `.env`
   - Test with small amounts
   - Verify all functionality

2. **Monitor Initial Trades**:
   - Watch first few trades closely
   - Verify stop-loss placement
   - Check position sizing

3. **Regular Maintenance**:
   - Update dependencies regularly
   - Review log files daily
   - Monitor exchange account

4. **Risk Management**:
   - Never risk more than you can afford to lose
   - Start with small positions
   - Diversify your portfolio manually

## Support

For issues not covered in this guide:
1. Check the console output and log files
2. Review existing documentation in the `docs/` folder
3. Run the test scripts to diagnose problems
4. Contact support with detailed error information

Remember: Cryptocurrency trading involves significant risk. Only trade with funds you can afford to lose.