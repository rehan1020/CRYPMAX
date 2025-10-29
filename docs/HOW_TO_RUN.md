# How to Run the Crympax Trading Bot

This guide explains how to run the Crympax trading bot using `python advanced_main.py`.

## Running the Bot

### Basic Execution
To run the bot, use the following command from the Personal bot directory:

```bash
python advanced_main.py
```

### Step-by-Step Instructions

1. **Open Terminal/Command Prompt**
   - Windows: Press `Win + R`, type `cmd`, press Enter
   - macOS: Open Terminal from Applications
   - Linux: Open your preferred terminal

2. **Navigate to the Bot Directory**
   ```bash
   cd "c:\Users\30reh\Downloads\backendtraderz( paper)\Personal bot"
   ```

3. **Run the Bot**
   ```bash
   python advanced_main.py
   ```

## What Happens When You Run the Bot

When you execute `python advanced_main.py`, the bot will:

1. **Load Configuration**
   - Read settings from the [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file
   - Validate API credentials
   - Initialize trading parameters

2. **Connect to Exchange**
   - Establish connection to Bitget exchange
   - Test connectivity and permissions
   - Enable sandbox mode if configured

3. **Initialize Components**
   - Load the ML trading model
   - Set up risk management systems
   - Initialize strategy managers
   - Configure notifications

4. **Start Trading Loop**
   - Begin monitoring selected trading pairs
   - Analyze market conditions
   - Make trading decisions
   - Execute trades (in sandbox or live mode)

## Bot Operation Modes

### Sandbox Mode (Testing)
- Trades are executed on Bitget testnet
- No real funds are used
- Perfect for testing and practice

### Live Mode (Real Trading)
- Trades are executed on Bitget live exchange
- Real funds are used
- Requires live API credentials

## Stopping the Bot

To stop the bot gracefully:
- Press `Ctrl + C` in the terminal
- The bot will complete current operations and shut down cleanly

## Monitoring the Bot

While the bot is running, you can monitor:

1. **Console Output**
   - Real-time trading decisions
   - Connection status
   - Error messages

2. **Log File**
   - Detailed activity log in `enhanced_trading_bot.log`
   - Historical trading data
   - Debug information

3. **Exchange Interface**
   - View orders and positions on Bitget website
   - Monitor account balance changes

## Configuration Before Running

Before running the bot, ensure your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file is properly configured:

### For Sandbox Testing
```env
SANDBOX_MODE=true
BITGET_API_KEY=your_testnet_api_key
BITGET_SECRET=your_testnet_secret
BITGET_PASSPHRASE=your_testnet_passphrase
```

### For Live Trading
```env
SANDBOX_MODE=false
BITGET_API_KEY=your_live_api_key
BITGET_SECRET=your_live_secret
BITGET_PASSPHRASE=your_live_passphrase
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Ensure you're in the correct directory
   - Install required packages: `pip install -r requirements.txt`

2. **API credential errors**
   - Verify your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file has correct credentials
   - Check that API keys have proper permissions

3. **Connection issues**
   - Check internet connectivity
   - Verify Bitget API is accessible
   - Confirm sandbox mode settings match your credentials

### Getting Help
If you encounter issues:
1. Check the console output for error messages
2. Review the log file (`enhanced_trading_bot.log`)
3. Verify your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) configuration
4. Ensure all dependencies are installed

## Best Practices

1. **Start with Sandbox Mode**
   - Test thoroughly before using real funds
   - Verify trading logic and risk management

2. **Monitor Initial Trades**
   - Watch the first few trades closely
   - Ensure position sizing is appropriate

3. **Regular Monitoring**
   - Check the bot periodically during operation
   - Review logs for any anomalies

4. **Secure Your Configuration**
   - Keep your [.env](file:///c%3A/Users/30reh/Downloads/CryptoPulse-T4/Personal%20bot/.env) file secure
   - Never share API credentials
   - Use strong passwords and passphrases