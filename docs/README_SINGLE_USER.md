# Crympax Personal Trading Bot - Single User Setup

This guide explains how to set up and run the Crympax crypto trading bot for personal use on your local system.

For a detailed explanation of all files in the codebase, see [docs/CODEBASE_FILE_STRUCTURE.md](docs/CODEBASE_FILE_STRUCTURE.md).

## Prerequisites

- Python 3.8+
- API keys from supported exchanges (Bitget)

## Installation

1. Clone or download the bot files to your local machine.

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` file and fill in your configuration:
   - Set your exchange API keys (at least one exchange)
   - Adjust trading parameters as needed

## Configuration

### Required Settings

- **Exchange Credentials**: Set API keys for at least one exchange:
  ```
  BITGET_API_KEY=your_bitget_api_key
  BITGET_SECRET=your_bitget_secret
  BITGET_PASSPHRASE=your_bitget_passphrase
  ```

### Optional Settings

- **Trading Pairs**:
  ```
  SUPPORTED_PAIRS=BTC/USDT,ETH/USDT
  ```

## Running the Bot

Start the simple bot:
```bash
python main.py
```

Or start the advanced bot with enhanced strategies:
```bash
python advanced_main.py
```

The bot will:
1. Load configuration from `.env`
2. Initialize exchange connections
3. Start the trading loop with analysis and automated trades

For details on the advanced bot features, see [docs/ADVANCED_BOT.md](docs/ADVANCED_BOT.md).

## Stopping the Bot

Press `Ctrl+C` to stop the bot gracefully.

## Features

### Simple Bot
- **Single Exchange Support**: Trade on Bitget
- **Simple Trading Strategy**: Moving average crossover strategy
- **Real-time Trading**: 5-minute timeframe analysis
- **No Database Required**: Lightweight implementation

### Advanced Bot
- **Multi-Indicator Strategies**: RSI, MACD, Bollinger Bands, Volume
- **Advanced Risk Management**: Position sizing, stop-loss calculation
- **Multi-Timeframe Analysis**: 1m-1h timeframe data
- **Confidence Scoring**: Weighted signal confidence
- **Same Lightweight Architecture**: No database dependencies

## Safety Notes

- Start with small amounts and test in a safe environment
- Monitor the bot's performance regularly
- Keep API keys secure and never share them
- Use exchange features like 2FA and IP restrictions

## Troubleshooting

- **No exchanges initialized**: Check API keys in `.env`
- **Import errors**: Ensure all dependencies are installed

For issues, check the console output and log files.