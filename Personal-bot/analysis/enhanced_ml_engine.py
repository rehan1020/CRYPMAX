# bot/enhanced_ml_engine.py
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.feature_selection import SelectKBest, f_classif
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from datetime import datetime, timedelta
import talib
import warnings
warnings.filterwarnings('ignore')


def safe_talib_conversion(data: Union[pd.Series, pd.DataFrame, Any]) -> np.ndarray:
    """Safely convert pandas Series to numpy array for TA-Lib"""
    try:
        if hasattr(data, 'values'):
            return np.ascontiguousarray(data.values, dtype=np.float64)
        else:
            return np.ascontiguousarray(np.array(data, dtype=np.float64))
    except (ValueError, TypeError):
        # Fallback for any conversion issues
        try:
            if hasattr(data, 'values'):
                return np.ascontiguousarray(data.values, dtype=np.float64)
            return np.ascontiguousarray(np.array(data, dtype=np.float64))
        except Exception:
            # Final fallback - return a default array
            return np.ascontiguousarray(np.array([0.0], dtype=np.float64))


class EnhancedMLEngine:
    """Enhanced Machine Learning engine with advanced features and news sentiment"""

    def __init__(self, model_path: str = "models/enhanced_trading_model.pkl"):
        # Debug: Print the model path being passed to the constructor
        import os
        env_model_path = os.getenv('ML_MODEL_PATH')
        self.logger = logging.getLogger('EnhancedMLEngine')
        self.logger.info(f"Constructor called with model_path: {model_path}")
        self.logger.info(f"ML_MODEL_PATH environment variable: {env_model_path}")
        
        self.model_path = model_path
        self.models = {}  # Multiple model ensemble
        self.scaler = None
        self.feature_selector = None
        self.feature_columns = []
        self.feature_importance = {}
        self.model_performance = {}
        self.is_trained = False

        # Create models directory
        os.makedirs(os.path.dirname(model_path), exist_ok=True)

        # Model configurations
        self.model_configs = {
            'xgboost': {
                'model': XGBClassifier,
                'params': {
                    'n_estimators': 200,
                    'max_depth': 8,
                    'learning_rate': 0.1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'n_jobs': -1,
                    'eval_metric': 'mlogloss'
                }
            },
            'lightgbm': {
                'model': LGBMClassifier,
                'params': {
                    'n_estimators': 200,
                    'max_depth': 8,
                    'learning_rate': 0.1,
                    'num_leaves': 50,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'random_state': 42,
                    'n_jobs': -1,
                    'verbose': -1
                }
            },
            'random_forest': {
                'model': RandomForestClassifier,
                'params': {
                    'n_estimators': 200,
                    'max_depth': 15,
                    'min_samples_split': 5,
                    'min_samples_leaf': 2,
                    'random_state': 42,
                    'n_jobs': -1
                }
            }
        }

        # Load existing model if available
        self.load_model()

    def prepare_advanced_features(self, df: pd.DataFrame, include_news: bool = False) -> pd.DataFrame:
        """Prepare advanced technical features for ML model with reduced DataFrame fragmentation"""
        if df.empty:
            return df
            
        # Create a copy to avoid modifying the original DataFrame
        df = df.copy()
        
        # Collect all new features in a dictionary to add them all at once at the end
        new_features = {}
        
        # Basic returns
        df['returns'] = df['close'].pct_change(fill_method=None)
        new_features['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        new_features['high_low_ratio'] = df['high'] / df['low']
        new_features['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            if len(df) > period:
                df[f'sma_{period}'] = df['close'].rolling(period).mean()
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
                df[f'price_to_sma_{period}'] = df['close'] / df[f'sma_{period}']
        
        # Volatility features
        df['volatility_20'] = df['returns'].rolling(20).std()
        df['volatility_ratio'] = df['volatility_20'] / df['volatility_20'].rolling(50).mean()
        
        # RSI
        if len(df) > 14:
            try:
                close_values = safe_talib_conversion(df['close'])
                df['rsi_14'] = talib.RSI(close_values)
            except Exception as e:
                self.logger.debug(f"RSI calculation failed: {e}")
                df['rsi_14'] = 50  # Neutral RSI value

        # MACD
        if len(df) > 26:
            try:
                close_values = safe_talib_conversion(df['close'])
                macd_line, signal_line, hist = talib.MACD(close_values)
                df['macd_line'] = macd_line
                df['signal_line'] = signal_line
                df['macd_histogram'] = hist
                df['macd_signal'] = np.where(df['macd_histogram'] > 0, 1, -1)
            except Exception as e:
                self.logger.debug(f"MACD calculation failed: {e}")
                df['macd_line'] = 0
                df['signal_line'] = 0
                df['macd_histogram'] = 0
                df['macd_signal'] = 0

        # Bollinger Bands
        if len(df) > 20:
            try:
                close_values = safe_talib_conversion(df['close'])
                upper, middle, lower = talib.BBANDS(close_values)
                df['bb_upper'] = upper
                df['bb_middle'] = middle
                df['bb_lower'] = lower
                df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
                df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            except Exception as e:
                self.logger.debug(f"Bollinger Bands calculation failed: {e}")
                df['bb_upper'] = df['close']
                df['bb_middle'] = df['close']
                df['bb_lower'] = df['close']
                df['bb_width'] = 0
                df['bb_position'] = 0.5

        # ADX
        if len(df) > 14:
            try:
                high_values = safe_talib_conversion(df['high'])
                low_values = safe_talib_conversion(df['low'])
                close_values = safe_talib_conversion(df['close'])
                df['adx'] = talib.ADX(high_values, low_values, close_values)
                df['di_plus'] = talib.PLUS_DI(high_values, low_values, close_values)
                df['di_minus'] = talib.MINUS_DI(high_values, low_values, close_values)
                df['di_diff'] = df['di_plus'] - df['di_minus']
            except Exception as e:
                self.logger.debug(f"ADX calculation failed: {e}")
                df['adx'] = 20
                df['di_plus'] = 20
                df['di_minus'] = 20
                df['di_diff'] = 0

        # Volume features
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_momentum'] = df['volume'].pct_change(3, fill_method=None)
        
        # On-Balance Volume (OBV)
        df['obv'] = self._calculate_obv(df)
        df['obv_momentum'] = df['obv'].pct_change(5, fill_method=None)
        
        # Volume Price Trend (VPT)
        df['vpt'] = self._calculate_vpt(df)
        df['vpt_momentum'] = df['vpt'].pct_change(5, fill_method=None)

        # Money Flow Index (MFI)
        if len(df) > 14:
            try:
                high_values = safe_talib_conversion(df['high'])
                low_values = safe_talib_conversion(df['low'])
                close_values = safe_talib_conversion(df['close'])
                volume_values = safe_talib_conversion(df['volume'])
                df['mfi'] = talib.MFI(high_values, low_values, close_values, volume_values)
            except Exception as e:
                self.logger.debug(f"MFI calculation failed: {e}")
                df['mfi'] = 50

        # Price momentum features
        for period in [1, 3, 5, 10, 20]:
            if len(df) > period:
                df[f'momentum_{period}'] = df['close'].pct_change(period, fill_method=None)
                df[f'momentum_acceleration_{period}'] = df[f'momentum_{period}'].diff(1)

        # Support and resistance features
        df['support_20'] = df['low'].rolling(20).min()
        df['resistance_20'] = df['high'].rolling(20).max()
        df['support_distance'] = (df['close'] - df['support_20']) / df['close']
        df['resistance_distance'] = (df['resistance_20'] - df['close']) / df['close']

        # Trend features
        for period in [10, 20, 50]:
            if len(df) > period:
                df[f'trend_{period}'] = np.where(df['close'] > df[f'sma_{period}'], 1, -1)
                df[f'trend_strength_{period}'] = abs(df['close'] - df[f'sma_{period}']) / df[f'sma_{period}']

        # Candlestick pattern features (simplified binary features)
        df['doji'] = np.where(abs(df['open'] - df['close']) / (df['high'] - df['low'] + 1e-8) < 0.1, 1, 0)
        df['hammer'] = np.where(
            (df['low'] < np.minimum(df['open'], df['close'])) &
            ((np.minimum(df['open'], df['close']) - df['low']) > 2 * abs(df['open'] - df['close'])), 1, 0
        )
        df['shooting_star'] = np.where(
            (df['high'] > np.maximum(df['open'], df['close'])) &
            ((df['high'] - np.maximum(df['open'], df['close'])) > 2 * abs(df['open'] - df['close'])), 1, 0
        )
        
        # Additional candlestick patterns
        # Engulfing patterns
        if len(df) > 1:
            prev_open = df['open'].shift(1)
            prev_close = df['close'].shift(1)
            prev_high = df['high'].shift(1)
            prev_low = df['low'].shift(1)
            
            # Bullish engulfing
            new_features['bullish_engulfing'] = np.where(
                (df['close'] > df['open']) &  # Current bullish
                (prev_open > prev_close) &    # Previous bearish
                (df['open'] < prev_close) &   # Current opens below previous close
                (df['close'] > prev_open),    # Current closes above previous open
                1, 0
            )
            
            # Bearish engulfing
            new_features['bearish_engulfing'] = np.where(
                (df['open'] > df['close']) &  # Current bearish
                (prev_close > prev_open) &    # Previous bullish
                (df['open'] > prev_close) &   # Current opens above previous close
                (df['close'] < prev_open),    # Current closes below previous open
                1, 0
            )
            
            # Harami patterns
            new_features['bullish_harami'] = np.where(
                (prev_open > prev_close) &    # Previous bearish
                (df['close'] > df['open']) &  # Current bullish
                (df['open'] > prev_close) &   # Current opens above previous close
                (df['close'] < prev_open),    # Current closes below previous open
                1, 0
            )
            
            new_features['bearish_harami'] = np.where(
                (prev_close > prev_open) &    # Previous bullish
                (df['open'] > df['close']) &  # Current bearish
                (df['open'] < prev_close) &   # Current opens below previous close
                (df['close'] > prev_open),    # Current closes above previous open
                1, 0
            )
            
            # Piercing line and dark cloud cover
            new_features['piercing_line'] = np.where(
                (prev_open > prev_close) &    # Previous bearish
                (df['close'] > df['open']) &  # Current bullish
                (df['open'] < prev_low) &     # Current opens below previous low
                (df['close'] > (prev_open + prev_close) / 2),  # Closes above midpoint
                1, 0
            )
            
            new_features['dark_cloud_cover'] = np.where(
                (prev_close > prev_open) &    # Previous bullish
                (df['open'] > df['close']) &  # Current bearish
                (df['open'] > prev_high) &    # Current opens above previous high
                (df['close'] < (prev_open + prev_close) / 2),  # Closes below midpoint
                1, 0
            )
            
            # Morning and evening star (simplified 3-bar patterns)
            if len(df) > 2:
                prev2_open = df['open'].shift(2)
                prev2_close = df['close'].shift(2)
                
                # Morning star - simplified
                new_features['morning_star'] = np.where(
                    (prev2_open > prev2_close) &  # 2 bars ago bearish
                    (prev_close < prev_open) &    # Previous bearish but smaller
                    (df['close'] > df['open']) &  # Current bullish
                    (df['close'] > prev2_open),   # Current closes above 2 bars ago open
                    1, 0
                )
                
                # Evening star - simplified
                new_features['evening_star'] = np.where(
                    (prev2_close > prev2_open) &  # 2 bars ago bullish
                    (prev_close > prev_open) &    # Previous bullish but smaller
                    (df['open'] > df['close']) &  # Current bearish
                    (df['close'] < prev2_open),   # Current closes below 2 bars ago open
                    1, 0
                )
            else:
                # If not enough data, set all additional patterns to 0
                new_features['morning_star'] = 0
                new_features['evening_star'] = 0
        else:
            # If not enough data, set all additional patterns to 0
            new_features['bullish_engulfing'] = 0
            new_features['bearish_engulfing'] = 0
            new_features['bullish_harami'] = 0
            new_features['bearish_harami'] = 0
            new_features['piercing_line'] = 0
            new_features['dark_cloud_cover'] = 0
            new_features['morning_star'] = 0
            new_features['evening_star'] = 0

        # Market microstructure features
        new_features['price_efficiency'] = abs(df['returns']) / (df['high'] - df['low'] + 1e-8)
        new_features['intraday_return'] = (df['close'] - df['open']) / df['open']
        new_features['overnight_return'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        # Prepare additional features as a batch to reduce DataFrame fragmentation
        additional_features = {}
        
        # Regime detection features - only if sufficient data
        if 'volatility_20' in df.columns:
            additional_features['volatility_regime'] = np.where(df['volatility_20'] > df['volatility_20'].rolling(50).quantile(0.7), 1, 0)
        else:
            additional_features['volatility_regime'] = 0
        additional_features['volume_regime'] = np.where(df['volume_ratio'] > 1.5, 1, 0)

        # Seasonal features
        try:
            if hasattr(df.index, 'hour'):
                additional_features['hour'] = df.index.hour  # type: ignore
            else:
                additional_features['hour'] = 12
            if hasattr(df.index, 'dayofweek'):    
                additional_features['day_of_week'] = df.index.dayofweek  # type: ignore
            else:
                additional_features['day_of_week'] = 1
        except AttributeError:
            additional_features['hour'] = 12
            additional_features['day_of_week'] = 1
        
        hour_values = additional_features.get('hour', 12)
        day_of_week_values = additional_features.get('day_of_week', 1)
        additional_features['hour_sin'] = np.sin(2 * np.pi * hour_values / 24)
        additional_features['hour_cos'] = np.cos(2 * np.pi * hour_values / 24)
        additional_features['dow_sin'] = np.sin(2 * np.pi * day_of_week_values / 7)
        additional_features['dow_cos'] = np.cos(2 * np.pi * day_of_week_values / 7)

        # News sentiment features (placeholder - would integrate with actual news API)
        if include_news:
            additional_features['news_sentiment'] = 0.0  # Neutral sentiment
            additional_features['news_volume'] = 0  # No news
            additional_features['sentiment_momentum'] = 0.0

        # Interaction features (most important combinations) - handle missing columns gracefully
        rsi_value = df['rsi_14'].iloc[0] if 'rsi_14' in df.columns and len(df) > 0 else 50
        momentum_value = df['momentum_5'].iloc[0] if 'momentum_5' in df.columns and len(df) > 0 else 0
        additional_features['rsi_momentum_interaction'] = rsi_value * momentum_value
        
        volume_ratio_value = df['volume_ratio'].iloc[0] if 'volume_ratio' in df.columns and len(df) > 0 else 1
        returns_value = df['returns'].iloc[0] if 'returns' in df.columns and len(df) > 0 else 0
        additional_features['volume_price_interaction'] = volume_ratio_value * abs(returns_value)
        
        volatility_value = df['volatility_20'].iloc[0] if 'volatility_20' in df.columns and len(df) > 0 else 0.02
        momentum_10_value = df['momentum_10'].iloc[0] if 'momentum_10' in df.columns and len(df) > 0 else 0
        additional_features['volatility_momentum_interaction'] = volatility_value * momentum_10_value
        
        # Add all additional features at once to reduce fragmentation
        # Combine new_features and additional_features
        all_new_features = {**new_features, **additional_features}
        additional_df = pd.DataFrame(all_new_features, index=df.index)
        df = pd.concat([df, additional_df], axis=1)

        # Remove infinite and NaN values
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.ffill().bfill().fillna(0)

        return df

    def create_enhanced_labels(self, df: pd.DataFrame, prediction_horizon: int = 5, 
                             profit_threshold: float = 0.015, loss_threshold: float = 0.01) -> pd.Series:
        """Create enhanced target labels with multiple profit/loss thresholds"""
        future_prices = df['close'].shift(-prediction_horizon)
        current_prices = df['close']
        
        # Calculate future returns
        future_returns = (future_prices - current_prices) / current_prices
        
        # Multi-class labeling with confidence levels
        labels = pd.Series(1, index=df.index)  # Default HOLD
        
        # Strong BUY: Expected return > profit_threshold
        labels[future_returns > profit_threshold] = 2
        
        # Strong SELL: Expected return < -loss_threshold  
        labels[future_returns < -loss_threshold] = 0
        
        # Remove labels for last prediction_horizon rows
        if len(labels) > prediction_horizon:
            labels = labels[:-prediction_horizon]
        
        return pd.Series(labels, index=df.index[:len(labels)])

    def train_ensemble_model(self, historical_data: Dict[str, pd.DataFrame], 
                           test_size: float = 0.2, optimize_hyperparams: bool = True) -> bool:
        """Train ensemble of ML models with hyperparameter optimization"""
        self.logger.info("Starting enhanced ensemble model training...")
        
        try:
            # Prepare training data
            all_features, all_labels = self._prepare_training_data(historical_data)
            
            if len(all_features) < 100:
                self.logger.error("Insufficient training data")
                return False

            # Feature selection
            self.feature_selector = SelectKBest(score_func=f_classif, k=min(50, len(all_features.columns)))
            X_selected = self.feature_selector.fit_transform(all_features, all_labels)
            selected_features = all_features.columns[self.feature_selector.get_support()]
            self.feature_columns = list(selected_features)
            
            self.logger.info(f"Selected {len(self.feature_columns)} features from {len(all_features.columns)}")

            # Scale features
            self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
            X_scaled = self.scaler.fit_transform(X_selected)

            # Split data with stratification
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, all_labels, test_size=test_size, random_state=42, 
                stratify=all_labels, shuffle=True
            )

            # Train individual models
            for model_name, config in self.model_configs.items():
                self.logger.info(f"Training {model_name}...")
                
                model_class = config['model']
                base_params = config['params'].copy()
                
                if optimize_hyperparams and model_name == 'xgboost':
                    # Hyperparameter optimization for best model
                    model = self._optimize_hyperparameters(model_class, base_params, X_train, y_train)
                else:
                    model = model_class(**base_params)
                
                # Train model
                model.fit(X_train, y_train)
                
                # Evaluate model
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_scaled, all_labels, cv=5, scoring='accuracy')
                
                self.models[model_name] = model
                self.model_performance[model_name] = {
                    'train_accuracy': train_score,
                    'test_accuracy': test_score,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                }
                
                self.logger.info(
                    f"{model_name}: Train={train_score:.4f}, Test={test_score:.4f}, "
                    f"CV={cv_scores.mean():.4f}±{cv_scores.std():.4f}"
                )

            # Create ensemble model
            ensemble_models = [(name, model) for name, model in self.models.items()]
            self.ensemble_model = VotingClassifier(
                estimators=ensemble_models,
                voting='soft'  # Use probabilities for voting
            )
            self.ensemble_model.fit(X_train, y_train)
            
            # Evaluate ensemble
            ensemble_train_score = self.ensemble_model.score(X_train, y_train)
            ensemble_test_score = self.ensemble_model.score(X_test, y_test)
            
            self.model_performance['ensemble'] = {
                'train_accuracy': ensemble_train_score,
                'test_accuracy': ensemble_test_score
            }
            
            self.logger.info(
                f"Ensemble: Train={ensemble_train_score:.4f}, Test={ensemble_test_score:.4f}"
            )

            # Feature importance analysis
            self._analyze_feature_importance()
            
            # Save model
            self.is_trained = True
            self.save_model()
            
            return True

        except Exception as e:
            self.logger.error(f"Enhanced model training failed: {str(e)}")
            return False

    def predict_with_confidence(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Make prediction with ensemble model and confidence intervals"""
        if not self.is_trained or not hasattr(self, 'ensemble_model'):
            return {
                'prediction': 'HOLD',
                'confidence': 0.0,
                'probabilities': {'SELL': 0.33, 'HOLD': 0.34, 'BUY': 0.33},
                'ensemble_agreement': 0.0
            }

        try:
            # Prepare features
            features_df = self.prepare_advanced_features(df)
            if len(features_df) == 0:
                return {'prediction': 'HOLD', 'confidence': 0.0, 'probabilities': {}}

            # Get latest features
            latest_features = features_df.iloc[-1:][self.feature_columns]
            if self.scaler is not None:
                X_scaled = self.scaler.transform(latest_features)
            else:
                X_scaled = latest_features.values

            # Individual model predictions
            individual_predictions = {}
            individual_probabilities = {}
            
            for model_name, model in self.models.items():
                pred = model.predict(X_scaled)[0]
                proba = model.predict_proba(X_scaled)[0]
                
                individual_predictions[model_name] = pred
                individual_probabilities[model_name] = proba

            # Ensemble prediction
            ensemble_pred = self.ensemble_model.predict(X_scaled)[0]
            ensemble_proba = self.ensemble_model.predict_proba(X_scaled)[0]

            # Calculate ensemble agreement
            pred_values = list(individual_predictions.values())
            agreement = pred_values.count(ensemble_pred) / len(pred_values)

            # Convert to trading signals
            prediction_map = {0: 'SELL', 1: 'HOLD', 2: 'BUY'}
            prediction = prediction_map.get(ensemble_pred, 'HOLD')
            
            # Confidence is the probability of predicted class
            confidence = float(ensemble_proba.max())
            
            # Adjust confidence based on ensemble agreement
            adjusted_confidence = confidence * (0.5 + 0.5 * agreement)

            probabilities = {
                'SELL': float(ensemble_proba[0]),
                'HOLD': float(ensemble_proba[1]) if len(ensemble_proba) > 1 else 0.0,
                'BUY': float(ensemble_proba[2]) if len(ensemble_proba) > 2 else 0.0
            }

            return {
                'prediction': prediction,
                'confidence': adjusted_confidence,
                'probabilities': probabilities,
                'ensemble_agreement': agreement,
                'individual_predictions': individual_predictions,
                'model_performance': self.model_performance
            }

        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            return {'prediction': 'HOLD', 'confidence': 0.0, 'probabilities': {}}

    def _prepare_training_data(self, historical_data: Dict[str, pd.DataFrame]) -> Tuple[Any, Any]:
        """Prepare training dataset from historical data"""
        all_features = []
        all_labels = []

        for symbol, df in historical_data.items():
            if len(df) < 200:  # Need sufficient data
                continue

            try:
                # Prepare features
                features_df = self.prepare_advanced_features(df, include_news=False)
                
                # Create labels
                labels = self.create_enhanced_labels(features_df)
                
                # Align features and labels
                common_index = features_df.index.intersection(labels.index)
                if len(common_index) < 100:
                    continue
                    
                features_aligned = features_df.loc[common_index]
                labels_aligned = labels.loc[common_index]

                all_features.append(features_aligned)
                all_labels.append(labels_aligned)
                
                self.logger.info(f"Prepared {len(features_aligned)} samples for {symbol}")

            except Exception as e:
                self.logger.warning(f"Failed to prepare data for {symbol}: {e}")
                continue

        if not all_features:
            raise ValueError("No valid training data prepared")

        # Combine all data
        X = pd.concat(all_features, ignore_index=True)
        y = pd.concat(all_labels, ignore_index=True)

        # Remove non-numeric columns and handle missing values
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        X = X.fillna(X.median())  # Fill remaining NaN with median

        self.logger.info(f"Final training set: {len(X)} samples, {len(X.columns)} features")
        return X, y  # type: ignore

    def _optimize_hyperparameters(self, model_class, base_params: Dict, X_train, y_train):
        """Optimize hyperparameters using GridSearchCV"""
        param_grid = {
            'n_estimators': [100, 200],
            'max_depth': [6, 8, 10],
            'learning_rate': [0.05, 0.1, 0.15]
        }
        
        model = model_class(**base_params)
        grid_search = GridSearchCV(
            model, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=0
        )
        
        grid_search.fit(X_train, y_train)
        
        self.logger.info(f"Best parameters: {grid_search.best_params_}")
        return grid_search.best_estimator_

    def _analyze_feature_importance(self):
        """Analyze and store feature importance from trained models"""
        if 'xgboost' in self.models:
            # Get feature importance from XGBoost
            importance_scores = self.models['xgboost'].feature_importances_
            self.feature_importance = dict(zip(self.feature_columns, importance_scores))
            
            # Sort by importance
            sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            self.logger.info("Top 10 most important features:")
            for feature, importance in sorted_features[:10]:
                self.logger.info(f"  {feature}: {importance:.4f}")

    def save_model(self):
        """Save trained ensemble model"""
        try:
            model_data = {
                'models': self.models,
                'ensemble_model': self.ensemble_model,
                'scaler': self.scaler,
                'feature_selector': self.feature_selector,
                'feature_columns': self.feature_columns,
                'feature_importance': self.feature_importance,
                'model_performance': self.model_performance,
                'trained_at': datetime.now(),
                'model_version': '2.0'
            }
            
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_data, f)
                
            self.logger.info("Enhanced ensemble model saved successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to save model: {str(e)}")

    def load_model(self):
        """Load trained ensemble model"""
        try:
            # Debug: Print the model path being checked
            self.logger.info(f"Checking for model at path: {self.model_path}")
            self.logger.info(f"Current working directory: {os.getcwd()}")
            self.logger.info(f"Absolute model path: {os.path.abspath(self.model_path)}")
            self.logger.info(f"Model file exists: {os.path.exists(self.model_path)}")
            
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.models = model_data.get('models', {})
                self.ensemble_model = model_data.get('ensemble_model')
                self.scaler = model_data.get('scaler')
                self.feature_selector = model_data.get('feature_selector')
                self.feature_columns = model_data.get('feature_columns', [])
                self.feature_importance = model_data.get('feature_importance', {})
                self.model_performance = model_data.get('model_performance', {})
                
                if self.ensemble_model is not None:
                    self.is_trained = True
                    self.logger.info("Enhanced ensemble model loaded successfully")
                else:
                    self.logger.info("Model file exists but ensemble model not found")
            else:
                self.logger.info("No existing model found")
                
        except Exception as e:
            self.logger.error(f"Failed to load model: {str(e)}")

    def get_model_stats(self) -> Dict[str, Any]:
        """Get comprehensive model statistics"""
        if not self.is_trained:
            return {'status': 'not_trained'}

        try:
            stats = {
                'status': 'trained',
                'features_count': len(self.feature_columns),
                'models_count': len(self.models),
                'feature_importance': dict(list(self.feature_importance.items())[:10]),
                'model_performance': self.model_performance,
                'top_features': list(self.feature_importance.keys())[:5] if self.feature_importance else []
            }
            
            return stats
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    # Helper methods
    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculate On-Balance Volume"""
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        return pd.Series(obv, index=df.index)

    def _calculate_vpt(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Volume Price Trend"""
        vpt = [0]
        for i in range(1, len(df)):
            price_change = (df['close'].iloc[i] - df['close'].iloc[i-1]) / df['close'].iloc[i-1]
            vpt.append(vpt[-1] + df['volume'].iloc[i] * price_change)
        return pd.Series(vpt, index=df.index)