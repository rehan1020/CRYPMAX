# analysis/enhanced_backtesting.py
"""
Enhanced Backtesting Framework for Cryptocurrency Trading Strategies

This module implements a comprehensive backtesting framework that:
1. Supports multiple trading strategies
2. Implements realistic transaction costs and slippage
3. Provides detailed performance metrics
4. Supports walk-forward optimization
5. Includes stress testing capabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Optional imports for plotting (won't crash if not available)
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

from strategies.working_strategy_manager import WorkingStrategyManager
from analysis.risk_management import EnhancedRiskManager

logger = logging.getLogger(__name__)

class TradeDirection(Enum):
    """Trade direction enumeration"""
    LONG = "long"
    SHORT = "short"

@dataclass
class BacktestTrade:
    """Represents a single trade in backtesting"""
    timestamp: datetime
    symbol: str
    direction: TradeDirection
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    profit_loss: float
    profit_loss_pct: float
    holding_period: timedelta
    strategy: str

@dataclass
class BacktestMetrics:
    """Backtesting performance metrics"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    avg_holding_period: timedelta
    largest_win: float
    largest_loss: float
    avg_trade_duration: timedelta
    volatility: float

class EnhancedBacktester:
    """Enhanced cryptocurrency trading strategy backtester"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize backtester
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            'initial_capital': 10000.0,
            'transaction_cost': 0.001,  # 0.1% per trade
            'slippage': 0.0005,         # 0.05% slippage
            'risk_free_rate': 0.02,     # 2% annual risk-free rate
            'short_selling_enabled': True,
            'leverage_enabled': False,
            'max_leverage': 1.0,        # No leverage by default
            'minimum_trade_size': 10.0, # Minimum $10 trades
            'walk_forward_periods': 3,   # Number of walk-forward periods
        }
        
        self.default_config.update(self.config)
        self.config = self.default_config
        
        # Components
        self.strategy_manager = WorkingStrategyManager()
        self.risk_manager = EnhancedRiskManager()
        
        # State
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.metrics: Optional[BacktestMetrics] = None
        
        logger.info("Enhanced Backtester initialized")

    def _ensure_datetime(self, ts):
        """Ensure timestamp is a datetime object, handling NaT and other edge cases"""
        try:
            # Handle None and NaT
            if ts is None:
                return datetime.now()
            # If it's already a datetime, return as is
            if isinstance(ts, datetime):
                return ts
            # Handle pandas objects
            if hasattr(ts, 'to_pydatetime'):
                # Check for NaT first
                try:
                    # Use a safer way to check for NaT
                    if str(ts) == 'NaT':
                        return datetime.now()
                except:
                    pass
                try:
                    result = ts.to_pydatetime()
                    # Double-check that result is a datetime
                    if isinstance(result, datetime):
                        return result
                except:
                    pass
            # Handle DatetimeIndex
            if hasattr(ts, '__getitem__') and hasattr(ts, '__len__'):
                try:
                    if len(ts) > 0:
                        first_item = ts[0]
                        if hasattr(first_item, 'to_pydatetime'):
                            try:
                                # Use a safer way to check for NaT
                                if str(first_item) == 'NaT':
                                    return datetime.now()
                            except:
                                pass
                            result = first_item.to_pydatetime()
                            if isinstance(result, datetime):
                                return result
                except:
                    pass
            # Fallback: try to convert via pandas Timestamp
            try:
                converted_ts = pd.Timestamp(ts)
                try:
                    # Use a safer way to check for NaT
                    if str(converted_ts) != 'NaT':
                        result = converted_ts.to_pydatetime()
                        if isinstance(result, datetime):
                            return result
                    else:
                        return datetime.now()
                except:
                    return datetime.now()
            except:
                # Last resort: convert to string and then to datetime
                try:
                    str_ts = str(ts)
                    if str_ts and str_ts != 'NaT':
                        return datetime.fromisoformat(str_ts)
                except:
                    return datetime.now()
        except:
            pass
        # Final fallback
        result = datetime.now()
        # Ensure we return a datetime object
        if isinstance(result, datetime):
            return result
        else:
            return datetime.now()

    async def run_backtest(self, 
                          strategy_func: Callable,
                          data: pd.DataFrame,
                          symbol: str,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          **strategy_params) -> Dict[str, Any]:
        """
        Run backtest for a strategy on historical data
        
        Args:
            strategy_func: Strategy function to test
            data: Historical market data (OHLCV)
            symbol: Trading symbol
            start_date: Start date for backtest
            end_date: End date for backtest
            **strategy_params: Additional strategy parameters
            
        Returns:
            Dictionary with backtest results
        """
        try:
            # Filter data by date range
            if start_date:
                data = data[data.index >= start_date]  # type: ignore
            if end_date:
                data = data[data.index <= end_date]  # type: ignore
                
            if data.empty:
                raise ValueError("No data available for backtest period")
            
            # Initialize state
            capital = self.config['initial_capital']
            position = 0.0
            position_value = 0.0
            entry_price = 0.0
            entry_time = None
            in_position = False
            direction = TradeDirection.LONG
            
            # Reset trades and equity curve
            self.trades = []
            first_timestamp = self._ensure_datetime(pd.to_datetime(data.index[0]))
            self.equity_curve = [(first_timestamp, capital)]
            
            # Run strategy on each bar
            for i in range(1, len(data)):
                current_time = data.index[i]
                current_price = float(data['close'].iloc[i])
                previous_price = float(data['close'].iloc[i-1])
                
                # Update equity curve
                if in_position:
                    # Calculate current position value
                    if direction == TradeDirection.LONG:
                        position_value = position * current_price
                    else:
                        # For short positions: profit = (entry_price - current_price) * quantity
                        position_value = position * entry_price + position * (entry_price - current_price)
                    
                    current_equity = capital + position_value
                else:
                    current_equity = capital
                    
                # Fix timestamp conversion - convert to datetime
                current_timestamp = self._ensure_datetime(pd.to_datetime(current_time))
                self.equity_curve.append((current_timestamp, current_equity))
                
                # Get strategy decision
                if hasattr(strategy_func, '__call__'):
                    # If it's a custom strategy function
                    decision = strategy_func(data.iloc[:i+1], **strategy_params)
                else:
                    # If it's using the strategy manager
                    decision, _ = self.strategy_manager.decide(data.iloc[:i+1], symbol)
                
                # Execute trades based on decision
                if decision == 'BUY' and not in_position:
                    # Enter long position
                    if self._can_enter_trade(current_equity, current_price):
                        position, capital = self._enter_long(current_price, capital, current_timestamp)
                        entry_price = current_price
                        entry_time = current_time
                        in_position = True
                        direction = TradeDirection.LONG
                        
                elif decision == 'SELL' and not in_position and self.config['short_selling_enabled']:
                    # Enter short position
                    if self._can_enter_trade(current_equity, current_price):
                        position, capital = self._enter_short(current_price, capital, current_timestamp)
                        entry_price = current_price
                        entry_time = current_time
                        in_position = True
                        direction = TradeDirection.SHORT
                        
                elif decision == 'SELL' and in_position and direction == TradeDirection.LONG:
                    # Exit long position
                    # Fix timestamp conversion for exit - convert to datetime
                    exit_timestamp = current_timestamp
                    entry_timestamp = exit_timestamp
                    if entry_time is not None:
                        entry_timestamp = self._ensure_datetime(pd.to_datetime(entry_time))
                    capital = self._exit_long(position, entry_price, current_price, capital, 
                                            entry_timestamp, exit_timestamp, symbol, strategy_func.__name__ if hasattr(strategy_func, '__name__') else 'unknown_strategy')
                    position = 0.0
                    in_position = False
                    
                elif decision == 'BUY' and in_position and direction == TradeDirection.SHORT:
                    # Exit short position
                    # Fix timestamp conversion for exit - convert to datetime
                    exit_timestamp = current_timestamp
                    entry_timestamp = exit_timestamp
                    if entry_time is not None:
                        entry_timestamp = self._ensure_datetime(pd.to_datetime(entry_time))
                    capital = self._exit_short(position, entry_price, current_price, capital,
                                             entry_timestamp, exit_timestamp, symbol, strategy_func.__name__ if hasattr(strategy_func, '__name__') else 'unknown_strategy')
                    position = 0.0
                    in_position = False
            
            # Close any open positions at the end
            if in_position:
                # Make sure we have a current_price
                current_price = float(data['close'].iloc[-1])
                # Fix timestamp conversion for final exit - convert to datetime
                final_timestamp = self._ensure_datetime(pd.to_datetime(data.index[-1]))
                entry_timestamp = final_timestamp
                if entry_time is not None:
                    entry_timestamp = self._ensure_datetime(pd.to_datetime(entry_time))
                if direction == TradeDirection.LONG:
                    capital = self._exit_long(position, entry_price, current_price, capital,
                                            entry_timestamp, final_timestamp, symbol, strategy_func.__name__ if hasattr(strategy_func, '__name__') else 'unknown_strategy')
                else:
                    capital = self._exit_short(position, entry_price, current_price, capital,
                                             entry_timestamp, final_timestamp, symbol, strategy_func.__name__ if hasattr(strategy_func, '__name__') else 'unknown_strategy')
            
            # Calculate metrics
            self.metrics = self._calculate_metrics()
            
            # Generate results
            start_date_ts = self._ensure_datetime(pd.to_datetime(data.index[0]))
            end_date_ts = self._ensure_datetime(pd.to_datetime(data.index[-1]))
                
            # Convert to ISO format strings
            start_date_str = start_date_ts.isoformat() if hasattr(start_date_ts, 'isoformat') else str(start_date_ts)
            end_date_str = end_date_ts.isoformat() if hasattr(end_date_ts, 'isoformat') else str(end_date_ts)
            results = {
                'symbol': symbol,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'initial_capital': self.config['initial_capital'],
                'final_capital': capital,
                'total_return': capital - self.config['initial_capital'],
                'total_return_pct': ((capital / self.config['initial_capital']) - 1) * 100,
                'metrics': asdict(self.metrics) if self.metrics else {},
                'trades': len(self.trades),
                'equity_curve': [(t.isoformat() if hasattr(t, 'isoformat') else str(t), v) for t, v in self.equity_curve],
                'config': self.config
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {
                'error': str(e),
                'symbol': symbol,
                'initial_capital': self.config['initial_capital'],
                'final_capital': self.config['initial_capital'],  # No change
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'metrics': {},
                'trades': 0,
                'equity_curve': []
            }

    def _can_enter_trade(self, equity: float, price: float) -> bool:
        """
        Check if a trade can be entered
        
        Args:
            equity: Current equity
            price: Current price
            
        Returns:
            Boolean indicating if trade can be entered
        """
        # Check minimum trade size
        if price <= 0:
            return False
            
        min_quantity = self.config['minimum_trade_size'] / price
        min_trade_value = min_quantity * price * (1 + self.config['transaction_cost'])
        
        return equity >= min_trade_value

    def _enter_long(self, price: float, capital: float, timestamp: datetime) -> Tuple[float, float]:
        """
        Enter long position
        
        Args:
            price: Entry price
            capital: Available capital
            timestamp: Entry timestamp
            
        Returns:
            Tuple of (position_size, remaining_capital)
        """
        # Apply slippage
        entry_price = price * (1 + self.config['slippage'])
        
        # Calculate position size (use all available capital)
        position_value = capital
        transaction_cost = position_value * self.config['transaction_cost']
        position_size = (position_value - transaction_cost) / entry_price
        
        # Update capital
        remaining_capital = capital - position_value
        
        return position_size, remaining_capital

    def _enter_short(self, price: float, capital: float, timestamp: datetime) -> Tuple[float, float]:
        """
        Enter short position
        
        Args:
            price: Entry price
            capital: Available capital
            timestamp: Entry timestamp
            
        Returns:
            Tuple of (position_size, remaining_capital)
        """
        # Apply slippage
        entry_price = price * (1 - self.config['slippage'])
        
        # Calculate position size (use all available capital)
        position_value = capital
        transaction_cost = position_value * self.config['transaction_cost']
        position_size = (position_value - transaction_cost) / entry_price
        
        # Update capital (for short selling, we don't receive cash upfront)
        remaining_capital = capital - transaction_cost
        
        return position_size, remaining_capital

    def _exit_long(self, position: float, entry_price: float, exit_price: float,
                   capital: float, entry_time: datetime, exit_time: datetime,
                   symbol: str, strategy_name: str) -> float:
        """
        Exit long position
        
        Args:
            position: Position size
            entry_price: Entry price
            exit_price: Exit price
            capital: Available capital
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            symbol: Trading symbol
            strategy_name: Strategy name
            
        Returns:
            Updated capital
        """
        # Apply slippage
        actual_exit_price = exit_price * (1 - self.config['slippage'])
        
        # Calculate profit/loss
        entry_value = position * entry_price
        exit_value = position * actual_exit_price
        gross_pnl = exit_value - entry_value
        
        # Transaction costs for exit
        exit_cost = exit_value * self.config['transaction_cost']
        
        # Update capital
        updated_capital = capital + exit_value - exit_cost
        
        # Record trade
        trade = BacktestTrade(
            timestamp=self._ensure_datetime(exit_time),
            symbol=symbol,
            direction=TradeDirection.LONG,
            entry_price=entry_price,
            exit_price=actual_exit_price,
            quantity=position,
            entry_time=self._ensure_datetime(entry_time) if entry_time else self._ensure_datetime(exit_time),
            exit_time=self._ensure_datetime(exit_time),
            profit_loss=gross_pnl - exit_cost,
            profit_loss_pct=(actual_exit_price / entry_price - 1) * 100,
            holding_period=self._ensure_datetime(exit_time) - self._ensure_datetime(entry_time) if entry_time else timedelta(),
            strategy=strategy_name
        )
        
        self.trades.append(trade)
        
        return updated_capital

    def _exit_short(self, position: float, entry_price: float, exit_price: float,
                    capital: float, entry_time: datetime, exit_time: datetime,
                    symbol: str, strategy_name: str) -> float:
        """
        Exit short position
        
        Args:
            position: Position size
            entry_price: Entry price
            exit_price: Exit price
            capital: Available capital
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            symbol: Trading symbol
            strategy_name: Strategy name
            
        Returns:
            Updated capital
        """
        # Apply slippage
        actual_exit_price = exit_price * (1 + self.config['slippage'])
        
        # Calculate profit/loss for short position
        # Profit = (entry_price - exit_price) * quantity
        gross_pnl = position * (entry_price - actual_exit_price)
        
        # Transaction costs for exit
        exit_cost = position * actual_exit_price * self.config['transaction_cost']
        
        # Update capital
        updated_capital = capital + gross_pnl - exit_cost
        
        # Record trade
        trade = BacktestTrade(
            timestamp=self._ensure_datetime(exit_time),
            symbol=symbol,
            direction=TradeDirection.SHORT,
            entry_price=entry_price,
            exit_price=actual_exit_price,
            quantity=position,
            entry_time=self._ensure_datetime(entry_time) if entry_time else self._ensure_datetime(exit_time),
            exit_time=self._ensure_datetime(exit_time),
            profit_loss=gross_pnl - exit_cost,
            profit_loss_pct=((entry_price / actual_exit_price) - 1) * 100,
            holding_period=self._ensure_datetime(exit_time) - self._ensure_datetime(entry_time) if entry_time else timedelta(),
            strategy=strategy_name
        )
        
        self.trades.append(trade)
        
        return updated_capital

    def _calculate_metrics(self) -> BacktestMetrics:
        """
        Calculate comprehensive backtesting metrics
        
        Returns:
            BacktestMetrics object
        """
        try:
            if not self.trades:
                return BacktestMetrics(
                    total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                    total_pnl=0.0, total_pnl_pct=0.0, average_win=0.0, average_loss=0.0,
                    profit_factor=0.0, max_drawdown=0.0, max_drawdown_pct=0.0,
                    sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
                    avg_holding_period=timedelta(), largest_win=0.0, largest_loss=0.0,
                    avg_trade_duration=timedelta(), volatility=0.0
                )
            
            # Basic trade statistics
            total_trades = len(self.trades)
            winning_trades = len([t for t in self.trades if t.profit_loss > 0])
            losing_trades = total_trades - winning_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
            
            # Profit/Loss calculations
            profits = [t.profit_loss for t in self.trades if t.profit_loss > 0]
            losses = [abs(t.profit_loss) for t in self.trades if t.profit_loss < 0]
            
            total_pnl = sum(t.profit_loss for t in self.trades)
            total_pnl_pct = (total_pnl / self.config['initial_capital']) * 100
            
            average_win = np.mean(profits) if profits else 0.0
            average_loss = np.mean(losses) if losses else 0.0
            
            # Profit factor
            total_wins = sum(profits)
            total_losses = sum(losses)
            profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
            
            # Drawdown calculations
            max_drawdown, max_drawdown_pct = self._calculate_max_drawdown()
            
            # Risk-adjusted returns
            sharpe_ratio = self._calculate_sharpe_ratio()
            sortino_ratio = self._calculate_sortino_ratio()
            calmar_ratio = total_pnl_pct / abs(max_drawdown_pct) if max_drawdown_pct < 0 else 0.0
            
            # Time-based metrics
            holding_periods = [float(t.holding_period.total_seconds()) for t in self.trades]
            avg_holding_period = timedelta(seconds=float(np.mean(holding_periods))) if holding_periods else timedelta()
            
            largest_win = float(max(profits)) if profits else 0.0
            largest_loss = float(max(losses)) if losses else 0.0
            
            trade_durations = [float(t.holding_period.total_seconds()) for t in self.trades]
            avg_trade_duration = timedelta(seconds=float(np.mean(trade_durations))) if trade_durations else timedelta()
            
            # Volatility
            returns = [float(t.profit_loss_pct / 100) for t in self.trades]
            volatility = float(np.std(returns) * np.sqrt(252)) if returns else 0.0  # Annualized
            
            return BacktestMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=float(win_rate),
                total_pnl=float(total_pnl),
                total_pnl_pct=float(total_pnl_pct),
                average_win=float(average_win) if not np.isnan(average_win) and not isinstance(average_win, np.floating) else float(average_win) if isinstance(average_win, np.floating) else 0.0,
                average_loss=float(average_loss) if not np.isnan(average_loss) and not isinstance(average_loss, np.floating) else float(average_loss) if isinstance(average_loss, np.floating) else 0.0,
                profit_factor=float(profit_factor) if not np.isinf(profit_factor) and not np.isnan(profit_factor) else 0.0,
                max_drawdown=float(max_drawdown),
                max_drawdown_pct=float(max_drawdown_pct),
                sharpe_ratio=float(sharpe_ratio) if not np.isnan(sharpe_ratio) else 0.0,
                sortino_ratio=float(sortino_ratio) if not np.isnan(sortino_ratio) else 0.0,
                calmar_ratio=float(calmar_ratio) if not np.isnan(calmar_ratio) else 0.0,
                avg_holding_period=avg_holding_period,
                largest_win=float(largest_win),
                largest_loss=float(largest_loss),
                avg_trade_duration=avg_trade_duration,
                volatility=float(volatility)
            )
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
                total_pnl=0.0, total_pnl_pct=0.0, average_win=0.0, average_loss=0.0,
                profit_factor=0.0, max_drawdown=0.0, max_drawdown_pct=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0, calmar_ratio=0.0,
                avg_holding_period=timedelta(), largest_win=0.0, largest_loss=0.0,
                avg_trade_duration=timedelta(), volatility=0.0
            )

    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """
        Calculate maximum drawdown
        
        Returns:
            Tuple of (max_drawdown_amount, max_drawdown_percentage)
        """
        try:
            if not self.equity_curve:
                return 0.0, 0.0
                
            equity_values = [v for t, v in self.equity_curve]
            running_max = np.maximum.accumulate(equity_values)
            drawdown = (equity_values - running_max) / running_max
            max_drawdown_idx = np.argmin(drawdown)
            max_drawdown_pct = drawdown[max_drawdown_idx] * 100
            max_drawdown_amount = equity_values[max_drawdown_idx] - running_max[max_drawdown_idx]
            
            return max_drawdown_amount, max_drawdown_pct
            
        except Exception as e:
            logger.warning(f"Error calculating max drawdown: {e}")
            return 0.0, 0.0

    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate Sharpe ratio
        
        Returns:
            Sharpe ratio
        """
        try:
            if not self.trades or len(self.trades) < 2:
                return 0.0
                
            returns = [t.profit_loss_pct / 100 for t in self.trades]
            if not returns:
                return 0.0
                
            # Calculate excess returns (above risk-free rate)
            risk_free_rate_daily = self.config['risk_free_rate'] / 252  # Daily risk-free rate
            excess_returns = [r - risk_free_rate_daily for r in returns]
            
            # Calculate Sharpe ratio
            mean_excess_return = np.mean(excess_returns)
            std_excess_return = np.std(excess_returns)
            
            if std_excess_return == 0:
                return 0.0
                
            sharpe_ratio = mean_excess_return / std_excess_return * np.sqrt(252)  # Annualized
            return sharpe_ratio
            
        except Exception as e:
            logger.warning(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    def _calculate_sortino_ratio(self) -> float:
        """
        Calculate Sortino ratio
        
        Returns:
            Sortino ratio
        """
        try:
            if not self.trades or len(self.trades) < 2:
                return 0.0
                
            returns = [t.profit_loss_pct / 100 for t in self.trades]
            if not returns:
                return 0.0
                
            # Calculate downside deviation
            risk_free_rate_daily = self.config['risk_free_rate'] / 252
            negative_returns = [min(0, r - risk_free_rate_daily) for r in returns]
            downside_deviation = np.std(negative_returns)
            
            if downside_deviation == 0:
                return 0.0
                
            # Calculate Sortino ratio
            mean_return = np.mean(returns)
            excess_return = mean_return - risk_free_rate_daily
            sortino_ratio = (excess_return / downside_deviation) * np.sqrt(252)  # Annualized
            return sortino_ratio
            
        except Exception as e:
            logger.warning(f"Error calculating Sortino ratio: {e}")
            return 0.0

    async def run_walk_forward_optimization(self, 
                                    strategy_func: Callable,
                                    data: pd.DataFrame,
                                    symbol: str,
                                    optimization_params: Dict[str, Any],
                                    **fixed_params) -> Dict[str, Any]:
        """
        Run walk-forward optimization
        
        Args:
            strategy_func: Strategy function to optimize
            data: Historical market data
            symbol: Trading symbol
            optimization_params: Parameters to optimize
            **fixed_params: Fixed strategy parameters
            
        Returns:
            Dictionary with optimization results
        """
        try:
            # Split data into periods
            n_periods = self.config['walk_forward_periods']
            period_length = len(data) // n_periods
            
            results = []
            best_params = {}
            best_performance = float('-inf')
            
            for i in range(n_periods - 1):  # Use all but last period for optimization
                # Training period
                train_start = i * period_length
                train_end = (i + 1) * period_length
                train_data = data.iloc[train_start:train_end]
                
                # Optimization period
                opt_start = train_end
                opt_end = min((i + 2) * period_length, len(data))
                opt_data = data.iloc[opt_start:opt_end]
                
                # Optimize parameters on training data
                optimized_params = self._optimize_parameters(
                    strategy_func, train_data, symbol, optimization_params, **fixed_params
                )
                
                # Test optimized parameters on optimization period
                test_result = await self.run_backtest(
                    strategy_func, opt_data, symbol, **{**fixed_params, **optimized_params}
                )
                
                results.append({
                    'period': i,
                    'optimized_params': optimized_params,
                    'performance': test_result['total_return_pct'],
                    'metrics': test_result['metrics']
                })
                
                # Track best parameters
                if test_result['total_return_pct'] > best_performance:
                    best_performance = test_result['total_return_pct']
                    best_params = optimized_params
            
            # Test best parameters on out-of-sample data (last period)
            oos_start = (n_periods - 1) * period_length
            oos_data = data.iloc[oos_start:]
            oos_result = await self.run_backtest(
                strategy_func, oos_data, symbol, **{**fixed_params, **best_params}
            )
            
            return {
                'walk_forward_results': results,
                'out_of_sample_result': oos_result,
                'best_params': best_params,
                'best_performance': best_performance
            }
            
        except Exception as e:
            logger.error(f"Error running walk-forward optimization: {e}")
            return {'error': str(e)}

    def _optimize_parameters(self, 
                           strategy_func: Callable,
                           data: pd.DataFrame,
                           symbol: str,
                           optimization_params: Dict[str, Any],
                           **fixed_params) -> Dict[str, Any]:
        """
        Optimize strategy parameters (simplified grid search)
        
        Args:
            strategy_func: Strategy function to optimize
            data: Historical market data
            symbol: Trading symbol
            optimization_params: Parameters to optimize
            **fixed_params: Fixed strategy parameters
            
        Returns:
            Dictionary with optimized parameters
        """
        # This is a simplified implementation
        # In practice, you would use more sophisticated optimization techniques
        return optimization_params  # Return as-is for now

    def generate_report(self, backtest_results: Dict[str, Any]) -> str:
        """
        Generate detailed backtest report
        
        Args:
            backtest_results: Backtest results dictionary
            
        Returns:
            Formatted report string
        """
        try:
            report = []
            report.append("=" * 60)
            report.append("CRYPTOCURRENCY TRADING STRATEGY BACKTEST REPORT")
            report.append("=" * 60)
            report.append("")
            
            # Basic information
            report.append(f"Symbol: {backtest_results.get('symbol', 'N/A')}")
            report.append(f"Period: {backtest_results.get('start_date', 'N/A')} to {backtest_results.get('end_date', 'N/A')}")
            report.append(f"Initial Capital: ${backtest_results.get('initial_capital', 0):,.2f}")
            report.append(f"Final Capital: ${backtest_results.get('final_capital', 0):,.2f}")
            report.append(f"Total Return: ${backtest_results.get('total_return', 0):,.2f} ({backtest_results.get('total_return_pct', 0):.2f}%)")
            report.append("")
            
            # Performance metrics
            metrics = backtest_results.get('metrics', {})
            if metrics:
                report.append("PERFORMANCE METRICS")
                report.append("-" * 30)
                report.append(f"Total Trades: {metrics.get('total_trades', 0)}")
                report.append(f"Win Rate: {metrics.get('win_rate', 0) * 100:.2f}%")
                report.append(f"Average Win: ${metrics.get('average_win', 0):,.2f}")
                report.append(f"Average Loss: ${metrics.get('average_loss', 0):,.2f}")
                report.append(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
                report.append(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
                report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                report.append(f"Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
                report.append("")
            
            # Risk metrics
            report.append("RISK METRICS")
            report.append("-" * 30)
            report.append(f"Volatility: {metrics.get('volatility', 0) * 100:.2f}%")
            report.append(f"Largest Win: ${metrics.get('largest_win', 0):,.2f}")
            report.append(f"Largest Loss: ${metrics.get('largest_loss', 0):,.2f}")
            report.append(f"Avg Holding Period: {metrics.get('avg_holding_period', '0s')}")
            report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"

    def plot_equity_curve(self, backtest_results: Dict[str, Any], filename: Optional[str] = None):
        """
        Plot equity curve
        
        Args:
            backtest_results: Backtest results dictionary
            filename: Output filename (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available for plotting")
            return
            
        try:
            equity_curve = backtest_results.get('equity_curve', [])
            if not equity_curve:
                logger.warning("No equity curve data to plot")
                return
                
            # Convert to DataFrame for easier plotting
            timestamps = [datetime.fromisoformat(t) for t, v in equity_curve]
            values = [v for t, v in equity_curve]
            
            df = pd.DataFrame({'timestamp': timestamps, 'equity': values})
            df.set_index('timestamp', inplace=True)
            
            # Create plot
            if plt is not None:
                plt.figure(figsize=(12, 6))
                plt.plot(df.index, df['equity'])
                plt.title('Strategy Equity Curve')
                plt.xlabel('Date')
                plt.ylabel('Equity ($)')
                plt.grid(True)
                
                if filename:
                    plt.savefig(filename, dpi=300, bbox_inches='tight')
                    plt.close()
                else:
                    plt.show()
                
        except Exception as e:
            logger.error(f"Error plotting equity curve: {e}")

    def plot_trade_analysis(self, filename: Optional[str] = None):
        """
        Plot trade analysis charts
        
        Args:
            filename: Output filename (optional)
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available for plotting")
            return
            
        try:
            if not self.trades:
                logger.warning("No trades to analyze")
                return
                
            # Convert trades to DataFrame
            trade_data = []
            for trade in self.trades:
                trade_data.append({
                    'profit_loss': trade.profit_loss,
                    'holding_period': trade.holding_period.total_seconds() / 3600,  # Hours
                    'direction': trade.direction.value
                })
                
            df = pd.DataFrame(trade_data)
            
            # Create subplots
            if plt is not None:
                fig, axes = plt.subplots(2, 2, figsize=(15, 10))
                
                # Profit/Loss distribution
                axes[0, 0].hist(df['profit_loss'], bins=30, alpha=0.7, color='blue')
                axes[0, 0].set_title('Profit/Loss Distribution')
                axes[0, 0].set_xlabel('Profit/Loss ($)')
                axes[0, 0].set_ylabel('Frequency')
                
                # Holding period distribution
                axes[0, 1].hist(df['holding_period'], bins=30, alpha=0.7, color='green')
                axes[0, 1].set_title('Holding Period Distribution')
                axes[0, 1].set_xlabel('Holding Period (Hours)')
                axes[0, 1].set_ylabel('Frequency')
                
                # Profit/Loss by direction
                df.boxplot(column='profit_loss', by='direction', ax=axes[1, 0])
                axes[1, 0].set_title('Profit/Loss by Trade Direction')
                axes[1, 0].set_xlabel('Direction')
                axes[1, 0].set_ylabel('Profit/Loss ($)')
                
                # Cumulative profits
                cumulative_profits = np.cumsum([t.profit_loss for t in self.trades])
                axes[1, 1].plot(cumulative_profits)
                axes[1, 1].set_title('Cumulative Profits')
                axes[1, 1].set_xlabel('Trade Number')
                axes[1, 1].set_ylabel('Cumulative Profit ($)')
                
                plt.tight_layout()
                
                if filename:
                    plt.savefig(filename, dpi=300, bbox_inches='tight')
                    plt.close()
                else:
                    plt.show()
                
        except Exception as e:
            logger.error(f"Error plotting trade analysis: {e}")