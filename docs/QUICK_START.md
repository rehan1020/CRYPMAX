# Crympax Quick Start Guide

This guide provides step-by-step instructions to get your Crympax personal cryptocurrency trading bot up and running quickly.

## Prerequisites

Before starting, ensure you have:

- **Python 3.8 or higher** installed on your system
- **Bitget exchange account** with API keys
- **Git** (optional, for cloning the repository)
- **Basic understanding** of cryptocurrency trading

## Step 1: Get the Bot

### Option A: Download ZIP File
1. Download the bot package
2. Extract to a folder on your computer

### Option B: Clone Repository
```bash
git clone <repository-url>
cd backendtraderz
```

## Step 2: Install Dependencies

Open a terminal/command prompt in the bot directory and run:

```bash
pip install -r requirements.txt
```

This installs all required Python packages including:
- ccxt (exchange connectivity)
- pandas (data analysis)
- numpy (numerical computing)
- scikit-learn (machine learning)
- colorama (colored console output)

## Step 3: Configure the Bot

### Create Environment File
Copy the example configuration file:
```bash
cp .env.example .env
```

### Edit Configuration
Open `.env` in a text editor and update these essential settings:

```env
# Exchange API Credentials (REQUIRED)
BITGET_API_KEY=your_actual_api_key_here
BITGET_SECRET=your_actual_secret_here
BITGET_PASSPHRASE=your_actual_passphrase_here

# Sandbox Mode (recommended for first run)
SANDBOX_MODE=true

# Basic Trading Settings
MIN_INVESTMENT=10.0
MAX_DAILY_TRADES=10000.0
```

### API Key Setup
1. Log into your Bitget account
2. Go to "API Management" in account settings
3. Create a new API key with:
   - **Permissions**: Read and Trade (no withdrawal)
   - **IP Restriction**: Add your IP address (optional but recommended)
4. Copy the API Key, Secret, and Passphrase to your `.env` file

## Step 4: Test Your Setup

### Run Component Tests
```bash
python test_components.py
```
Expected output: All components should load successfully

### Test Exchange Connection
```bash
python test_bitget_connection.py
```
Expected output: Connection to Bitget should succeed

## Step 5: Start Trading

### Sandbox Mode (Recommended First)
With `SANDBOX_MODE=true` in your `.env`:
```bash
python advanced_main.py
```

### Live Trading
To trade with real funds, set `SANDBOX_MODE=false` and restart the bot.

## Step 6: Monitor the Bot

### Console Output
Watch the color-coded console:
- **Green**: Buy signals and successful trades
- **Red**: Sell signals and errors
- **Blue**: Hold signals and general information
- **Yellow**: Warnings and cautions

### Log Files
Check `enhanced_trading_bot.log` for detailed activity records.

## Common First-Time Issues

### 1. "Module not found" Errors
**Solution**: Re-run `pip install -r requirements.txt`

### 2. Authentication Errors
**Solution**: 
- Verify API keys in `.env` file
- Ensure keys have proper permissions
- Check for extra spaces in credentials

### 3. Insufficient Funds
**Solution**: 
- Add funds to your exchange account
- Start with small amounts for testing

### 4. Network Issues
**Solution**:
- Check internet connection
- Verify firewall settings
- Try connecting to exchange website manually

## Next Steps

### 1. Learn the Strategies
Read `TRADING_STRATEGIES.md` to understand how the bot makes trading decisions.

### 2. Configure Risk Management
Review `RISK_MANAGEMENT.md` to adjust risk settings to your preference.

### 3. Set Up Notifications
Configure Telegram or email notifications in `.env` for trade alerts.

### 4. Monitor Performance
Use the logging system to track your bot's performance over time.

## Safety Recommendations

### Start Small
- Begin with small position sizes
- Use sandbox mode for initial testing
- Monitor the first few trades closely

### Secure Your Setup
- Never share your `.env` file
- Use strong, unique passwords
- Enable two-factor authentication on your exchange

### Regular Monitoring
- Check the bot daily
- Review log files regularly
- Monitor your exchange account

## Getting Help

### Documentation
- `USER_GUIDE.md`: Complete user manual
- `TROUBLESHOOTING_GUIDE.md`: Problem-solving guide
- `CONFIGURATION_REFERENCE.md`: Detailed configuration options

### Testing Your Installation
```bash
python test_complete_integration.py
```
This runs a comprehensive test of all bot components.

### Support
If you encounter issues:
1. Check console output and log files
2. Review documentation
3. Run specific test scripts
4. Contact support with detailed error information

## Example Configuration

Here's a sample `.env` file for getting started:

```env
# ===========================================
# ESSENTIAL SETTINGS - UPDATE THESE
# ===========================================
BITGET_API_KEY=your_actual_api_key_here
BITGET_SECRET=your_actual_secret_here
BITGET_PASSPHRASE=your_actual_passphrase_here

# ===========================================
# RECOMMENDED FOR FIRST RUN
# ===========================================
SANDBOX_MODE=true
TEST_MODE=true
MIN_INVESTMENT=10.0
MAX_DAILY_TRADES=1000.0
SUPPORTED_PAIRS=BTC/USDT,ETH/USDT

# ===========================================
# OPTIONAL NOTIFICATIONS
# ===========================================
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Remember: Cryptocurrency trading involves significant risk. Only trade with funds you can afford to lose. Start with small amounts and test thoroughly before increasing your investment.