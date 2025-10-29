#!/usr/bin/env python3
"""
Script to train and save the ML model for the trading bot
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from analysis.enhanced_ml_engine import EnhancedMLEngine
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_sample_data(symbol="BTC/USDT", days=30) -> Dict[str, pd.DataFrame]:
    """Generate sample market data for training"""
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # Generate realistic price data
    n_points = len(dates)
    base_price = 50000  # Starting price for BTC
    
    # Generate price series with some randomness
    prices: list[float] = [base_price]
    for i in range(1, n_points):
        # Random walk with trend
        change = np.random.normal(0, 0.02)  # 2% standard deviation
        new_price = prices[-1] * (1 + change)
        # Keep prices reasonable
        new_price = max(new_price, base_price * 0.5)  # Minimum 50% of base
        new_price = min(new_price, base_price * 1.5)  # Maximum 150% of base
        prices.append(float(new_price))
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
        'close': prices,
        'volume': [np.random.uniform(1000, 10000) for _ in range(n_points)]
    })
    
    # Adjust high/low to make sure they encompass open/close
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    df.set_index('timestamp', inplace=True)
    return {symbol: df}

def train_model():
    """Train and save the ML model"""
    print("Training ML model...")
    
    try:
        # Initialize ML engine
        ml_engine = EnhancedMLEngine("models/enhanced_trading_model.pkl")
        
        # Generate sample training data
        print("Generating sample training data...")
        historical_data = generate_sample_data("BTC/USDT", days=30)
        
        # Add more symbols for better training
        historical_data.update(generate_sample_data("ETH/USDT", days=30))
        historical_data.update(generate_sample_data("BNB/USDT", days=30))
        
        # Train the model
        print("Training ensemble model...")
        success = ml_engine.train_ensemble_model(historical_data, optimize_hyperparams=False)
        
        if success:
            print("✅ Model trained successfully")
            
            # Save the model
            print("Saving model...")
            ml_engine.save_model()
            
            # Test prediction
            print("Testing prediction...")
            sample_data = list(historical_data.values())[0].tail(100)  # Last 100 data points
            prediction = ml_engine.predict_with_confidence(sample_data)
            print(f"Sample prediction: {prediction}")
            
            return True
        else:
            print("❌ Model training failed")
            return False
            
    except Exception as e:
        print(f"❌ Error training model: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = train_model()
    sys.exit(0 if success else 1)