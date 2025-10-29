# Crympax Trading Modes

This document explains how to switch between sandbox (testnet) mode and live trading mode for the Crympax trading bot.

## Overview

The Crympax trading bot supports two trading modes:

1. **Sandbox Mode (Testnet)**: Uses fake funds for testing and practice
2. **Live Trading Mode**: Uses real funds for actual trading

## Configuration

The trading mode is controlled by two environment variables in the [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file:

- `SANDBOX_MODE`: Controls whether to use testnet or live exchange
- `TEST_MODE`: Controls whether to run in interactive test mode or fully automated mode

## Sandbox Mode (Testing)

For testing with fake funds on Bitget's testnet:

```env
SANDBOX_MODE=true
TEST_MODE=true
```

### Requirements for Sandbox Mode

1. Bitget testnet account (sign up at https://testnet.bitget.com/)
2. Testnet API credentials (generated in the testnet environment)
3. Test funds (available through testnet faucet)

### Benefits of Sandbox Mode

- Practice trading without risking real funds
- Test new strategies and configurations
- Verify bot functionality
- Debug issues safely

## Live Trading Mode

For trading with real funds on Bitget's live exchange:

```env
SANDBOX_MODE=false
TEST_MODE=false
```

### Requirements for Live Trading Mode

1. Bitget live account (sign up at https://www.bitget.com/)
2. Live API credentials with proper permissions (read and trade)
3. Real funds in your account

### Important Safety Considerations

- Start with small position sizes
- Monitor the bot closely during initial live trading
- Ensure adequate funds for trading
- Verify all configuration settings before going live

## Switching Between Modes

### To Switch to Live Trading Mode

1. Open the [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file in the `Personal bot` directory
2. Set `SANDBOX_MODE=false`
3. Set `TEST_MODE=false`
4. Ensure your live API credentials are correctly set:
   ```env
   BITGET_API_KEY=your_live_api_key
   BITGET_SECRET=your_live_secret
   BITGET_PASSPHRASE=your_live_passphrase
   ```
5. Save the file

### To Switch Back to Sandbox Mode

1. Open the [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file in the `Personal bot` directory
2. Set `SANDBOX_MODE=true`
3. Set `TEST_MODE=true`
4. Ensure your testnet API credentials are correctly set:
   ```env
   BITGET_API_KEY=your_testnet_api_key
   BITGET_SECRET=your_testnet_secret
   BITGET_PASSPHRASE=your_testnet_passphrase
   ```
5. Save the file

## Verification

You can verify your current configuration by running the test script in the tests directory:

```bash
cd tests
python test_live_trading.py
```

This script will check:
- Whether sandbox mode is disabled
- Whether test mode is disabled
- Whether all required API credentials are present

## Best Practices

### Before Going Live

1. Test thoroughly in sandbox mode
2. Start with small position sizes
3. Monitor the bot closely during the first few trades
4. Verify all risk management settings
5. Ensure adequate funds in your account

### Security

1. Never share your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file
2. Use strong, unique passwords and passphrases
3. Enable two-factor authentication on your exchange account
4. Regularly rotate your API keys
5. Restrict API key permissions to only what is necessary (read and trade)

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify API credentials are correct and have proper permissions
2. **Insufficient Funds**: Ensure adequate funds in your account for trading
3. **Network Issues**: Check internet connectivity and firewall settings
4. **Configuration Errors**: Double-check [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file settings

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Review the log file (`enhanced_trading_bot.log`)
3. Verify your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) configuration
4. Ensure all dependencies are installed

Remember: Trading bots involve financial risk. Only trade with funds you can afford to lose.