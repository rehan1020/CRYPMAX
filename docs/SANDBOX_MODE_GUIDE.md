# Sandbox Mode Guide for Crympax Trading Bot

This guide explains how to use the Crympax trading bot in sandbox mode for safe testing.

## What is Sandbox Mode?

Sandbox mode allows you to:
- Test the bot with real market data
- Execute trades without using real funds
- Verify trading logic and risk management
- Practice without financial risk

In sandbox mode, the bot connects to Bitget's testnet where all trades use fake funds.

## Current Configuration

Your bot is currently configured for sandbox mode:

```
SANDBOX_MODE=true
```

This means all trades will be executed on Bitget's testnet, not the live exchange.

## How to Use Sandbox Mode

### 1. Keep Current Settings (Sandbox Mode)
Your current [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file is already set up for sandbox mode:

```env
SANDBOX_MODE=true
BITGET_API_KEY=your_testnet_api_key
BITGET_SECRET=your_testnet_secret
BITGET_PASSPHRASE=your_testnet_passphrase
```

### 2. Get Bitget Testnet Credentials
To use sandbox mode properly:

1. Go to [Bitget Testnet](https://testnet.bitget.com/)
2. Create a testnet account
3. Generate API credentials in the testnet environment
4. Update your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file with testnet credentials

### 3. Run the Bot
Simply run the bot as normal:

```bash
python advanced_main.py
```

The bot will:
- Connect to Bitget testnet
- Make trading decisions using real market data
- Execute trades with fake funds
- Apply all risk management rules

## Switching to Live Trading

When you're ready to trade with real funds:

1. Set `SANDBOX_MODE=false` in your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file
2. Update with your live Bitget API credentials
3. Run the bot normally

```env
SANDBOX_MODE=false
BITGET_API_KEY=your_live_api_key
BITGET_SECRET=your_live_secret
BITGET_PASSPHRASE=your_live_passphrase
```

## Safety Features in Sandbox Mode

Even in sandbox mode, the bot includes safety features:

- **Risk Management**: Position sizing and stop-losses still apply
- **Daily Limits**: Trading limits are enforced
- **Cooldown Periods**: Prevents excessive trading
- **Logging**: All trades are logged for review

## Monitoring Sandbox Trades

You can monitor your sandbox trades by:

1. Checking the console output
2. Reviewing the log file (`enhanced_trading_bot.log`)
3. Logging into the Bitget testnet website to see your fake portfolio

## Best Practices

1. **Start with small amounts**: Even in sandbox mode, test with small position sizes
2. **Monitor the logs**: Review trading decisions and executions
3. **Test different market conditions**: Run during both volatile and calm periods
4. **Verify risk management**: Ensure stop-losses and position sizing work as expected
5. **Gradual transition**: When switching to live trading, start with very small amounts

## Troubleshooting

### Connection Issues
If the bot can't connect to Bitget testnet:
- Verify your testnet API credentials
- Check your internet connection
- Ensure Bitget testnet is operational

### No Trading Activity
If the bot isn't making trades:
- Check that `MAX_DAILY_TRADES` is not set to 0
- Verify your risk parameters aren't too restrictive
- Ensure the ML model is making confident predictions

### Error Messages
Common sandbox mode errors and solutions:
- "Invalid API Key": Double-check your testnet credentials
- "Permission denied": Ensure your API key has trading permissions
- "Market not found": Some pairs may not be available on testnet

## Next Steps

1. Run the bot in sandbox mode for a few days
2. Review the trading decisions and executions
3. Adjust configuration parameters as needed
4. When comfortable, switch to live trading with small amounts