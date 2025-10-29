# bot/risk_management.py
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Import colorama for colored console output if available
try:
    from colorama import init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class PositionSize:
    """Position sizing calculation result"""
    recommended_size: float
    max_size: float
    risk_amount: float
    risk_percentage: float
    confidence_adjusted_size: float
    reasoning: str

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics"""
    portfolio_risk: float
    position_risk: float
    correlation_risk: float
    volatility_risk: float
    drawdown_risk: float
    concentration_risk: float
    overall_risk_level: RiskLevel
    risk_warnings: List[str]

class EnhancedRiskManager:
    """Comprehensive risk management system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger('EnhancedRiskManager')
        
        # Risk parameters (configurable)
        self.config = config or {}
        self.max_position_risk = self.config.get('max_position_risk', 0.02)  # 2% per trade
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.10)  # 10% total
        self.max_correlation = self.config.get('max_correlation', 0.7)  # 70% correlation limit
        self.max_concentration = self.config.get('max_concentration', 0.25)  # 25% in single asset
        self.max_drawdown = self.config.get('max_drawdown', 0.15)  # 15% max drawdown
        self.volatility_threshold = self.config.get('volatility_threshold', 0.5)  # 50% annualized vol
        
        # Portfolio tracking
        self.portfolio_value = self.config.get('initial_capital', 10000)
        self.current_positions = {}
        self.trade_history = []
        self.daily_returns = []
        
    def calculate_position_size(self, 
                              signal_confidence: float,
                              market_data: pd.DataFrame,
                              symbol: str,
                              side: str,
                              current_price: float,
                              stop_loss_price: Optional[float] = None) -> PositionSize:
        """
        Calculate optimal position size using multiple risk management techniques
        
        Args:
            signal_confidence: Trading signal confidence (0-1)
            market_data: Historical market data for volatility calculation
            symbol: Trading symbol
            side: 'buy' or 'sell'
            current_price: Current market price
            stop_loss_price: Stop loss price (optional)
            
        Returns:
            PositionSize object with detailed sizing recommendations
        """
        
        try:
            # 1. Kelly Criterion sizing
            kelly_size = self._calculate_kelly_size(signal_confidence, market_data)
            
            # 2. Volatility-based sizing
            volatility = self._calculate_volatility(market_data)
            vol_size = self._calculate_volatility_size(volatility)
            
            # 3. Fixed fractional sizing
            fixed_size = self.max_position_risk * self.portfolio_value
            
            # 4. Stop-loss based sizing
            if stop_loss_price:
                stop_loss_size = self._calculate_stop_loss_size(current_price, stop_loss_price)
            else:
                # Estimate stop loss based on ATR
                atr = self._calculate_atr(market_data)
                estimated_stop = current_price - (2 * atr) if side == 'buy' else current_price + (2 * atr)
                stop_loss_size = self._calculate_stop_loss_size(current_price, estimated_stop)
            
            # Take the minimum of all sizing methods for safety
            base_size = min(kelly_size, vol_size, fixed_size, stop_loss_size)
            
            # Confidence adjustment
            confidence_adjusted_size = base_size * signal_confidence
            
            # Portfolio heat adjustment
            portfolio_heat = self._calculate_portfolio_heat()
            if portfolio_heat > 0.5:  # Reduce size if portfolio is already risky
                confidence_adjusted_size *= (1 - portfolio_heat * 0.5)
            
            # Maximum size limits
            max_position_value = self.portfolio_value * self.max_concentration
            max_size = max_position_value / current_price
            
            # Final recommended size
            recommended_size = min(confidence_adjusted_size / current_price, max_size)
            
            # Ensure minimum order size (10 USDT) - NEW: Check if calculated size meets minimum requirements
            min_order_value = 10.0  # USDT
            min_size_for_order = min_order_value / current_price if current_price > 0 else 0.0
            
            # If calculated size is below minimum, use minimum size
            if recommended_size * current_price < min_order_value:
                recommended_size = min_size_for_order
            
            # But ensure we don't exceed maximum size limits even with minimum order size
            recommended_size = min(recommended_size, max_size)
            
            # Log position sizing with color coding
            if COLORAMA_AVAILABLE:
                try:
                    from colorama import Fore, Style
                    if recommended_size * current_price >= min_order_value:
                        size_status = f"{Fore.GREEN}✓ Meets minimum{Style.RESET_ALL}"
                    else:
                        size_status = f"{Fore.YELLOW}⚠ Adjusted to minimum{Style.RESET_ALL}"
                    
                    self.logger.info(f"Position sizing for {symbol}: {recommended_size:.6f} ({recommended_size * current_price:.2f} USDT) - {size_status}")
                except ImportError:
                    self.logger.info(f"Position sizing for {symbol}: {recommended_size:.6f} ({recommended_size * current_price:.2f} USDT)")
            else:
                self.logger.info(f"Position sizing for {symbol}: {recommended_size:.6f} ({recommended_size * current_price:.2f} USDT)")
            
            return PositionSize(
                recommended_size=recommended_size,
                max_size=max_size,
                risk_amount=recommended_size * current_price,
                risk_percentage=(recommended_size * current_price) / self.portfolio_value,
                confidence_adjusted_size=confidence_adjusted_size / current_price,
                reasoning=f"Kelly: ${kelly_size:.0f}, Vol: ${vol_size:.0f}, Fixed: ${fixed_size:.0f}, "
                         f"StopLoss: ${stop_loss_size:.0f}, Confidence: {signal_confidence:.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Position sizing calculation failed: {e}")
            # Return conservative fallback
            if current_price > 0:
                fallback_size = (self.portfolio_value * 0.01) / current_price  # 1% of portfolio
            else:
                fallback_size = 0.0  # Can't calculate with zero price
            return PositionSize(
                recommended_size=fallback_size,
                max_size=fallback_size,
                risk_amount=fallback_size * current_price if current_price > 0 else 0.0,
                risk_percentage=0.01 if self.portfolio_value > 0 else 0.0,
                confidence_adjusted_size=fallback_size,
                reasoning="Fallback due to calculation error"
            )
    
    def assess_trade_risk(self, 
                         symbol: str,
                         side: str,
                         size: float,
                         confidence: float,
                         market_data: pd.DataFrame) -> RiskMetrics:
        """
        Comprehensive risk assessment for a potential trade
        
        Returns:
            RiskMetrics object with detailed risk analysis
        """
        
        warnings = []
        
        # 1. Position risk
        if len(market_data) > 0 and 'close' in market_data.columns and len(market_data['close']) > 0:
            position_value = size * market_data['close'].iloc[-1]
        else:
            position_value = size * 50000.0  # Default price for fallback
        position_risk = position_value / self.portfolio_value if self.portfolio_value > 0 else 0.0
        
        # 2. Portfolio risk
        portfolio_risk = self._calculate_portfolio_risk(symbol, position_value)
        
        # 3. Correlation risk
        correlation_risk = self._calculate_correlation_risk(symbol, market_data)
        
        # 4. Volatility risk
        volatility = self._calculate_volatility(market_data)
        volatility_risk = min(volatility / self.volatility_threshold, 1.0) if self.volatility_threshold > 0 else 0.0
        
        # 5. Drawdown risk
        drawdown_risk = self._calculate_current_drawdown()
        
        # 6. Concentration risk
        concentration_risk = self._calculate_concentration_risk(symbol, position_value)
        
        # Generate warnings
        if position_risk > self.max_position_risk:
            warnings.append(f"Position risk {position_risk:.1%} exceeds limit {self.max_position_risk:.1%}")
            
        if portfolio_risk > self.max_portfolio_risk:
            warnings.append(f"Portfolio risk {portfolio_risk:.1%} exceeds limit {self.max_portfolio_risk:.1%}")
            
        if volatility_risk > 0.8:
            warnings.append(f"High volatility detected: {volatility:.1%} annualized")
            
        if drawdown_risk > 0.8:
            warnings.append("Portfolio near maximum drawdown limit")
            
        if concentration_risk > 0.8:
            warnings.append(f"High concentration risk in {symbol}")
        
        # Overall risk level - more nuanced calculation
        # For small positions, don't immediately classify as HIGH risk
        position_risk_factor = position_risk / self.max_position_risk if self.max_position_risk > 0 else 0.0
        portfolio_risk_factor = portfolio_risk / self.max_portfolio_risk if self.max_portfolio_risk > 0 else 0.0
        
        # Use weighted average with emphasis on actual violations
        risk_scores = [
            min(position_risk_factor, 1.0),  # Cap at 1.0 for position risk
            min(portfolio_risk_factor, 1.0),  # Cap at 1.0 for portfolio risk
            correlation_risk,
            volatility_risk,
            drawdown_risk,
            concentration_risk
        ]
        
        # If position risk is only slightly over the limit, don't penalize too harshly
        if position_risk_factor <= 1.5:  # Up to 50% over limit is acceptable
            risk_scores[0] = position_risk_factor * 0.7  # Reduce impact
            
        # If portfolio risk is only slightly over the limit, don't penalize too harshly
        if portfolio_risk_factor <= 1.5:  # Up to 50% over limit is acceptable
            risk_scores[1] = portfolio_risk_factor * 0.7  # Reduce impact
        
        avg_risk = np.mean(risk_scores)
        
        if avg_risk < 0.3:
            risk_level = RiskLevel.LOW
        elif avg_risk < 0.6:
            risk_level = RiskLevel.MEDIUM
        elif avg_risk < 0.9:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL
            
        # Log risk assessment with color coding
        if COLORAMA_AVAILABLE:
            try:
                from colorama import Fore, Style
                if risk_level == RiskLevel.LOW:
                    risk_color = Fore.GREEN
                elif risk_level == RiskLevel.MEDIUM:
                    risk_color = Fore.BLUE
                elif risk_level == RiskLevel.HIGH:
                    risk_color = Fore.YELLOW
                else:  # CRITICAL
                    risk_color = Fore.RED + Style.BRIGHT
                
                risk_display = f"{risk_color}{risk_level.value.upper()}{Style.RESET_ALL}"
                self.logger.info(f"Risk assessment for {symbol}: {risk_display} (avg: {avg_risk:.2f})")
            except ImportError:
                self.logger.info(f"Risk assessment for {symbol}: {risk_level.value.upper()} (avg: {avg_risk:.2f})")
        else:
            self.logger.info(f"Risk assessment for {symbol}: {risk_level.value.upper()} (avg: {avg_risk:.2f})")
            
        return RiskMetrics(
            portfolio_risk=portfolio_risk,
            position_risk=position_risk,
            correlation_risk=correlation_risk,
            volatility_risk=volatility_risk,
            drawdown_risk=drawdown_risk,
            concentration_risk=concentration_risk,
            overall_risk_level=risk_level,
            risk_warnings=warnings
        )
    
    def should_allow_trade(self, risk_metrics: RiskMetrics, confidence: float) -> Tuple[bool, str]:
        """
        Determine if a trade should be allowed based on risk assessment
        
        Returns:
            Tuple of (allow_trade, reason)
        """
        
        # Critical risk level blocks all trades
        if risk_metrics.overall_risk_level == RiskLevel.CRITICAL:
            return False, "Critical risk level - trade blocked"
        
        # High risk requires high confidence
        if risk_metrics.overall_risk_level == RiskLevel.HIGH and confidence < 0.8:
            return False, "High risk requires high confidence (>80%)"
        
        # Portfolio risk limits
        if risk_metrics.portfolio_risk > self.max_portfolio_risk:
            return False, f"Portfolio risk {risk_metrics.portfolio_risk:.1%} exceeds limit"
        
        # Position risk limits
        if risk_metrics.position_risk > self.max_position_risk * 2:  # Allow some flexibility
            return False, f"Position risk {risk_metrics.position_risk:.1%} too high"
        
        # Drawdown protection
        if risk_metrics.drawdown_risk > 0.9:
            return False, "Portfolio near maximum drawdown limit"
        
        return True, "Trade allowed"
    
    def calculate_stop_loss(self, 
                           entry_price: float,
                           side: str,
                           market_data: pd.DataFrame,
                           method: str = 'atr') -> Dict[str, Any]:
        """
        Calculate dynamic stop loss levels
        
        Args:
            entry_price: Entry price for the position
            side: 'buy' or 'sell'
            market_data: Historical market data
            method: 'atr', 'support_resistance', 'percentage', or 'volatility'
            
        Returns:
            Dict with stop loss information
        """
        
        if method == 'atr':
            atr = self._calculate_atr(market_data)
            multiplier = 2.0  # 2x ATR
            
            if side == 'buy':
                stop_loss = entry_price - (atr * multiplier)
            else:
                stop_loss = entry_price + (atr * multiplier)
                
            return {
                'stop_loss_price': stop_loss,
                'distance': abs(entry_price - stop_loss),
                'distance_percentage': abs(entry_price - stop_loss) / entry_price,
                'method': 'ATR',
                'atr_value': atr,
                'atr_multiplier': multiplier
            }
            
        elif method == 'percentage':
            percentage = 0.03  # 3% stop loss
            
            if side == 'buy':
                stop_loss = entry_price * (1 - percentage)
            else:
                stop_loss = entry_price * (1 + percentage)
                
            return {
                'stop_loss_price': stop_loss,
                'distance': abs(entry_price - stop_loss),
                'distance_percentage': percentage,
                'method': 'Percentage'
            }
            
        elif method == 'volatility':
            volatility = self._calculate_volatility(market_data, period=20)
            # Use 2 standard deviations
            vol_distance = entry_price * volatility * 2
            
            if side == 'buy':
                stop_loss = entry_price - vol_distance
            else:
                stop_loss = entry_price + vol_distance
                
            return {
                'stop_loss_price': stop_loss,
                'distance': vol_distance,
                'distance_percentage': vol_distance / entry_price,
                'method': 'Volatility',
                'volatility': volatility
            }
            
        else:  # support_resistance
            # Simplified support/resistance calculation
            if side == 'buy':
                support = market_data['low'].rolling(20).min().iloc[-1]
                stop_loss = support * 0.99  # Slightly below support
            else:
                resistance = market_data['high'].rolling(20).max().iloc[-1]
                stop_loss = resistance * 1.01  # Slightly above resistance
                
            return {
                'stop_loss_price': stop_loss,
                'distance': abs(entry_price - stop_loss),
                'distance_percentage': abs(entry_price - stop_loss) / entry_price,
                'method': 'Support/Resistance'
            }
    
    def calculate_take_profit(self,
                            entry_price: float,
                            side: str,
                            stop_loss_price: float,
                            risk_reward_ratio: float = 2.0) -> Dict[str, Any]:
        """
        Calculate take profit levels based on risk/reward ratio
        
        Args:
            entry_price: Entry price
            side: 'buy' or 'sell'
            stop_loss_price: Stop loss price
            risk_reward_ratio: Target risk/reward ratio
            
        Returns:
            Dict with take profit information
        """
        
        risk_distance = abs(entry_price - stop_loss_price)
        reward_distance = risk_distance * risk_reward_ratio
        
        if side == 'buy':
            take_profit = entry_price + reward_distance
        else:
            take_profit = entry_price - reward_distance
            
        return {
            'take_profit_price': take_profit,
            'risk_distance': risk_distance,
            'reward_distance': reward_distance,
            'risk_reward_ratio': risk_reward_ratio,
            'expected_profit_percentage': reward_distance / entry_price
        }
    
    def update_portfolio_state(self, 
                              symbol: str,
                              side: str,
                              size: float,
                              price: float,
                              trade_type: str = 'open'):
        """
        Update portfolio state after trade execution
        
        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Position size
            price: Execution price
            trade_type: 'open' or 'close'
        """
        
        trade_value = size * price
        
        if trade_type == 'open':
            # Opening new position
            if symbol not in self.current_positions:
                self.current_positions[symbol] = {
                    'size': 0,
                    'average_price': 0,
                    'unrealized_pnl': 0
                }
            
            current_size = self.current_positions[symbol]['size']
            current_avg_price = self.current_positions[symbol]['average_price']
            
            if side == 'buy':
                new_size = current_size + size
                new_avg_price = ((current_size * current_avg_price) + trade_value) / new_size if new_size > 0 else price
            else:  # sell
                new_size = current_size - size
                if new_size != 0:
                    new_avg_price = current_avg_price  # Keep same average for partial close
                else:
                    new_avg_price = 0
                    
            self.current_positions[symbol]['size'] = new_size
            self.current_positions[symbol]['average_price'] = new_avg_price
            
        elif trade_type == 'close':
            # Closing position (partial or full)
            if symbol in self.current_positions:
                current_size = self.current_positions[symbol]['size']
                current_avg_price = self.current_positions[symbol]['average_price']
                
                if side == 'buy':
                    # Closing a short position
                    new_size = current_size + size
                else:  # sell
                    # Closing a long position
                    new_size = current_size - size
                
                # Update size
                self.current_positions[symbol]['size'] = new_size
                
                # If position is fully closed, reset average price
                if new_size == 0:
                    self.current_positions[symbol]['average_price'] = 0
                # For partial close, average price remains the same
                
        # Record trade
        trade_record = {
            'timestamp': datetime.now(),
            'symbol': symbol,
            'side': side,
            'size': size,
            'price': price,
            'value': trade_value,
            'type': trade_type
        }
        
        self.trade_history.append(trade_record)
        self.logger.info(f"Portfolio updated: {trade_record}")
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        
        total_value = self.portfolio_value
        total_exposure = sum(abs(pos['size'] * pos['average_price']) 
                           for pos in self.current_positions.values() 
                           if pos['size'] != 0)
        
        # Calculate unrealized P&L (simplified)
        total_unrealized_pnl = sum(pos['unrealized_pnl'] for pos in self.current_positions.values())
        
        # Risk metrics
        portfolio_heat = total_exposure / total_value if total_value > 0 else 0
        
        return {
            'total_value': total_value,
            'total_exposure': total_exposure,
            'portfolio_heat': portfolio_heat,
            'unrealized_pnl': total_unrealized_pnl,
            'open_positions': len([pos for pos in self.current_positions.values() if pos['size'] != 0]),
            'total_trades': len(self.trade_history),
            'risk_metrics': {
                'max_position_risk': self.max_position_risk,
                'max_portfolio_risk': self.max_portfolio_risk,
                'current_portfolio_risk': min(portfolio_heat, 1.0)
            }
        }
    
    # Private helper methods
    def _calculate_kelly_size(self, win_probability: float, market_data: pd.DataFrame) -> float:
        """Calculate Kelly Criterion position size"""
        if len(market_data) < 20:
            return self.portfolio_value * 0.02  # Fallback
            
        returns = market_data['close'].pct_change(fill_method=None).dropna()
        
        # Estimate win rate and average win/loss
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        if len(positive_returns) == 0 or len(negative_returns) == 0:
            return self.portfolio_value * 0.02
            
        avg_win = positive_returns.mean()
        avg_loss = abs(negative_returns.mean())
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds, p = win probability, q = loss probability
        if avg_loss == 0:
            return self.portfolio_value * 0.02
            
        b = avg_win / avg_loss  # odds
        p = win_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        kelly_fraction = np.clip(kelly_fraction, 0, 0.25)  # Cap at 25%
        
        return self.portfolio_value * kelly_fraction
    
    def _calculate_volatility_size(self, volatility: float) -> float:
        """Calculate position size based on volatility"""
        # Inverse relationship: higher volatility = smaller position
        target_volatility = 0.02  # 2% daily volatility target
        size_multiplier = min(target_volatility / max(volatility, 0.005), 1.0)
        
        return self.portfolio_value * self.max_position_risk * size_multiplier
    
    def _calculate_stop_loss_size(self, entry_price: float, stop_loss_price: float) -> float:
        """Calculate position size based on stop loss distance"""
        risk_per_share = abs(entry_price - stop_loss_price)
        if risk_per_share <= 0:
            return self.portfolio_value * 0.01  # Fallback
            
        max_risk_amount = self.portfolio_value * self.max_position_risk
        max_shares = max_risk_amount / risk_per_share
        
        return max_shares * entry_price
    
    def _calculate_volatility(self, market_data: pd.DataFrame, period: int = 20) -> float:
        """Calculate annualized volatility"""
        if len(market_data) < period:
            return 0.02  # Default 2% daily volatility
            
        returns = market_data['close'].pct_change(fill_method=None).tail(period)
        return returns.std() * np.sqrt(252)  # Annualized
    
    def _calculate_atr(self, market_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(market_data) < period + 1:
            return market_data['close'].iloc[-1] * 0.02  # 2% of price as fallback
            
        high = market_data['high']
        low = market_data['low']
        close = market_data['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(period).mean().iloc[-1]  # type: ignore
        
        return atr if not pd.isna(atr) else market_data['close'].iloc[-1] * 0.02
    
    def _calculate_portfolio_heat(self) -> float:
        """Calculate current portfolio heat (risk exposure)"""
        total_exposure = sum(abs(pos['size'] * pos['average_price']) 
                           for pos in self.current_positions.values() 
                           if pos['size'] != 0)
        
        return min(total_exposure / self.portfolio_value, 1.0) if self.portfolio_value > 0 else 0
    
    def _calculate_portfolio_risk(self, new_symbol: str, new_position_value: float) -> float:
        """Calculate total portfolio risk including new position"""
        current_exposure = sum(abs(pos['size'] * pos['average_price']) 
                              for pos in self.current_positions.values() 
                              if pos['size'] != 0)
        
        total_exposure = current_exposure + new_position_value
        return total_exposure / self.portfolio_value if self.portfolio_value > 0 else 0.0
    
    def _calculate_correlation_risk(self, symbol: str, market_data: pd.DataFrame) -> float:
        """Calculate correlation risk (simplified)"""
        # This would normally calculate correlation with existing positions
        # For now, return low risk
        return 0.3
    
    def _calculate_current_drawdown(self) -> float:
        """Calculate current portfolio drawdown"""
        # Simplified calculation - would need historical portfolio values
        return 0.0
    
    def _calculate_concentration_risk(self, symbol: str, new_position_value: float) -> float:
        """Calculate concentration risk in single asset"""
        current_position_value = 0
        if symbol in self.current_positions:
            pos = self.current_positions[symbol]
            current_position_value = abs(pos['size'] * pos['average_price'])
        
        total_position_value = current_position_value + new_position_value
        concentration = total_position_value / self.portfolio_value if self.portfolio_value > 0 else 0.0
        
        return min(concentration / self.max_concentration, 1.0) if self.max_concentration > 0 else 0.0
