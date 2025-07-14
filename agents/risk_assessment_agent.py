# agents/risk_assessment_agent.py
"""
Risk Assessment Agent for Financial Multi-Agent System
Calculates and evaluates various financial risks
Author: Zhang Weiling (Insybell)
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats
from ..core.base_agent import BaseFinancialAgent
from ..core.models import RiskAssessment, RiskMetrics, MarketAnalysis
from ..core.enums import MessageType, Priority, RiskLevel

logger = logging.getLogger(__name__)


class RiskAssessmentAgent(BaseFinancialAgent):
    """Agent responsible for comprehensive risk assessment and evaluation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RiskAssessmentAgent", config)
        self.risk_models = {
            'var': self._calculate_var,
            'sharpe': self._calculate_sharpe_ratio,
            'sortino': self._calculate_sortino_ratio,
            'max_drawdown': self._calculate_max_drawdown,
            'beta': self._calculate_beta,
            'information_ratio': self._calculate_information_ratio
        }
        
        # Risk thresholds configuration
        self.risk_thresholds = {
            RiskLevel.LOW: {"volatility": 0.15, "var_95": -0.02, "max_drawdown": -0.1},
            RiskLevel.MEDIUM: {"volatility": 0.25, "var_95": -0.03, "max_drawdown": -0.2},
            RiskLevel.HIGH: {"volatility": 0.4, "var_95": -0.05, "max_drawdown": -0.3},
            RiskLevel.CRITICAL: {"volatility": float('inf'), "var_95": float('-inf'), "max_drawdown": float('-inf')}
        }
        
        # Register message handlers
        self.register_message_handler(MessageType.ANALYSIS_COMPLETE, self._handle_analysis_complete)
    
    async def _handle_analysis_complete(self, message):
        """Handle incoming market analysis messages"""
        market_analysis_dict = message.data.get('market_analysis', {})
        market_insights = message.data.get('market_insights', {})
        
        # Deserialize market analysis
        market_analysis = self._deserialize_market_analysis(market_analysis_dict)
        
        # Perform risk assessment
        risk_assessment = await self.assess_comprehensive_risk(market_analysis, market_insights)
        
        # Send to next agent
        await self.send_mcp_message(
            target_agent="RecommendationAgent",
            message_type=MessageType.RISK_ASSESSED,
            data={
                'risk_assessment': self._serialize_risk_assessment(risk_assessment),
                'market_analysis': market_analysis_dict,
                'market_insights': market_insights
            },
            priority=Priority.HIGH if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else Priority.MEDIUM,
            correlation_id=message.correlation_id
        )
    
    def _generate_mock_returns(self, symbol: str, days: int = 252) -> pd.Series:
        """Generate realistic mock returns for demonstration purposes"""
        # In production, this would extract actual returns from historical data
        # For now, we'll create realistic mock data based on the symbol
        
        np.random.seed(hash(symbol) % 2**32)  # Consistent seed based on symbol
        
        # Different volatility patterns for different types of stocks
        if symbol in ['AAPL', 'MSFT', 'GOOGL']:  # Large cap tech
            mu, sigma = 0.0008, 0.015
        elif symbol in ['TSLA', 'NVDA']:  # High volatility growth
            mu, sigma = 0.001, 0.035
        elif symbol in ['JNJ', 'PG', 'KO']:  # Defensive stocks
            mu, sigma = 0.0005, 0.008
        else:  # Default
            mu, sigma = 0.0006, 0.02
        
        # Generate returns with some autocorrelation
        returns = np.random.normal(mu, sigma, days)
        
        # Add some clustering volatility (GARCH-like behavior)
        for i in range(1, len(returns)):
            if abs(returns[i-1]) > sigma:
                returns[i] *= 1.5  # Volatility clustering
        
        return pd.Series(returns)
    
    def _calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk"""
        if len(returns) < 30:
            logger.warning("Insufficient data for reliable VaR calculation")
            return -0.02  # Default conservative estimate
        
        return float(np.percentile(returns, (1 - confidence) * 100))
    
    def _calculate_conditional_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        var = self._calculate_var(returns, confidence)
        tail_losses = returns[returns <= var]
        
        if len(tail_losses) == 0:
            return var
        
        return float(tail_losses.mean())
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if returns.std() == 0:
            return 0.0
        
        excess_returns = returns.mean() - risk_free_rate / 252  # Daily risk-free rate
        return float((excess_returns / returns.std()) * np.sqrt(252))  # Annualized
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return float(self._calculate_sharpe_ratio(returns, risk_free_rate))
        
        downside_std = downside_returns.std()
        return float((excess_returns.mean() / downside_std) * np.sqrt(252))
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        return float(drawdown.min())
    
    def _calculate_beta(self, stock_returns: pd.Series, market_returns: Optional[pd.Series] = None) -> float:
        """Calculate beta against market"""
        if market_returns is None:
            # Generate mock market returns (S&P 500 proxy)
            market_returns = self._generate_mock_returns("SPY", len(stock_returns))
        
        if len(stock_returns) != len(market_returns) or len(stock_returns) < 30:
            return 1.0  # Default beta
        
        try:
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                return 1.0
            
            return float(covariance / market_variance)
        except:
            return 1.0
    
    def _calculate_information_ratio(self, returns: pd.Series, benchmark_returns: Optional[pd.Series] = None) -> float:
        """Calculate Information Ratio"""
        if benchmark_returns is None:
            benchmark_returns = self._generate_mock_returns("SPY", len(returns))
        
        if len(returns) != len(benchmark_returns):
            return 0.0
        
        excess_returns = returns - benchmark_returns
        tracking_error = excess_returns.std()
        
        if tracking_error == 0:
            return 0.0
        
        return float((excess_returns.mean() / tracking_error) * np.sqrt(252))
    
    def _calculate_volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility"""
        return float(returns.std() * np.sqrt(252))
    
    def _assess_liquidity_risk(self, market_analysis: MarketAnalysis) -> Dict[str, Any]:
        """Assess liquidity risk based on volume patterns"""
        volume_analysis = market_analysis.volume_analysis
        
        # Liquidity risk factors
        risk_factors = []
        liquidity_score = 1.0  # 1.0 = high liquidity, 0.0 = low liquidity
        
        # Volume ratio analysis
        volume_ratio = volume_analysis.get('current_vs_average', 1.0)
        if volume_ratio < 0.5:
            risk_factors.append("Low trading volume relative to average")
            liquidity_score *= 0.7
        elif volume_ratio < 0.8:
            risk_factors.append("Below-average trading volume")
            liquidity_score *= 0.9
        
        # Volume trend analysis
        volume_trend = volume_analysis.get('trend', 'stable')
        if volume_trend == 'decreasing':
            risk_factors.append("Decreasing volume trend")
            liquidity_score *= 0.8
        
        # Price-volume correlation
        pv_correlation = volume_analysis.get('price_volume_correlation', 0.0)
        if abs(pv_correlation) < 0.1:
            risk_factors.append("Weak price-volume relationship")
            liquidity_score *= 0.85
        
        # Determine liquidity risk level
        if liquidity_score > 0.8:
            liquidity_risk = "low"
        elif liquidity_score > 0.6:
            liquidity_risk = "medium"
        elif liquidity_score > 0.4:
            liquidity_risk = "high"
        else:
            liquidity_risk = "critical"
        
        return {
            'liquidity_score': liquidity_score,
            'liquidity_risk': liquidity_risk,
            'risk_factors': risk_factors,
            'volume_metrics': {
                'current_vs_average': volume_ratio,
                'trend': volume_trend,
                'price_volume_correlation': pv_correlation
            }
        }
    
    def _assess_technical_risk(self, market_analysis: MarketAnalysis) -> Dict[str, Any]:
        """Assess technical analysis based risks"""
        indicators = market_analysis.technical_indicators
        risk_factors = []
        risk_score = 0  # Higher score = higher risk
        
        # RSI-based risk assessment
        if indicators.rsi > 80:
            risk_factors.append("Severely overbought conditions (RSI > 80)")
            risk_score += 3
        elif indicators.rsi > 70:
            risk_factors.append("Overbought conditions (RSI > 70)")
            risk_score += 2
        elif indicators.rsi < 20:
            risk_factors.append("Severely oversold conditions (RSI < 20)")
            risk_score += 2
        elif indicators.rsi < 30:
            risk_factors.append("Oversold conditions (RSI < 30)")
            risk_score += 1
        
        # Moving average risk assessment
        current_price = market_analysis.current_price
        if current_price < indicators.sma_200:
            risk_factors.append("Price below 200-day moving average (bearish long-term trend)")
            risk_score += 2
        
        if indicators.sma_20 < indicators.sma_50 < indicators.sma_200:
            risk_factors.append("Death cross pattern (bearish moving average alignment)")
            risk_score += 3
        
        # Bollinger Bands risk assessment
        bb_position = (current_price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower)
        if bb_position > 0.95:
            risk_factors.append("Price near upper Bollinger Band (potential reversal)")
            risk_score += 2
        elif bb_position < 0.05:
            risk_factors.append("Price near lower Bollinger Band (potential bounce)")
            risk_score += 1
        
        # MACD divergence risk
        if indicators.macd < indicators.macd_signal and indicators.macd < 0:
            risk_factors.append("MACD bearish divergence")
            risk_score += 2
        
        # Support/resistance risk
        support_resistance = market_analysis.support_resistance
        distance_to_support = support_resistance.get('distance_to_support', 0.1)
        distance_to_resistance = support_resistance.get('distance_to_resistance', 0.1)
        
        if distance_to_support < 0.02:  # Very close to support
            risk_factors.append("Price very close to key support level")
            risk_score += 2
        elif distance_to_resistance < 0.02:  # Very close to resistance
            risk_factors.append("Price very close to key resistance level")
            risk_score += 1
        
        # Determine technical risk level
        if risk_score >= 8:
            technical_risk = "critical"
        elif risk_score >= 6:
            technical_risk = "high"
        elif risk_score >= 3:
            technical_risk = "medium"
        else:
            technical_risk = "low"
        
        return {
            'technical_risk': technical_risk,
            'risk_score': risk_score,
            'risk_factors': risk_factors,
            'technical_levels': {
                'rsi': indicators.rsi,
                'bb_position': bb_position,
                'ma_alignment': "bearish" if indicators.sma_20 < indicators.sma_50 else "bullish",
                'macd_signal': "bearish" if indicators.macd < indicators.macd_signal else "bullish"
            }
        }
    
    def _calculate_composite_risk_score(self, risk_metrics: RiskMetrics, 
                                      liquidity_risk: Dict, technical_risk: Dict) -> float:
        """Calculate composite risk score from all risk factors"""
        score = 0.0
        
        # Volatility component (25% weight)
        vol_score = min(risk_metrics.volatility / 0.4, 1.0) * 25
        score += vol_score
        
        # VaR component (20% weight)
        var_score = min(abs(risk_metrics.var_95) / 0.05, 1.0) * 20
        score += var_score
        
        # Maximum drawdown component (20% weight)
        dd_score = min(abs(risk_metrics.max_drawdown) / 0.3, 1.0) * 20
        score += dd_score
        
        # Sharpe ratio component (15% weight) - inverse relationship
        sharpe_score = max(0, (2.0 - risk_metrics.sharpe_ratio) / 2.0) * 15
        score += sharpe_score
        
        # Liquidity risk component (10% weight)
        liquidity_score = (1.0 - liquidity_risk['liquidity_score']) * 10
        score += liquidity_score
        
        # Technical risk component (10% weight)
        tech_risk_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
        tech_score = tech_risk_map.get(technical_risk['technical_risk'], 0.5) * 10
        score += tech_score
        
        return min(score / 100.0, 1.0)  # Normalize to 0-1 scale
    
    def _determine_overall_risk_level(self, composite_score: float, 
                                    risk_metrics: RiskMetrics) -> RiskLevel:
        """Determine overall risk level based on composite score and key metrics"""
        
        # Check for critical conditions first
        if (risk_metrics.volatility > 0.6 or 
            abs(risk_metrics.var_95) > 0.08 or 
            abs(risk_metrics.max_drawdown) > 0.5):
            return RiskLevel.CRITICAL
        
        # Use composite score for classification
        if composite_score >= 0.8:
            return RiskLevel.CRITICAL
        elif composite_score >= 0.6:
            return RiskLevel.HIGH
        elif composite_score >= 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def assess_comprehensive_risk(self, market_analysis: MarketAnalysis, 
                                      market_insights: Dict[str, Any] = None) -> RiskAssessment:
        """Perform comprehensive risk assessment"""
        try:
            await self.log_activity(f"Starting risk assessment for {market_analysis.symbol}")
            
            # Generate returns data (in production, this would come from actual historical data)
            returns = self._generate_mock_returns(market_analysis.symbol)
            
            # Calculate all risk metrics
            risk_metrics = RiskMetrics(
                var_95=self._calculate_var(returns, 0.95),
                var_99=self._calculate_var(returns, 0.99),
                sharpe_ratio=self._calculate_sharpe_ratio(returns),
                max_drawdown=self._calculate_max_drawdown(returns),
                volatility=self._calculate_volatility(returns),
                beta=self._calculate_beta(returns),
                information_ratio=self._calculate_information_ratio(returns),
                sortino_ratio=self._calculate_sortino_ratio(returns)
            )
            
            # Assess different types of risks
            liquidity_risk = self._assess_liquidity_risk(market_analysis)
            technical_risk = self._assess_technical_risk(market_analysis)
            
            # Calculate composite risk score
            composite_score = self._calculate_composite_risk_score(
                risk_metrics, liquidity_risk, technical_risk
            )
            
            # Determine overall risk level
            overall_risk_level = self._determine_overall_risk_level(composite_score, risk_metrics)
            
            # Compile risk factors
            risk_factors = []
            risk_factors.extend(liquidity_risk['risk_factors'])
            risk_factors.extend(technical_risk['risk_factors'])
            
            # Add quantitative risk factors
            if risk_metrics.volatility > 0.3:
                risk_factors.append(f"High volatility: {risk_metrics.volatility:.1%}")
            if abs(risk_metrics.max_drawdown) > 0.2:
                risk_factors.append(f"Significant historical drawdown: {risk_metrics.max_drawdown:.1%}")
            if risk_metrics.sharpe_ratio < 0.5:
                risk_factors.append(f"Poor risk-adjusted returns: Sharpe {risk_metrics.sharpe_ratio:.2f}")
            if risk_metrics.beta > 1.5:
                risk_factors.append(f"High market sensitivity: Beta {risk_metrics.beta:.2f}")
            
            # Calculate confidence based on data quality and analysis completeness
            base_confidence = market_analysis.data_quality
            
            # Adjust confidence based on available data and analysis depth
            if len(returns) >= 252:  # Full year of data
                confidence_adjustment = 1.0
            elif len(returns) >= 126:  # Half year
                confidence_adjustment = 0.9
            elif len(returns) >= 63:  # Quarter
                confidence_adjustment = 0.8
            else:
                confidence_adjustment = 0.6
            
            final_confidence = min(base_confidence * confidence_adjustment, 0.95)
            
            # Create risk assessment
            risk_assessment = RiskAssessment(
                symbol=market_analysis.symbol,
                risk_metrics=risk_metrics,
                risk_level=overall_risk_level,
                confidence=final_confidence,
                risk_factors=risk_factors,
                assessment_timestamp=datetime.now().isoformat(),
                methodology="comprehensive_quantitative"
            )
            
            await self.log_activity(
                f"Risk assessment completed for {market_analysis.symbol}",
                data={
                    'risk_level': overall_risk_level.value,
                    'composite_score': composite_score,
                    'volatility': risk_metrics.volatility,
                    'var_95': risk_metrics.var_95,
                    'confidence': final_confidence
                }
            )
            
            return risk_assessment
            
        except Exception as e:
            await self.log_activity(f"Risk assessment failed for {market_analysis.symbol}: {str(e)}", "error")
            raise
    
    async def assess_portfolio_risk(self, individual_assessments: List[RiskAssessment],
                                  weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """Assess portfolio-level risk across multiple positions"""
        try:
            if not individual_assessments:
                return {"error": "No individual assessments provided"}
            
            if weights is None:
                weights = [1.0 / len(individual_assessments)] * len(individual_assessments)
            
            if len(weights) != len(individual_assessments):
                raise ValueError("Weights must match number of assessments")
            
            # Calculate weighted portfolio metrics
            portfolio_var_95 = sum(w * assess.risk_metrics.var_95 for w, assess in zip(weights, individual_assessments))
            portfolio_volatility = np.sqrt(sum((w * assess.risk_metrics.volatility) ** 2 for w, assess in zip(weights, individual_assessments)))
            portfolio_sharpe = sum(w * assess.risk_metrics.sharpe_ratio for w, assess in zip(weights, individual_assessments))
            portfolio_beta = sum(w * assess.risk_metrics.beta for w, assess in zip(weights, individual_assessments))
            
            # Risk distribution analysis
            risk_distribution = {level.value: 0.0 for level in RiskLevel}
            for weight, assessment in zip(weights, individual_assessments):
                risk_distribution[assessment.risk_level.value] += weight
            
            # Concentration risk
            max_weight = max(weights)
            concentration_risk = "high" if max_weight > 0.3 else "medium" if max_weight > 0.2 else "low"
            
            # Correlation analysis (simplified - would use actual correlation matrix in production)
            correlation_risk = "medium"  # Placeholder
            
            # Overall portfolio risk level
            weighted_risk_scores = []
            risk_level_scores = {RiskLevel.LOW: 1, RiskLevel.MEDIUM: 2, RiskLevel.HIGH: 3, RiskLevel.CRITICAL: 4}
            
            for weight, assessment in zip(weights, individual_assessments):
                score = risk_level_scores[assessment.risk_level]
                weighted_risk_scores.append(weight * score)
            
            avg_risk_score = sum(weighted_risk_scores)
            if avg_risk_score >= 3.5:
                portfolio_risk_level = RiskLevel.CRITICAL
            elif avg_risk_score >= 2.5:
                portfolio_risk_level = RiskLevel.HIGH
            elif avg_risk_score >= 1.5:
                portfolio_risk_level = RiskLevel.MEDIUM
            else:
                portfolio_risk_level = RiskLevel.LOW
            
            return {
                'portfolio_risk_level': portfolio_risk_level.value,
                'portfolio_metrics': {
                    'var_95': portfolio_var_95,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': portfolio_sharpe,
                    'beta': portfolio_beta
                },
                'risk_distribution': risk_distribution,
                'concentration_risk': concentration_risk,
                'correlation_risk': correlation_risk,
                'diversification_score': 1.0 - max_weight,  # Simple diversification measure
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Portfolio risk assessment failed: {str(e)}")
            return {"error": f"Portfolio assessment failed: {str(e)}"}
    
    async def process(self, input_data: Dict[str, Any]) -> RiskAssessment:
        """Main processing method"""
        try:
            # Handle market analysis input
            if 'market_analysis' in input_data:
                market_analysis = self._deserialize_market_analysis(input_data['market_analysis'])
                market_insights = input_data.get('market_insights', {})
            else:
                raise ValueError("Market analysis data required for risk assessment")
            
            # Perform risk assessment
            risk_assessment = await self.assess_comprehensive_risk(market_analysis, market_insights)
            
            # Send to Recommendation Agent
            await self.send_mcp_message(
                target_agent="RecommendationAgent",
                message_type=MessageType.RISK_ASSESSED,
                data={
                    'risk_assessment': self._serialize_risk_assessment(risk_assessment),
                    'market_analysis': input_data['market_analysis'],
                    'market_insights': market_insights
                },
                priority=Priority.HIGH if risk_assessment.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else Priority.MEDIUM
            )
            
            return risk_assessment
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def _deserialize_market_analysis(self, data_dict: Dict[str, Any]) -> MarketAnalysis:
        """Deserialize market analysis from MCP message"""
        from ..core.models import TechnicalIndicators
        
        tech_indicators = TechnicalIndicators(**data_dict['technical_indicators'])
        
        return MarketAnalysis(
            symbol=data_dict['symbol'],
            current_price=data_dict['current_price'],
            trend_strength=data_dict['trend_strength'],
            technical_indicators=tech_indicators,
            volume_analysis=data_dict['volume_analysis'],
            support_resistance=data_dict['support_resistance'],
            data_quality=data_dict['data_quality'],
            analysis_timestamp=data_dict['analysis_timestamp']
        )
    
    def _serialize_risk_assessment(self, assessment: RiskAssessment) -> Dict[str, Any]:
        """Serialize risk assessment for MCP transmission"""
        return {
            'symbol': assessment.symbol,
            'risk_metrics': {
                'var_95': assessment.risk_metrics.var_95,
                'var_99': assessment.risk_metrics.var_99,
                'sharpe_ratio': assessment.risk_metrics.sharpe_ratio,
                'max_drawdown': assessment.risk_metrics.max_drawdown,
                'volatility': assessment.risk_metrics.volatility,
                'beta': assessment.risk_metrics.beta,
                'information_ratio': assessment.risk_metrics.information_ratio,
                'sortino_ratio': assessment.risk_metrics.sortino_ratio
            },
            'risk_level': assessment.risk_level.value,
            'confidence': assessment.confidence,
            'risk_factors': assessment.risk_factors,
            'assessment_timestamp': assessment.assessment_timestamp,
            'methodology': assessment.methodology
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "value_at_risk_calculation",
            "sharpe_ratio_analysis",
            "sortino_ratio_calculation",
            "maximum_drawdown_assessment",
            "beta_calculation",
            "information_ratio_analysis",
            "liquidity_risk_assessment",
            "technical_risk_evaluation",
            "portfolio_risk_aggregation",
            "composite_risk_scoring",
            "risk_level_classification"
        ]
    
    async def get_risk_model_performance(self) -> Dict[str, Any]:
        """Get performance metrics for risk models"""
        return {
            "models_available": list(self.risk_models.keys()),
            "risk_thresholds": {level.value: thresholds for level, thresholds in self.risk_thresholds.items()},
            "last_updated": datetime.now().isoformat()
        }
    
    async def update_risk_thresholds(self, new_thresholds: Dict[str, Dict[str, float]]):
        """Update risk threshold configuration"""
        for risk_level_str, thresholds in new_thresholds.items():
            try:
                risk_level = RiskLevel(risk_level_str)
                self.risk_thresholds[risk_level].update(thresholds)
            except ValueError:
                logger.warning(f"Invalid risk level: {risk_level_str}")
        
        await self.log_activity("Risk thresholds updated", data=new_thresholds)
