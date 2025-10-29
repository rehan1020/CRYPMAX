# Crympax Personal Trading Bot

A clean, structured single-user terminal-only cryptocurrency trading bot.

## Features

- Terminal-only output (no web interface)
- Live-updating dashboard with color coding
- Environment-based configuration
- No user input required during runtime (except for initial investment amount)
- Fully automated trading
- Bitget Exchange Compatible only
## Project Structure

```
Crympax-Personal/
├── analysis/                    # Market analysis and machine learning modules
├── connectors/                  # Exchange-specific connector implementations
├── core/                        # Core trading logic and infrastructure
├── docs/                        # Documentation files
├── strategies/                  # Trading strategy implementations
├── tests/                       # Test files
├── main.py                      # Main entry point for the bot
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
└── README_SINGLE_USER.md        # Setup and usage instructions
```

For a detailed explanation of all files in each directory, see [CODEBASE_FILE_STRUCTURE.md](CODEBASE_FILE_STRUCTURE.md).

## Setup
Note: Download the whole project as a zip, then extract the all folders from the zip to start.

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your exchange API keys:
   ```env
   BITGET_API_KEY=your_bitget_api_key_here
   BITGET_SECRET=your_bitget_secret_here
   BITGET_PASSPHRASE=your_bitget_passphrase_here
   ```

## Usage

Run the personal trading bot:
```bash
python advanced_main.py
```

On first run, you'll be prompted to enter your investment amount in USDT (if implemented in your version).

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- [QUICK_START.md](QUICK_START.md) - Get started quickly
- [USER_GUIDE.md](USER_GUIDE.md) - Complete user manual
- [CONFIGURATION_REFERENCE.md](CONFIGURATION_REFERENCE.md) - Detailed configuration options
- [TRADING_STRATEGIES.md](TRADING_STRATEGIES.md) - Trading strategy explanations
- [RISK_MANAGEMENT.md](RISK_MANAGEMENT.md) - Risk management system
- [MONITORING_AND_LOGGING.md](MONITORING_AND_LOGGING.md) - Monitoring and logging guide
- [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md) - Problem-solving guide
- [TESTING_FRAMEWORK.md](TESTING_FRAMEWORK.md) - Testing framework overview
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Advanced features explanation
- [TRADING_MODES.md](TRADING_MODES.md) - Switching between sandbox and live trading modes

## Requirements

- Python 3.7+
- ccxt
- colorama
- python-dotenv
- pandas
- numpy

## Disclaimer
This is a prototype, it will be improved in feature and has been made for testing purposes only, CRYPMAX team is not responsible for any loss that occurs during the usage of this bot or beyond.
