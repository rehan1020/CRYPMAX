# Crympax Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Crympax personal cryptocurrency trading bot.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Problems](#configuration-problems)
3. [Exchange Connection Errors](#exchange-connection-errors)
4. [Trading Execution Issues](#trading-execution-issues)
5. [Market Data Problems](#market-data-problems)
6. [Risk Management Errors](#risk-management-errors)
7. [Performance and Monitoring](#performance-and-monitoring)
8. [Advanced Debugging](#advanced-debugging)

## Installation Issues

### Missing Dependencies

**Symptom**: Import errors or "module not found" messages
**Solution**:
```bash
pip install -r requirements.txt
```

If you still encounter issues:
```bash
pip install --upgrade -r requirements.txt
```

### Python Version Compatibility

**Symptom**: Syntax errors or runtime errors
**Solution**: 
- Ensure you're using Python 3.8 or higher
- Check version with: `python --version`

### Permission Errors

**Symptom**: "Permission denied" when running scripts
**Solution**:
- On Windows: Run Command Prompt or PowerShell as Administrator
- On macOS/Linux: Use `sudo` or fix file permissions

## Configuration Problems

### Missing Environment Variables

**Symptom**: 
```
ERROR: Bitget credentials not provided
```

**Solution**:
1. Verify `.env` file exists in the project root
2. Check that all required variables are set:
   ```env
   BITGET_API_KEY=your_key
   BITGET_SECRET=your_secret
   BITGET_PASSPHRASE=your_passphrase
   ```

### Invalid Configuration Values

**Symptom**:
```
WARNING: Invalid numeric value, using default
```

**Solution**:
1. Check syntax in `.env` file
2. Ensure numeric values don't contain quotes
3. Verify values are within reasonable ranges

### Configuration Loading Issues

**Diagnostic Command**:
```bash
python test_components.py
```

This test verifies:
- Configuration loads correctly
- All required settings are present
- Values are valid

## Exchange Connection Errors

### Authentication Failures

**Symptom**:
```
ERROR: Failed to initialize Bitget: Authentication error
```

**Common Causes and Solutions**:
1. **Incorrect API Keys**:
   - Verify keys in Bitget account settings
   - Ensure no extra spaces in `.env` file
   - Check that keys have proper permissions

2. **Wrong Passphrase**:
   - Passphrase is case-sensitive
   - Must match exactly what you set in Bitget

3. **IP Restrictions**:
   - Check if API key has IP restrictions
   - Add your current IP to allowed list

### Network Connectivity Issues

**Symptom**:
```
ERROR: Network error - Connection timeout
```

**Solutions**:
1. Check internet connection
2. Verify firewall settings
3. Try connecting to exchange website manually
4. Use a different network if possible

### Sandbox Mode Issues

**Symptom**:
```
ERROR: Exchange not available in sandbox mode
```

**Solution**:
1. Ensure you're using testnet API keys
2. Verify `SANDBOX_MODE=true` in `.env`
3. Check Bitget testnet status

### Exchange-Specific Configuration

**Required Bitget Settings**:
- API key with "Read" and "Trade" permissions
- Correct passphrase
- Position mode set to "One-Way" in exchange settings

**Diagnostic Command**:
```bash
python test_bitget_connection.py
```

## Trading Execution Issues

### Insufficient Funds

**Symptom**:
```
[INFO] Insufficient funds for BUY order. This is normal if you don't have enough balance.
```

**Solutions**:
1. Add funds to your exchange account
2. Reduce position size settings
3. Check minimum order requirements (typically 10 USDT)

### Order Size Too Small

**Symptom**:
```
[INFO] BUY order too small (min 10 USDT). This is normal for small balances.
```

**Solutions**:
1. Increase account balance
2. Bot automatically adjusts to minimum sizes
3. Consider trading higher-value pairs

### Invalid Order Parameters

**Symptom**:
```
[ERROR] Invalid order amount
```

**Solutions**:
1. Check account balance
2. Verify trading pair is active
3. Review position sizing configuration

### Trading Limits Exceeded

**Symptom**:
```
Trade execution failed: Trading limits exceeded
```

**Solutions**:
1. Increase `MAX_DAILY_TRADES` in `.env`
2. Wait for daily reset (midnight UTC)
3. Check your trading history

## Market Data Problems

### Yahoo Finance Data Issues

**Symptom**:
```
WARNING: Could not fetch market data for BTC/USDT
```

**Solutions**:
1. Check internet connectivity
2. Verify Yahoo Finance is accessible
3. Try different symbols
4. Check for rate limiting

### Data Quality Issues

**Symptom**:
```
WARNING: Insufficient data for analysis
```

**Solutions**:
1. Wait for more market data to accumulate
2. Check if symbol is actively trading
3. Verify timeframe settings

### Timeframe Compatibility

**Symptom**:
```
ERROR: Unsupported timeframe
```

**Solutions**:
1. Check supported timeframes for your data source
2. Modify `TRADING_TIMEFRAME` in `.env`
3. Verify exchange supports the timeframe

## Risk Management Errors

### Position Sizing Issues

**Symptom**:
```
WARNING: Position size calculation failed
```

**Solutions**:
1. Check market data availability
2. Verify account balance
3. Review risk management configuration

### Risk Limits Exceeded

**Symptom**:
```
[INFO] Trade not executed due to high risk
```

**Solutions**:
1. Review risk configuration in `.env`
2. Check current portfolio exposure
3. Wait for risk levels to decrease

## Performance and Monitoring

### Bot Not Trading

**Diagnostic Steps**:
1. Check console output for analysis results
2. Verify trading pairs are supported
3. Review confidence thresholds
4. Check account balances

### Slow Performance

**Potential Causes**:
1. Network latency
2. Exchange rate limiting
3. Heavy system load
4. Insufficient RAM

**Solutions**:
1. Optimize network connection
2. Reduce number of trading pairs
3. Close other resource-intensive applications

### Log File Analysis

**Key Log Locations**:
- `enhanced_trading_bot.log`: Main activity log
- Console output: Real-time status

**What to Look For**:
- ERROR messages indicating problems
- WARNING messages for potential issues
- Analysis results showing trading signals

## Advanced Debugging

### Enabling Debug Mode

Add to your `.env` file:
```env
LOG_LEVEL=DEBUG
```

This will provide more detailed logging information.

### Running Specific Tests

**Component Tests**:
```bash
python test_components.py
```

**Integration Tests**:
```bash
python test_complete_integration.py
```

**Exchange Tests**:
```bash
python test_bitget_connection.py
```

### Manual Verification Steps

1. **API Key Test**:
   - Log into exchange with same credentials
   - Verify API key permissions
   - Check account balance

2. **Market Data Test**:
   - Visit Yahoo Finance website
   - Check if symbols are available
   - Verify data freshness

3. **Network Test**:
   - Ping exchange API endpoints
   - Check firewall settings
   - Test with simple curl requests

### Common Log Messages and Meanings

| Log Level | Message | Meaning | Action Required |
|-----------|---------|---------|----------------|
| INFO | "Analysis: BUY" | Trading signal generated | None |
| INFO | "Insufficient funds" | Not enough balance | Add funds |
| WARNING | "Network issue" | Temporary connection problem | None (auto-retry) |
| ERROR | "Authentication failed" | API credentials issue | Check .env file |
| ERROR | "Invalid configuration" | Setup problem | Review configuration |

### Creating Debug Reports

When reporting issues, include:
1. Console output showing the error
2. Relevant sections from log files
3. Your `.env` configuration (remove sensitive data)
4. Steps to reproduce the issue

## Recovery Procedures

### Resetting Bot State

If the bot becomes unresponsive:
1. Press `Ctrl+C` to stop gracefully
2. Check for any remaining orders on exchange
3. Restart the bot

### Clearing Cache

To clear cached data:
1. Stop the bot
2. Delete `crypto_bot.db` file
3. Restart the bot

### Restoring from Backup

If you have configuration backups:
1. Stop the bot
2. Restore `.env` file from backup
3. Verify settings
4. Restart the bot

## Contact Support

If you're unable to resolve an issue:

1. **Gather Information**:
   - Exact error message
   - Console output
   - Relevant log file sections
   - Your configuration (without sensitive data)

2. **Check Community Resources**:
   - Documentation in `docs/` folder
   - Existing GitHub issues
   - Community forums

3. **Report Issues**:
   - Provide detailed reproduction steps
   - Include environment information
   - Attach relevant logs

Remember: Trading bots involve financial risk. Always test thoroughly in sandbox mode before using with real funds.