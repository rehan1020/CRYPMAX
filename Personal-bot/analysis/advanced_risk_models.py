# analysis/advanced_risk_models.py
"""
Advanced Risk Models for Cryptocurrency Trading

This module implements sophisticated risk models that:
1. Dynamic position sizing based on market conditions
2. Portfolio optimization using Modern Portfolio Theory
3. Value at Risk (VaR) calculations
4. Stress testing and scenario analysis
5. Tail risk management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from scipy import stats
from scipy.optimize import minimize

from analysis.risk_management import EnhancedRiskManager, RiskMetrics, RiskLevel

logger = logging.getLogger(__name__)

@dataclass
class VaRResult:
    """Value at Risk calculation result"""
    var_95: float  # 95% confidence level
    var_99: float  # 99% confidence level
    expected_shortfall: float  # Expected shortfall (CVaR)
    time_horizon: int  # Time horizon in days
    confidence_level: float

@dataclass
class PortfolioOptimizationResult:
    """Portfolio optimization result"""
    optimal_weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    efficient_frontier: List[Dict[str, float]]

@dataclass
class StressTestResult:
    """Stress test result"""
    scenario_name: str
    impact_on_portfolio: float  # Percentage impact
    affected_assets: List[str]
    recovery_time: int  # Days to recover
    risk_mitigation_required: bool

class AdvancedRiskModels:
    """Advanced risk models for cryptocurrency trading"""
    
    def __init__(self, risk_manager: EnhancedRiskManager, config: Optional[Dict[str, Any]] = None):
        """
        Initialize advanced risk models
        
        Args:
            risk_manager: EnhancedRiskManager instance
            config: Configuration dictionary
        """
        self.risk_manager = risk_manager
        self.config = config or {}
        
        # Default configuration
        self.default_config = {
            'var_confidence_levels': [0.95, 0.99],
            'var_time_horizon': 1,  # 1 day
            'stress_test_scenarios': [
                'market_crash_10',
                'market_crash_20',
                'flash_crash',
                'regulatory_event',
                'exchange_hack'
            ],
            'correlation_window': 30,  # 30 days
            'optimization_risk_free_rate': 0.02,  # 2% annual
            'tail_risk_threshold': 0.05,  # 5% tail risk
        }
        
        self.default_config.update(self.config)
        self.config = self.default_config
        
        logger.info("Advanced Risk Models initialized")

    def calculate_value_at_risk(self, 
                              returns_data: pd.DataFrame,
                              confidence_levels: Optional[List[float]] = None,
                              time_horizon: int = 1) -> VaRResult:
        """
        Calculate Value at Risk using multiple methods
        
        Args:
            returns_data: DataFrame with historical returns
            confidence_levels: List of confidence levels (default: [0.95, 0.99])
            time_horizon: Time horizon in days
            
        Returns:
            VaRResult object
        """
        try:
            if confidence_levels is None:
                confidence_levels = self.config['var_confidence_levels']
                
            # Historical simulation method
            hist_var_95 = self._calculate_historical_var(returns_data, 0.95)
            hist_var_99 = self._calculate_historical_var(returns_data, 0.99)
            
            # Parametric method (assuming normal distribution)
            param_var_95 = self._calculate_parametric_var(returns_data, 0.95)
            param_var_99 = self._calculate_parametric_var(returns_data, 0.99)
            
            # Monte Carlo simulation method
            mc_var_95 = self._calculate_monte_carlo_var(returns_data, 0.95)
            mc_var_99 = self._calculate_monte_carlo_var(returns_data, 0.99)
            
            # Use average of methods for more robust estimate
            var_95 = np.mean([hist_var_95, param_var_95, mc_var_95])
            var_99 = np.mean([hist_var_99, param_var_99, mc_var_99])
            
            # Calculate Expected Shortfall (Conditional VaR)
            expected_shortfall = self._calculate_expected_shortfall(returns_data, 0.95)
            
            # Scale for time horizon
            var_95 = var_95 * np.sqrt(time_horizon)
            var_99 = var_99 * np.sqrt(time_horizon)
            expected_shortfall = expected_shortfall * np.sqrt(time_horizon)
            
            return VaRResult(
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                time_horizon=time_horizon,
                confidence_level=0.95
            )
            
        except Exception as e:
            logger.error(f"Error calculating Value at Risk: {e}")
            # Return conservative estimates
            return VaRResult(
                var_95=0.10,  # 10% loss at 95% confidence
                var_99=0.20,  # 20% loss at 99% confidence
                expected_shortfall=0.15,
                time_horizon=time_horizon,
                confidence_level=0.95
            )

    def _calculate_historical_var(self, returns_data: pd.DataFrame, confidence_level: float) -> float:
        """
        Calculate VaR using historical simulation method
        
        Args:
            returns_data: DataFrame with historical returns
            confidence_level: Confidence level (e.g., 0.95)
            
        Returns:
            VaR value
        """
        try:
            if returns_data.empty:
                return 0.0
                
            # Get returns column (assuming single asset)
            returns = returns_data.iloc[:, 0] if len(returns_data.columns) == 1 else returns_data.mean(axis=1)
            
            # Calculate percentile
            var = np.percentile(returns, (1 - confidence_level) * 100)
            return float(abs(var))  # Return positive value for loss
            
        except Exception as e:
            logger.warning(f"Error in historical VaR calculation: {e}")
            return 0.05  # Conservative fallback

    def _calculate_parametric_var(self, returns_data: pd.DataFrame, confidence_level: float) -> float:
        """
        Calculate VaR using parametric method (normal distribution)
        
        Args:
            returns_data: DataFrame with historical returns
            confidence_level: Confidence level (e.g., 0.95)
            
        Returns:
            VaR value
        """
        try:
            if returns_data.empty:
                return 0.0
                
            # Get returns column
            returns = returns_data.iloc[:, 0] if len(returns_data.columns) == 1 else returns_data.mean(axis=1)
            
            # Calculate mean and standard deviation
            mean_return = np.mean(returns)
            std_dev = np.std(returns)
            
            # Calculate VaR using normal distribution
            z_score = stats.norm.ppf(1 - confidence_level)
            var = mean_return - (z_score * std_dev)
            return float(abs(var))  # Return positive value for loss
            
        except Exception as e:
            logger.warning(f"Error in parametric VaR calculation: {e}")
            return 0.05  # Conservative fallback

    def _calculate_monte_carlo_var(self, returns_data: pd.DataFrame, confidence_level: float, 
                                 simulations: int = 10000) -> float:
        """
        Calculate VaR using Monte Carlo simulation
        
        Args:
            returns_data: DataFrame with historical returns
            confidence_level: Confidence level (e.g., 0.95)
            simulations: Number of simulations
            
        Returns:
            VaR value
        """
        try:
            if returns_data.empty:
                return 0.0
                
            # Get returns column
            returns = returns_data.iloc[:, 0] if len(returns_data.columns) == 1 else returns_data.mean(axis=1)
            
            # Calculate parameters
            mean_return = np.mean(returns)
            std_dev = np.std(returns)
            
            # Generate random returns
            simulated_returns = np.random.normal(mean_return, std_dev, simulations)
            
            # Calculate VaR
            var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
            return float(abs(var))  # Return positive value for loss
            
        except Exception as e:
            logger.warning(f"Error in Monte Carlo VaR calculation: {e}")
            return 0.05  # Conservative fallback

    def _calculate_expected_shortfall(self, returns_data: pd.DataFrame, confidence_level: float) -> float:
        """
        Calculate Expected Shortfall (Conditional VaR)
        
        Args:
            returns_data: DataFrame with historical returns
            confidence_level: Confidence level (e.g., 0.95)
            
        Returns:
            Expected Shortfall value
        """
        try:
            if returns_data.empty:
                return 0.0
                
            # Get returns column
            if isinstance(returns_data, pd.DataFrame):
                returns = returns_data.iloc[:, 0] if len(returns_data.columns) == 1 else returns_data.mean(axis=1)
            else:
                returns = returns_data
                
            # Ensure returns is a pandas Series
            if not isinstance(returns, pd.Series):
                returns = pd.Series(returns)
            
            # Calculate VaR threshold
            var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
            
            # Calculate average of returns below VaR threshold
            tail_losses = returns[returns <= var_threshold]
            if len(tail_losses) > 0:
                expected_shortfall = np.mean(tail_losses)
                return float(abs(expected_shortfall))  # Return positive value for loss
            else:
                return float(abs(var_threshold))  # Fallback to VaR
                
        except Exception as e:
            logger.warning(f"Error in Expected Shortfall calculation: {e}")
            return 0.07  # Conservative fallback

    def optimize_portfolio(self, 
                          returns_data: pd.DataFrame,
                          symbols: List[str],
                          risk_free_rate: Optional[float] = None) -> PortfolioOptimizationResult:
        """
        Optimize portfolio using Modern Portfolio Theory
        
        Args:
            returns_data: DataFrame with historical returns for multiple assets
            symbols: List of asset symbols
            risk_free_rate: Risk-free rate (default from config)
            
        Returns:
            PortfolioOptimizationResult object
        """
        try:
            if risk_free_rate is None:
                risk_free_rate = self.config['optimization_risk_free_rate']
                
            if returns_data.empty or len(symbols) == 0:
                return PortfolioOptimizationResult(
                    optimal_weights={},
                    expected_return=0.0,
                    expected_volatility=0.0,
                    sharpe_ratio=0.0,
                    efficient_frontier=[]
                )
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns_data.mean()
            cov_matrix = returns_data.cov()
            
            # Number of assets
            n_assets = len(symbols)
            
            # Constraints: weights sum to 1
            constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
            
            # Bounds: weights between 0 and 1 (long-only)
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess: equal weights
            initial_weights = np.array([1/n_assets] * n_assets)
            
            # Optimize for maximum Sharpe ratio
            def negative_sharpe(weights):
                portfolio_return = np.sum(expected_returns * weights)
                portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                if portfolio_volatility > 0 and risk_free_rate is not None:
                    sharpe_ratio = (portfolio_return - risk_free_rate/252) / portfolio_volatility  # Daily risk-free rate
                else:
                    sharpe_ratio = 0.0
                return -sharpe_ratio  # Negative because we want to maximize
            
            # Perform optimization
            result = minimize(negative_sharpe, initial_weights, method='SLSQP', 
                            bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_weights = result.x
                portfolio_return = np.sum(expected_returns * optimal_weights)
                portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                if portfolio_volatility > 0 and risk_free_rate is not None:
                    sharpe_ratio = (portfolio_return - risk_free_rate/252) / portfolio_volatility
                else:
                    sharpe_ratio = 0.0
                
                # Create weights dictionary
                weights_dict = {symbols[i]: float(optimal_weights[i]) for i in range(len(symbols))}
                
                # Generate efficient frontier - ensure proper types
                if isinstance(expected_returns, pd.Series) and isinstance(cov_matrix, pd.DataFrame) and risk_free_rate is not None:
                    efficient_frontier = self._generate_efficient_frontier(
                        expected_returns, cov_matrix, float(risk_free_rate), symbols
                    )
                else:
                    efficient_frontier = []
                
                return PortfolioOptimizationResult(
                    optimal_weights=weights_dict,
                    expected_return=float(portfolio_return),
                    expected_volatility=float(portfolio_volatility),
                    sharpe_ratio=float(sharpe_ratio),
                    efficient_frontier=efficient_frontier
                )
            else:
                # Fallback to equal weights
                weights_dict = {symbols[i]: 1/len(symbols) for i in range(len(symbols))}
                expected_return_val = 0.0
                expected_volatility_val = 0.1
                if isinstance(expected_returns, pd.Series):
                    expected_return_val = float(expected_returns.mean()) if len(expected_returns) > 0 else 0.0
                if isinstance(cov_matrix, pd.DataFrame):
                    expected_volatility_val = float(np.sqrt(np.diag(cov_matrix).mean())) if len(cov_matrix) > 0 else 0.1
                    
                return PortfolioOptimizationResult(
                    optimal_weights=weights_dict,
                    expected_return=expected_return_val,
                    expected_volatility=expected_volatility_val,
                    sharpe_ratio=0.5,  # Conservative estimate
                    efficient_frontier=[]
                )
                
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            # Return equal weights as fallback
            weights_dict = {symbol: 1/len(symbols) for symbol in symbols} if symbols else {}
            return PortfolioOptimizationResult(
                optimal_weights=weights_dict,
                expected_return=0.0,
                expected_volatility=0.1,
                sharpe_ratio=0.5,
                efficient_frontier=[]
            )

    def _generate_efficient_frontier(self, expected_returns: pd.Series, 
                                   cov_matrix: pd.DataFrame,
                                   risk_free_rate: float,
                                   symbols: List[str]) -> List[Dict[str, float]]:
        """
        Generate efficient frontier points
        
        Args:
            expected_returns: Expected returns for assets
            cov_matrix: Covariance matrix
            risk_free_rate: Risk-free rate
            symbols: List of asset symbols
            
        Returns:
            List of efficient frontier points
        """
        try:
            frontier_points = []
            target_returns = np.linspace(expected_returns.min(), expected_returns.max(), 20)
            
            for target in target_returns:
                # Constraints: weights sum to 1 and expected return equals target
                constraints = [
                    {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                    {'type': 'eq', 'fun': lambda x: np.sum(expected_returns * x) - target}
                ]
                
                # Bounds: weights between 0 and 1
                bounds = tuple((0, 1) for _ in range(len(symbols)))
                
                # Initial guess: equal weights
                initial_weights = np.array([1/len(symbols)] * len(symbols))
                
                # Minimize portfolio variance
                def portfolio_variance(weights):
                    return np.dot(weights.T, np.dot(cov_matrix, weights))
                
                result = minimize(portfolio_variance, initial_weights, method='SLSQP',
                                bounds=bounds, constraints=constraints)
                
                if result.success:
                    weights = result.x
                    variance = portfolio_variance(weights)
                    volatility = np.sqrt(variance)
                    
                    frontier_points.append({
                        'expected_return': target,
                        'expected_volatility': volatility,
                        'sharpe_ratio': (target - risk_free_rate/252) / volatility if volatility > 0 else 0,
                        'weights': {symbols[i]: weights[i] for i in range(len(symbols))}
                    })
                    
            return frontier_points
            
        except Exception as e:
            logger.warning(f"Error generating efficient frontier: {e}")
            return []

    def perform_stress_test(self, 
                           portfolio_data: pd.DataFrame,
                           scenario: str = "market_crash_10") -> StressTestResult:
        """
        Perform stress test on portfolio
        
        Args:
            portfolio_data: DataFrame with portfolio holdings and prices
            scenario: Stress test scenario name
            
        Returns:
            StressTestResult object
        """
        try:
            # Define stress scenarios
            scenarios = {
                'market_crash_10': {
                    'description': '10% market crash',
                    'impact': -0.10,
                    'recovery_time': 5,
                    'affected_assets': 'all'
                },
                'market_crash_20': {
                    'description': '20% market crash',
                    'impact': -0.20,
                    'recovery_time': 10,
                    'affected_assets': 'all'
                },
                'flash_crash': {
                    'description': 'Sudden 30% drop with quick recovery',
                    'impact': -0.30,
                    'recovery_time': 2,
                    'affected_assets': 'volatile'
                },
                'regulatory_event': {
                    'description': 'Regulatory crackdown on crypto',
                    'impact': -0.25,
                    'recovery_time': 30,
                    'affected_assets': 'all'
                },
                'exchange_hack': {
                    'description': 'Major exchange security breach',
                    'impact': -0.15,
                    'recovery_time': 7,
                    'affected_assets': 'exchange_specific'
                }
            }
            
            # Get scenario parameters
            scenario_params = scenarios.get(scenario, scenarios['market_crash_10'])
            
            # Calculate portfolio impact
            portfolio_value = portfolio_data['value'].sum() if 'value' in portfolio_data.columns else 10000
            impact_amount = portfolio_value * scenario_params['impact']
            
            # Determine affected assets
            affected_assets = []
            if scenario_params['affected_assets'] == 'all':
                affected_assets = portfolio_data['symbol'].tolist() if 'symbol' in portfolio_data.columns else []
            elif scenario_params['affected_assets'] == 'volatile':
                # For flash crash, affect more volatile assets
                if 'volatility' in portfolio_data.columns:
                    # Sort by volatility and take top 50%
                    sorted_data = portfolio_data.sort_values('volatility', ascending=False)
                    affected_assets = sorted_data.head(len(sorted_data)//2)['symbol'].tolist()
                else:
                    affected_assets = portfolio_data['symbol'].tolist() if 'symbol' in portfolio_data.columns else []
            
            # Determine if risk mitigation is required
            risk_mitigation_required = abs(scenario_params['impact']) > 0.15
            
            return StressTestResult(
                scenario_name=scenario,
                impact_on_portfolio=scenario_params['impact'],
                affected_assets=affected_assets,
                recovery_time=scenario_params['recovery_time'],
                risk_mitigation_required=risk_mitigation_required
            )
            
        except Exception as e:
            logger.error(f"Error performing stress test: {e}")
            return StressTestResult(
                scenario_name=scenario,
                impact_on_portfolio=-0.10,  # Conservative estimate
                affected_assets=[],
                recovery_time=5,
                risk_mitigation_required=True
            )

    def calculate_tail_risk(self, returns_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate tail risk metrics
        
        Args:
            returns_data: DataFrame with historical returns
            
        Returns:
            Dictionary with tail risk metrics
        """
        try:
            if returns_data.empty:
                return {
                    'kurtosis': 0.0,
                    'skewness': 0.0,
                    'tail_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'downside_deviation': 0.0
                }
            
            # Get returns column
            if isinstance(returns_data, pd.DataFrame):
                returns = returns_data.iloc[:, 0] if len(returns_data.columns) == 1 else returns_data.mean(axis=1)
            else:
                returns = returns_data
                
            # Ensure returns is a pandas Series
            if not isinstance(returns, pd.Series):
                returns = pd.Series(returns)
            
            # Calculate kurtosis and skewness
            kurtosis = float(stats.kurtosis(returns)) if len(returns) > 0 else 0.0
            skewness = float(stats.skew(returns)) if len(returns) > 0 else 0.0
            
            # Calculate tail ratio (ratio of 95th percentile to 5th percentile)
            if len(returns) > 0:
                percentile_95 = float(np.percentile(returns, 95))
                percentile_5 = float(np.percentile(returns, 5))
                tail_ratio = float(abs(percentile_95 / percentile_5)) if percentile_5 != 0 else 0.0
            else:
                percentile_95 = 0.0
                percentile_5 = 0.0
                tail_ratio = 0.0
            
            # Calculate maximum drawdown
            if len(returns) > 0:
                cumulative_returns = (1 + returns).cumprod()
                running_max = cumulative_returns.expanding().max()
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = float(drawdown.min())
            else:
                max_drawdown = 0.0
            
            # Calculate downside deviation (deviation below zero)
            if len(returns) > 0:
                negative_returns = returns[returns < 0]
                downside_deviation = float(np.std(negative_returns)) if len(negative_returns) > 0 else 0.0
            else:
                downside_deviation = 0.0
            
            return {
                'kurtosis': float(kurtosis),
                'skewness': float(skewness),
                'tail_ratio': float(tail_ratio),
                'max_drawdown': float(max_drawdown),
                'downside_deviation': float(downside_deviation)
            }
            
        except Exception as e:
            logger.error(f"Error calculating tail risk: {e}")
            return {
                'kurtosis': 3.0,  # Normal distribution kurtosis
                'skewness': 0.0,  # Normal distribution skewness
                'tail_ratio': 1.0,
                'max_drawdown': -0.10,  # 10% drawdown
                'downside_deviation': 0.05
            }

    def generate_risk_report(self, 
                           market_data: Dict[str, pd.DataFrame],
                           portfolio_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive risk report
        
        Args:
            market_data: Dictionary with market data for different assets
            portfolio_data: DataFrame with portfolio holdings
            
        Returns:
            Dictionary with risk report data
        """
        try:
            # Calculate portfolio returns
            portfolio_returns = self._calculate_portfolio_returns(portfolio_data, market_data)
            
            # Calculate VaR
            var_result = self.calculate_value_at_risk(portfolio_returns)
            
            # Calculate tail risk
            tail_risk = self.calculate_tail_risk(portfolio_returns)
            
            # Perform stress tests
            stress_tests = []
            for scenario in self.config['stress_test_scenarios']:
                stress_result = self.perform_stress_test(portfolio_data, scenario)
                stress_tests.append({
                    'scenario': stress_result.scenario_name,
                    'impact': stress_result.impact_on_portfolio,
                    'recovery_time': stress_result.recovery_time,
                    'risk_mitigation_required': stress_result.risk_mitigation_required
                })
            
            # Calculate portfolio metrics
            if not portfolio_returns.empty:
                portfolio_volatility = float(portfolio_returns.std())
                portfolio_return = float(portfolio_returns.mean())
                sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            else:
                portfolio_volatility = 0.1
                portfolio_return = 0.0
                sharpe_ratio = 0.0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'portfolio_metrics': {
                    'expected_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'value_at_risk': {
                        'var_95': var_result.var_95,
                        'var_99': var_result.var_99,
                        'expected_shortfall': var_result.expected_shortfall
                    },
                    'tail_risk': tail_risk
                },
                'stress_tests': stress_tests,
                'risk_level': self._assess_overall_risk_level(var_result, tail_risk),
                'recommendations': self._generate_risk_recommendations(var_result, tail_risk, stress_tests)
            }
            
        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'portfolio_metrics': {
                    'expected_return': 0.0,
                    'volatility': 0.1,
                    'sharpe_ratio': 0.0,
                    'value_at_risk': {
                        'var_95': 0.10,
                        'var_99': 0.20,
                        'expected_shortfall': 0.15
                    },
                    'tail_risk': {
                        'kurtosis': 3.0,
                        'skewness': 0.0,
                        'tail_ratio': 1.0,
                        'max_drawdown': -0.10,
                        'downside_deviation': 0.05
                    }
                },
                'stress_tests': [],
                'risk_level': 'medium',
                'recommendations': ['Review risk parameters', 'Consider diversification']
            }

    def _calculate_portfolio_returns(self, 
                                   portfolio_data: pd.DataFrame,
                                   market_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Calculate portfolio returns from holdings and market data
        
        Args:
            portfolio_data: DataFrame with portfolio holdings
            market_data: Dictionary with market data for different assets
            
        Returns:
            DataFrame with portfolio returns
        """
        try:
            if portfolio_data.empty or not market_data:
                return pd.DataFrame()
            
            # Calculate weighted returns for each asset
            portfolio_returns = pd.DataFrame()
            
            for _, holding in portfolio_data.iterrows():
                symbol = holding.get('symbol')
                weight = holding.get('weight', 0)
                
                if symbol in market_data and weight is not None and weight > 0:
                    asset_data = market_data[symbol]
                    if 'close' in asset_data.columns and len(asset_data) > 1:
                        # Calculate returns
                        returns = asset_data['close'].pct_change(fill_method=None).dropna()
                        weighted_returns = returns * weight
                        
                        if portfolio_returns.empty:
                            portfolio_returns = weighted_returns.to_frame(name=symbol)
                        else:
                            portfolio_returns[symbol] = weighted_returns
            
            # Sum across assets to get portfolio returns
            if not portfolio_returns.empty:
                portfolio_returns['portfolio'] = portfolio_returns.sum(axis=1)
                result = portfolio_returns[['portfolio']].dropna()
                # Ensure we return a DataFrame
                if isinstance(result, pd.DataFrame):
                    return result
                else:
                    return pd.DataFrame({'portfolio': [result]}).dropna() if result is not None else pd.DataFrame()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.warning(f"Error calculating portfolio returns: {e}")
            return pd.DataFrame()

    def _assess_overall_risk_level(self, var_result: VaRResult, tail_risk: Dict[str, float]) -> str:
        """
        Assess overall risk level based on metrics
        
        Args:
            var_result: VaRResult object
            tail_risk: Dictionary with tail risk metrics
            
        Returns:
            Risk level string ('low', 'medium', 'high', 'critical')
        """
        try:
            risk_score = 0
            
            # VaR risk scoring
            if var_result.var_99 > 0.25:  # 25% loss at 99% confidence
                risk_score += 3
            elif var_result.var_99 > 0.15:  # 15% loss at 99% confidence
                risk_score += 2
            elif var_result.var_99 > 0.10:  # 10% loss at 99% confidence
                risk_score += 1
                
            # Tail risk scoring
            if tail_risk['kurtosis'] > 5:  # High kurtosis (fat tails)
                risk_score += 2
            elif tail_risk['kurtosis'] > 3:  # Moderate kurtosis
                risk_score += 1
                
            if tail_risk['max_drawdown'] < -0.20:  # 20% drawdown
                risk_score += 2
            elif tail_risk['max_drawdown'] < -0.10:  # 10% drawdown
                risk_score += 1
                
            # Determine risk level
            if risk_score >= 5:
                return 'critical'
            elif risk_score >= 3:
                return 'high'
            elif risk_score >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.warning(f"Error assessing risk level: {e}")
            return 'medium'

    def _generate_risk_recommendations(self, var_result: VaRResult, 
                                     tail_risk: Dict[str, float],
                                     stress_tests: List[Dict[str, Any]]) -> List[str]:
        """
        Generate risk management recommendations
        
        Args:
            var_result: VaRResult object
            tail_risk: Dictionary with tail risk metrics
            stress_tests: List of stress test results
            
        Returns:
            List of recommendation strings
        """
        try:
            recommendations = []
            
            # VaR-based recommendations
            if var_result.var_99 > 0.20:
                recommendations.append("Consider reducing position sizes to lower VaR")
                recommendations.append("Implement stricter stop-loss rules")
                
            # Tail risk recommendations
            if tail_risk['kurtosis'] > 5:
                recommendations.append("Portfolio exhibits fat tails - consider tail risk hedging")
                
            if tail_risk['max_drawdown'] < -0.15:
                recommendations.append("Historical drawdowns significant - review risk limits")
                
            # Stress test recommendations
            high_impact_scenarios = [st for st in stress_tests if st['impact'] < -0.20]
            if high_impact_scenarios:
                recommendations.append("High-impact stress scenarios identified - consider scenario hedging")
                
            # General recommendations
            if not recommendations:
                recommendations.append("Portfolio risk profile appears manageable")
                recommendations.append("Continue regular risk monitoring")
                
            return recommendations
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            return ["Review risk parameters", "Consider diversification"]