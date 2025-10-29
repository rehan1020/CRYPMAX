# Crympax Configuration Reference

This document provides detailed information about all configuration options available for the Crympax personal cryptocurrency trading bot.

## Environment Variables

All configuration is managed through environment variables in the `.env` file. This approach keeps sensitive information secure and makes configuration easy to manage.

### Bot Basic Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `your-secret-key-here-change-this` | Secret key for API security |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |

### Trading Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_INVESTMENT` | `1.0` | Minimum investment per trade (in base currency) |
| `MAX_DAILY_TRADES` | `1000000.0` | Maximum daily trading volume (in USDT) |
| `COOLDOWN_MINUTES` | `1` | Minimum time between trades (in minutes) |
| `REFRESH_INTERVAL_SECONDS` | `60` | Market analysis refresh interval (in seconds) |
| `TRADING_TIMEFRAME` | `5m` | Primary timeframe for trading decisions |
| `ANALYSIS_TIMEFRAMES` | `15m,30m,1h` | Timeframes for market analysis |
| `SUPPORTED_PAIRS` | `BTC/USDT,ETH/USDT,BNB/USDT,DOGE/USDT,ADA/USDT,XRP/USDT` | Trading pairs to monitor and trade |

### Risk Management

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_LOSS_PERCENT` | `0.0` | Maximum loss percentage per trade (0 = no limit) |
| `DAILY_PROFIT_TARGET_PERCENT` | `inf` | Daily profit target percentage (inf = no limit) |
| `MAX_DAILY_TRADES` | `1000000.0` | Maximum daily trading volume in USDT |

### Exchange Settings

| Variable | Required | Description |
|----------|----------|-------------|
| `BITGET_API_KEY` | Yes | Bitget API key |
| `BITGET_SECRET` | Yes | Bitget API secret |
| `BITGET_PASSPHRASE` | Yes | Bitget API passphrase |
| `SANDBOX_MODE` | No | Set to `true` for testnet trading |

### Notification Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | None | Telegram bot token for notifications |
| `TELEGRAM_CHAT_ID` | None | Telegram chat ID for notifications |
| `EMAIL_SMTP_SERVER` | None | SMTP server for email notifications |
| `EMAIL_SMTP_PORT` | `587` | SMTP server port |
| `EMAIL_USERNAME` | None | Email username |
| `EMAIL_PASSWORD` | None | Email password (app password recommended) |

### Database & Caching

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///crypto_bot.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for caching |

### Machine Learning

| Variable | Default | Description |
|----------|---------|-------------|
| `ML_MODEL_PATH` | `models/enhanced_trading_model.pkl` | Path to trained ML model |
| `USE_ML_PREDICTION` | `true` | Enable/disable ML predictions |

### Test Mode

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_MODE` | `true` | Enable test mode with user input |

## Configuration Examples

### Basic Live Trading Setup

```env
# Essential exchange credentials
BITGET_API_KEY=your_actual_api_key_here
BITGET_SECRET=your_actual_secret_here
BITGET_PASSPHRASE=your_actual_passphrase_here

# Live trading mode
SANDBOX_MODE=false

# Basic trading parameters
MIN_INVESTMENT=10.0
MAX_DAILY_TRADES=10000.0
SUPPORTED_PAIRS=BTC/USDT,ETH/USDT
```

### Sandbox Testing Setup

```env
# Testnet credentials (get from Bitget testnet)
BITGET_API_KEY=testnet_api_key
BITGET_SECRET=testnet_secret
BITGET_PASSPHRASE=testnet_passphrase

# Test mode
SANDBOX_MODE=true
TEST_MODE=true

# Conservative settings for testing
MIN_INVESTMENT=1.0
MAX_DAILY_TRADES=1000.0
```

### Advanced Configuration with Notifications

```env
# Exchange settings
BITGET_API_KEY=your_api_key
BITGET_SECRET=your_secret
BITGET_PASSPHRASE=your_passphrase
SANDBOX_MODE=false

# Trading parameters
MIN_INVESTMENT=50.0
MAX_DAILY_TRADES=50000.0
SUPPORTED_PAIRS=BTC/USDT,ETH/USDT,BNB/USDT

# Risk management
MAX_LOSS_PERCENT=2.0
DAILY_PROFIT_TARGET_PERCENT=5.0

# Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# ML settings
USE_ML_PREDICTION=true
```

## Security Best Practices

### API Key Security

1. **Use Dedicated Keys**:
   - Create separate API keys for the bot
   - Enable only required permissions (read and trade)
   - Disable withdrawal permissions

2. **IP Restrictions**:
   - Restrict API keys to specific IP addresses
   - Update restrictions when changing networks

3. **Regular Rotation**:
   - Change API keys periodically
   - Immediately revoke compromised keys

### Environment File Security

1. **Never Commit**:
   - Add `.env` to `.gitignore`
   - Never share your `.env` file

2. **File Permissions**:
   - Restrict file access to bot user only
   - Use appropriate file permissions (600 on Unix systems)

3. **Backup**:
   - Keep secure backups of your configuration
   - Store backups in encrypted storage

## Configuration Validation

The bot performs automatic validation of configuration settings:

### Required Validations

- API keys must be present for enabled exchanges
- Trading pairs must be supported by the exchange
- Numeric values must be within reasonable ranges
- Timeframes must be supported by data sources

### Warning Conditions

- Low minimum investment values
- Very high daily trading limits
- Unsupported trading pairs
- Missing optional configuration

## Environment-Specific Configuration

### Development Environment

```env
SANDBOX_MODE=true
TEST_MODE=true
MIN_INVESTMENT=1.0
MAX_DAILY_TRADES=1000.0
```

### Production Environment

```env
SANDBOX_MODE=false
TEST_MODE=false
MIN_INVESTMENT=50.0
MAX_DAILY_TRADES=100000.0
```

### Testing Environment

```env
SANDBOX_MODE=true
TEST_MODE=false
MIN_INVESTMENT=10.0
MAX_DAILY_TRADES=5000.0
```

## Troubleshooting Configuration Issues

### Common Configuration Errors

1. **Missing API Keys**:
   ```
   ERROR: Bitget credentials not provided
   ```
   **Solution**: Verify all three Bitget credentials are set

2. **Invalid Trading Pairs**:
   ```
   ERROR: Unsupported trading pair
   ```
   **Solution**: Check exchange for supported pairs

3. **Numeric Value Errors**:
   ```
   WARNING: Invalid numeric value, using default
   ```
   **Solution**: Check syntax and range of numeric values

### Configuration Loading Order

1. **Default Values**: Hardcoded defaults in `config.py`
2. **Environment Variables**: Values from `.env` file
3. **Runtime Overrides**: Values passed during bot initialization

### Testing Configuration

Use the configuration test script:
```bash
python test_config.py
```

This script validates:
- All required settings are present
- Values are within acceptable ranges
- Exchange connectivity with provided credentials