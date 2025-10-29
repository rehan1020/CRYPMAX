#!/usr/bin/env python3
"""
Advanced Personal Crypto Trading Bot - Bitget Only Version
Single-user focused with enhanced strategies and risk management
"""

import asyncio
import sys
import os
import ccxt.async_support as ccxt
from dotenv import load_dotenv
from colorama import Fore, Style, init
import logging
import time
from datetime import datetime
import pandas as pd
import numpy as np

# Initialize colorama
init(autoreset=True)

# Load environment variables
load_dotenv()

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add core, analysis, and strategies to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analysis'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'strategies'))

def validate_env():
    """Validate that Bitget API key is present"""
    # Only check for Bitget credentials
    bitget_keys = ['BITGET_API_KEY', 'BITGET_SECRET', 'BITGET_PASSPHRASE']
    
    if all(os.getenv(key) for key in bitget_keys):
        print(f"{Fore.GREEN}✅ Found Bitget API keys")
        return ['bitget']
    else:
        print(f"{Fore.RED}❌ Error: Bitget API keys not found in environment variables.")
        print(f"{Fore.YELLOW}Please set the following environment variables:")
        print(f"{Fore.YELLOW}- BITGET_API_KEY")
        print(f"{Fore.YELLOW}- BITGET_SECRET") 
        print(f"{Fore.YELLOW}- BITGET_PASSPHRASE")
        sys.exit(1)

def get_investment_amount():
    """Get investment amount from user input"""
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    if test_mode:
        print(f"{Fore.YELLOW}⚠️  Test mode enabled")
        print(f"{Fore.CYAN}Please enter your investment amount in USDT (or press Enter for default $1000.00): ", end="")
        try:
            user_input = input().strip()
            if user_input == "":
                amount = 1000.0
                print(f"{Fore.GREEN}✅ Test mode: Investment amount set to default ${amount:.2f} USDT")
            else:
                amount = float(user_input)
                if amount <= 0:
                    print(f"{Fore.RED}❌ Please enter a positive amount. Using default $1000.00")
                    amount = 1000.0
                print(f"{Fore.GREEN}✅ Test mode: Investment amount set to ${amount:.2f} USDT")
            return amount
        except ValueError:
            print(f"{Fore.RED}❌ Invalid input. Using default $1000.00")
            return 1000.0
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  Operation cancelled by user")
            sys.exit(0)

    while True:
        try:
            amount = input(f"{Fore.CYAN}Please enter your investment amount in USDT: ")
            amount = float(amount)
            if amount <= 0:
                print(f"{Fore.RED}❌ Please enter a positive amount.")
                continue
            print(f"{Fore.GREEN}✅ Investment amount set to ${amount:.2f} USDT")
            return amount
        except ValueError:
            print(f"{Fore.RED}❌ Please enter a valid number.")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠️  Operation cancelled by user")
            sys.exit(0)


def get_exchange_selection(available_exchanges):
    """Get exchange selection from user input - Bitget only"""
    # Only Bitget is available
    selected_exchange = 'bitget'
    print(f"{Fore.GREEN}✅ Selected exchange: {selected_exchange.capitalize()}")
    return selected_exchange



async def main():
    """Main function to run the advanced single-user bot using modular trading logic"""
    print(f"{Fore.CYAN}🚀 Starting Advanced Personal Crypto Trading Bot - Bitget Only")
    print(f"{Fore.CYAN}{'='*55}")

    try:
        # Import the enhanced bot and config
        from core.enhanced_main_bot import EnhancedCryptoTradingBot
        from core.config import config

        # Validate environment - only Bitget
        available_exchanges = validate_env()

        # Get investment amount from user
        investment_amount = get_investment_amount()

        # Update config with user investment amount
        config.min_investment = investment_amount
        print(f"{Fore.GREEN}✅ Configured minimum investment: ${investment_amount:.2f} USDT")

        # Get exchange credentials from environment - Bitget only
        exchange_credentials = config.get_exchange_credentials()

        if 'bitget' not in exchange_credentials:
            print(f"{Fore.RED}❌ Error: Bitget credentials not found.")
            sys.exit(1)

        print(f"{Fore.GREEN}✅ Loaded credentials for Bitget exchange")

        # Create bot instance with user config
        bot = EnhancedCryptoTradingBot(config.to_dict())

        # Initialize exchanges - only Bitget
        await bot.initialize_exchanges(exchange_credentials)

        # Check if Bitget was successfully initialized
        if 'bitget' not in bot.exchanges or bot.exchanges['bitget'] is None:
            print(f"{Fore.RED}[ERROR] Failed to initialize Bitget exchange.")
            print(f"{Fore.YELLOW}[INFO] Troubleshooting tips:")
            print(f"{Fore.YELLOW}   • Check that your API key, secret, and passphrase are correct in the .env file")
            print(f"{Fore.YELLOW}   • Verify your internet connection is working")
            print(f"{Fore.YELLOW}   • Ensure you're using the correct Bitget API credentials (not from a different exchange)")
            print(f"{Fore.YELLOW}   • Check that your Bitget account is verified and has trading enabled")
            sys.exit(1)

        print(f"{Fore.GREEN}[SUCCESS] Bot initialized successfully with advanced trading logic")

        # Start the enhanced trading loop
        await bot.run_enhanced_trading_loop()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INTERRUPTED] Bot stopped by user")
        print(f"{Fore.CYAN}[INFO] Tip: The bot will automatically close all connections and save its state.")
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Error running bot: {e}")
        print(f"{Fore.YELLOW}[INFO] Troubleshooting tips:")
        print(f"{Fore.YELLOW}   • Check the detailed error log above for more information")
        print(f"{Fore.YELLOW}   • Verify your .env file is properly configured")
        print(f"{Fore.YELLOW}   • Ensure all required Python packages are installed")
        print(f"{Fore.YELLOW}   • Check your internet connection")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[INTERRUPTED] Bot interrupted by user")
        print(f"{Fore.CYAN}[INFO] Tip: The bot will automatically close all connections and save its state.")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[ERROR] Unexpected error: {e}")
        print(f"{Fore.YELLOW}[INFO] Troubleshooting tips:")
        print(f"{Fore.YELLOW}   • Check the detailed error log above for more information")
        print(f"{Fore.YELLOW}   • Verify your .env file is properly configured")
        print(f"{Fore.YELLOW}   • Ensure all required Python packages are installed")
        print(f"{Fore.YELLOW}   • Check your internet connection")
        import traceback
        traceback.print_exc()
        sys.exit(1)