# Crympax Personal Trading Bot - Bitget Only Version

This is a simplified version of the Crympax trading bot that focuses exclusively on Bitget exchange integration with enhanced machine learning capabilities and risk management. It's designed for single-user deployment with a streamlined feature set.

## Key Features

1. **Single Exchange Focus**: Only Bitget exchange support for simplified configuration
2. **Enhanced ML Engine**: Advanced machine learning models for market prediction
3. **Risk Management**: Comprehensive risk controls and position sizing
4. **Multi-Timeframe Analysis**: Analysis across multiple timeframes for better decisions
5. **Strategy Management**: Coordination of multiple trading strategies
6. **Notification System**: Telegram and email notifications
7. **Yahoo Finance Integration**: Market data from Yahoo Finance for broader context

## Setup Instructions

1. **Install Dependencies**: Run `pip install -r requirements.txt`
2. **Configure Environment**: Set up your `.env` file with Bitget API credentials
3. **Test Connection**: Try the test script: `cd tests && python test_bitget_bot.py`
4. **Run the Bot**: Execute `python advanced_main.py` to start trading

## Configuration

The bot is configured through environment variables in the `.env` file:

- `BITGET_API_KEY`: Your Bitget API key
- `BITGET_SECRET`: Your Bitget API secret
- `BITGET_PASSPHRASE`: Your Bitget API passphrase
- `TELEGRAM_BOT_TOKEN`: (Optional) Telegram bot token for notifications
- `TELEGRAM_CHAT_ID`: (Optional) Telegram chat ID for notifications
- Other configuration options are available in `core/config.py`

## Running the Bot

To run the bot:

```bash
python advanced_main.py
```

The bot will initialize with your Bitget credentials, connect to the exchange, and start monitoring the configured trading pairs.

## Testing

Several test scripts are available in the `tests/` directory:

- `test_bitget_bot.py`: Test Bitget connection and basic functionality
- `test_complete_integration.py`: Full integration test
- `test_yahoo_integration.py`: Test Yahoo Finance integration

Run any test with:
```bash
cd tests
python test_bitget_bot.py
```

## Risk Management

The bot includes comprehensive risk management features:

- Position sizing based on account balance and risk parameters
- Maximum loss limits per trade and per day
- Daily profit targets
- Volatility-based risk adjustments
- Correlation risk analysis

## Machine Learning

The bot uses an enhanced machine learning engine for market prediction:

- Multi-feature analysis including technical indicators and market sentiment
- Ensemble models for improved accuracy
- Continuous learning and model updates
- Risk-adjusted predictions

## Support

For issues or questions, please check the documentation or open an issue on the project repository.