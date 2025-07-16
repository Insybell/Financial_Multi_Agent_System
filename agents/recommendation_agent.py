import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from ..core.base_agent import BaseFinancialAgent
from ..core.models import Recommendation, RiskAssessment, MarketAnalysis, RiskMetrics
from ..core.enums import MessageType, Priority, RiskLevel, RecommendationAction, TimeHorizon, ValidationStatus

logger = logging.getLogger(__name__)


class RecommendationAgent(BaseFinancialAgent):
    """Agent responsible for generating investment recommendations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RecommendationAgent", config)
        
        # Recommendation configuration
        self.recommendation_config = {
            "min_confidence_threshold": 0.3,
            "max_position_size": 0.1,  # 10% max position
            "risk_tolerance": {
                RiskLevel.LOW: {"max_allocation": 0.3, "stop_loss_pct": 0.05},
                RiskLevel.MEDIUM: {"max_allocation": 0.2, "stop_loss_pct": 0.08},
                RiskLevel.HIGH: {"max_allocation": 0.1, "stop_loss_pct": 0.12},
                RiskLevel.CRITICAL: {"max_allocation": 0.05, "stop_loss_pct": 0.15}
            },
            "time_horizons": {
                TimeHorizon.SHORT_TERM: {"min_return": 0.05, "max_risk": 0.2},
                TimeHorizon.MEDIUM_TERM: {"min_return": 0.1, "max_risk": 0.25},
                TimeHorizon.LONG_TERM: {"min_return": 0.15, "max_risk": 0.3}
            }
        }
        
        # Recommendation models
        self.recommendation_models = {
            'technical': self._technical_recommendation,
            'risk_adjusted': self._risk_adjusted_recommendation,
            'momentum': self._momentum_recommendation,
            'mean_reversion': self._mean_reversion_recommendation
        }
        
        # Register message handlers
        self.register_message_handler(MessageType.RISK_ASSESSED, self._handle_risk_assessed)
    
    async def _handle_risk_assessed(self, message):
        """Handle incoming risk assessment messages"""
        risk_assessment_dict = message.data.get('risk_assessment', {})
        market_analysis_dict = message.data.get('market_analysis', {})
        market_insights = message.data.get('market_insights', {})
        
        # Deserialize data
        risk_assessment = self._deserialize_risk_assessment(risk_assessment_dict)
        market_analysis = self._deserialize_market_analysis(market_analysis_dict)
        
        # Generate recommendation
        recommendation = await self.generate_comprehensive_recommendation(
            market_analysis, risk_assessment, market_insights
        )
        
        # Send to Report Generation Agent
        await self.send_mcp_message(
            target_agent="ReportGenerationAgent",
            message_type=MessageType.RECOMMENDATIONS_READY,
            data={
                'recommendation': self._serialize_recommendation(recommendation),
                'risk_assessment': risk_assessment_dict,
                'market_analysis': market_analysis_dict,
                'market_insights': market_insights
            },
            priority=Priority.HIGH if recommendation.action in [RecommendationAction.STRONG_BUY.value, RecommendationAction.STRONG_SELL.value] else Priority.MEDIUM,
            correlation_id=message.correlation_id
        )
    
    def _technical_recommendation(self, market_analysis: MarketAnalysis, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate recommendation based on technical analysis"""
        indicators = market_analysis.technical_indicators
        current_price = market_analysis.current_price
        
        # Technical scoring system
        technical_score = 0
        signals = []
        
        # RSI Analysis
        if indicators.rsi < 30:
            technical_score += 2
            signals.append("RSI oversold - potential bounce")
        elif indicators.rsi < 40:
            technical_score += 1
            signals.append("RSI approaching oversold")
        elif indicators.rsi > 70:
            technical_score -= 2
            signals.append("RSI overbought - potential pullback")
        elif indicators.rsi > 60:
            technical_score -= 1
            signals.append("RSI approaching overbought")
        
        # Moving Average Analysis
        if current_price > indicators.sma_20 > indicators.sma_50:
            technical_score += 2
            signals.append("Bullish MA alignment")
        elif current_price > indicators.sma_20:
            technical_score += 1
            signals.append("Price above short-term MA")
        elif current_price < indicators.sma_20 < indicators.sma_50:
            technical_score -= 2
            signals.append("Bearish MA alignment")
        elif current_price < indicators.sma_20:
            technical_score -= 1
            signals.append("Price below short-term MA")
        
        # MACD Analysis
        if indicators.macd > indicators.macd_signal and indicators.macd > 0:
            technical_score += 1
            signals.append("MACD bullish crossover")
        elif indicators.macd < indicators.macd_signal and indicators.macd < 0:
            technical_score -= 1
            signals.append("MACD bearish crossover")
        
        # Bollinger Bands Analysis
        bb_position = (current_price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower)
        if bb_position < 0.2:
            technical_score += 1
            signals.append("Price near lower BB - potential bounce")
        elif bb_position > 0.8:
            technical_score -= 1
            signals.append("Price near upper BB - potential reversal")
        
        # Volume Confirmation
        volume_ratio = indicators.volume_ratio
        if volume_ratio > 1.5 and technical_score > 0:
            technical_score += 1
            signals.append("High volume confirms bullish signals")
        elif volume_ratio > 1.5 and technical_score < 0:
            technical_score -= 1
            signals.append("High volume confirms bearish signals")
        
        return {
            'score': technical_score,
            'signals': signals,
            'model': 'technical'
        }
    
    def _risk_adjusted_recommendation(self, market_analysis: MarketAnalysis, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate risk-adjusted recommendation"""
        risk_metrics = risk_assessment.risk_metrics
        risk_score = 0
        risk_signals = []
        
        # Sharpe Ratio Analysis
        if risk_metrics.sharpe_ratio > 1.5:
            risk_score += 2
            risk_signals.append("Excellent risk-adjusted returns")
        elif risk_metrics.sharpe_ratio > 1.0:
            risk_score += 1
            risk_signals.append("Good risk-adjusted returns")
        elif risk_metrics.sharpe_ratio < 0:
            risk_score -= 2
            risk_signals.append("Negative risk-adjusted returns")
        elif risk_metrics.sharpe_ratio < 0.5:
            risk_score -= 1
            risk_signals.append("Poor risk-adjusted returns")
        
        # Volatility Analysis
        if risk_metrics.volatility < 0.15:
            risk_score += 1
            risk_signals.append("Low volatility environment")
        elif risk_metrics.volatility > 0.4:
            risk_score -= 2
            risk_signals.append("High volatility - proceed with caution")
        elif risk_metrics.volatility > 0.25:
            risk_score -= 1
            risk_signals.append("Elevated volatility")
        
        # VaR Analysis
        if abs(risk_metrics.var_95) < 0.02:
            risk_score += 1
            risk_signals.append("Acceptable daily risk")
        elif abs(risk_metrics.var_95) > 0.05:
            risk_score -= 2
            risk_signals.append("High daily risk exposure")
        
        # Maximum Drawdown Analysis
        if abs(risk_metrics.max_drawdown) < 0.1:
            risk_score += 1
            risk_signals.append("Limited historical drawdowns")
        elif abs(risk_metrics.max_drawdown) > 0.3:
            risk_score -= 2
            risk_signals.append("Significant historical drawdowns")
        
        # Beta Analysis
        if 0.8 <= risk_metrics.beta <= 1.2:
            risk_score += 1
            risk_signals.append("Moderate market correlation")
        elif risk_metrics.beta > 1.5:
            risk_score -= 1
            risk_signals.append("High market sensitivity")
        elif risk_metrics.beta < 0.5:
            risk_signals.append("Low market correlation")
        
        return {
            'score': risk_score,
            'signals': risk_signals,
            'model': 'risk_adjusted'
        }
    
    def _momentum_recommendation(self, market_analysis: MarketAnalysis, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate momentum-based recommendation"""
        trend_strength = market_analysis.trend_strength
        indicators = market_analysis.technical_indicators
        
        momentum_score = 0
        momentum_signals = []
        
        # Trend Analysis
        if trend_strength == "bullish":
            momentum_score += 2
            momentum_signals.append("Strong bullish momentum")
        elif trend_strength == "bearish":
            momentum_score -= 2
            momentum_signals.append("Strong bearish momentum")
        elif trend_strength == "volatile":
            momentum_score -= 1
            momentum_signals.append("Volatile momentum - unclear direction")
        
        # RSI Momentum
        if 40 < indicators.rsi < 60:
            momentum_score += 1
            momentum_signals.append("RSI in healthy momentum range")
        elif indicators.rsi > 80 or indicators.rsi < 20:
            momentum_score -= 1
            momentum_signals.append("RSI at extreme levels")
        
        # Volume Momentum
        volume_analysis = market_analysis.volume_analysis
        if volume_analysis.get('trend') == 'increasing':
            momentum_score += 1
            momentum_signals.append("Increasing volume supports momentum")
        elif volume_analysis.get('trend') == 'decreasing':
            momentum_score -= 1
            momentum_signals.append("Decreasing volume weakens momentum")
        
        return {
            'score': momentum_score,
            'signals': momentum_signals,
            'model': 'momentum'
        }
    
    def _mean_reversion_recommendation(self, market_analysis: MarketAnalysis, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Generate mean reversion recommendation"""
        indicators = market_analysis.technical_indicators
        current_price = market_analysis.current_price
        
        reversion_score = 0
        reversion_signals = []
        
        # Distance from moving averages
        ma_50_distance = (current_price - indicators.sma_50) / indicators.sma_50
        ma_200_distance = (current_price - indicators.sma_200) / indicators.sma_200
        
        # Oversold/Overbought conditions
        if indicators.rsi < 25:
            reversion_score += 2
            reversion_signals.append("Severely oversold - mean reversion candidate")
        elif indicators.rsi > 75:
            reversion_score -= 2
            reversion_signals.append("Severely overbought - mean reversion expected")
        
        # Price deviation from long-term mean
        if abs(ma_200_distance) > 0.2:
            if ma_200_distance < -0.2:
                reversion_score += 1
                reversion_signals.append("Significantly below long-term average")
            else:
                reversion_score -= 1
                reversion_signals.append("Significantly above long-term average")
        
        # Bollinger Bands reversion signals
        bb_position = (current_price - indicators.bb_lower) / (indicators.bb_upper - indicators.bb_lower)
        if bb_position < 0.1:
            reversion_score += 2
            reversion_signals.append("Near lower BB - strong reversion signal")
        elif bb_position > 0.9:
            reversion_score -= 2
            reversion_signals.append("Near upper BB - strong reversion signal")
        
        return {
            'score': reversion_score,
            'signals': reversion_signals,
            'model': 'mean_reversion'
        }
    
    def _calculate_price_targets(self, market_analysis: MarketAnalysis, 
                               recommendation_action: str) -> Tuple[Optional[float], Optional[float]]:
        """Calculate target price and stop loss"""
        current_price = market_analysis.current_price
        indicators = market_analysis.technical_indicators
        support_resistance = market_analysis.support_resistance
        
        target_price = None
        stop_loss = None
        
        if recommendation_action in [RecommendationAction.BUY.value, RecommendationAction.STRONG_BUY.value]:
            # Target price calculation for buy recommendations
            resistance = support_resistance.get('primary_resistance', current_price * 1.1)
            target_price = min(resistance * 0.95, current_price * 1.15)  # Conservative target
            
            # Stop loss calculation
            support = support_resistance.get('primary_support', current_price * 0.9)
            stop_loss = max(support * 1.02, current_price * 0.92)  # 8% stop loss max
            
        elif recommendation_action in [RecommendationAction.SELL.value, RecommendationAction.STRONG_SELL.value]:
            # Target price calculation for sell recommendations
            support = support_resistance.get('primary_support', current_price * 0.9)
            target_price = max(support * 1.05, current_price * 0.85)  # Conservative target
            
            # Stop loss calculation (for short positions)
            resistance = support_resistance.get('primary_resistance', current_price * 1.1)
            stop_loss = min(resistance * 0.98, current_price * 1.08)  # 8% stop loss max
        
        return target_price, stop_loss
    
    def _determine_time_horizon(self, market_analysis: MarketAnalysis, risk_assessment: RiskAssessment) -> TimeHorizon:
        """Determine appropriate time horizon for recommendation"""
        volatility = risk_assessment.risk_metrics.volatility
        trend_strength = market_analysis.trend_strength
        
        # High volatility suggests shorter time horizon
        if volatility > 0.4:
            return TimeHorizon.SHORT_TERM
        
        # Strong trends can support longer horizons
        if trend_strength in ["bullish", "bearish"]:
            if volatility < 0.2:
                return TimeHorizon.LONG_TERM
            else:
                return TimeHorizon.MEDIUM_TERM
        
        # Default to medium term
        return TimeHorizon.MEDIUM_TERM
    
    async def generate_comprehensive_recommendation(self, market_analysis: MarketAnalysis, 
                                                  risk_assessment: RiskAssessment,
                                                  market_insights: Dict[str, Any] = None) -> Recommendation:
        """Generate comprehensive investment recommendation"""
        try:
            await self.log_activity(f"Generating recommendation for {market_analysis.symbol}")
            
            # Run all recommendation models
            model_results = {}
            for model_name, model_func in self.recommendation_models.items():
                try:
                    result = model_func(market_analysis, risk_assessment)
                    model_results[model_name] = result
                except Exception as e:
                    logger.error(f"Error in {model_name} model: {str(e)}")
                    model_results[model_name] = {'score': 0, 'signals': [], 'model': model_name}
            
            # Aggregate scores with weights
            model_weights = {
                'technical': 0.3,
                'risk_adjusted': 0.3,
                'momentum': 0.2,
                'mean_reversion': 0.2
            }
            
            total_score = sum(
                model_results[model]['score'] * weight 
                for model, weight in model_weights.items()
                if model in model_results
            )
            
            # Determine recommendation action
            if total_score >= 3:
                action = RecommendationAction.STRONG_BUY.value
                confidence_base = 0.8
            elif total_score >= 1.5:
                action = RecommendationAction.BUY.value
                confidence_base = 0.7
            elif total_score <= -3:
                action = RecommendationAction.STRONG_SELL.value
                confidence_base = 0.8
            elif total_score <= -1.5:
                action = RecommendationAction.SELL.value
                confidence_base = 0.7
            else:
                action = RecommendationAction.HOLD.value
                confidence_base = 0.5
            
            # Adjust confidence based on risk assessment confidence and data quality
            confidence = min(
                confidence_base * risk_assessment.confidence * market_analysis.data_quality,
                0.95
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(model_results, market_insights, total_score)
            
            # Calculate price targets
            target_price, stop_loss = self._calculate_price_targets(market_analysis, action)
            
            # Determine time horizon
            time_horizon = self._determine_time_horizon(market_analysis, risk_assessment)
            
            # Compile risk factors
            risk_factors = risk_assessment.risk_factors.copy()
            
            # Add model-specific risk factors
            for model_result in model_results.values():
                risk_factors.extend([
                    signal for signal in model_result['signals'] 
                    if any(word in signal.lower() for word in ['risk', 'caution', 'warning', 'high', 'extreme'])
                ])
            
            # Remove duplicates
            risk_factors = list(set(risk_factors))
            
            # Calculate expected return (simplified)
            expected_return = self._calculate_expected_return(
                action, target_price, market_analysis.current_price, time_horizon
            )
            
            # Create recommendation
            recommendation = Recommendation(
                symbol=market_analysis.symbol,
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                target_price=target_price,
                stop_loss=stop_loss,
                time_horizon=time_horizon.value,
                risk_factors=risk_factors,
                expected_return=expected_return,
                recommendation_timestamp=datetime.now().isoformat()
            )
            
            # Validate recommendation with guardrails
            validation_status, issues = self.guardrails.validate_recommendation(recommendation)
            
            if validation_status == ValidationStatus.FAILED:
                # Adjust recommendation if it fails validation
                recommendation.confidence *= 0.5
                recommendation.risk_factors.extend(issues)
                await self.log_activity(f"Recommendation validation failed, adjusted confidence", "warning")
            elif issues:
                recommendation.risk_factors.extend(issues)
                await self.log_activity(f"Recommendation validation warnings: {len(issues)}", "warning")
            
            await self.log_activity(
                f"Recommendation generated for {market_analysis.symbol}",
                data={
                    'action': action,
                    'confidence': confidence,
                    'total_score': total_score,
                    'target_price': target_price,
                    'time_horizon': time_horizon.value
                }
            )
            
            return recommendation
            
        except Exception as e:
            await self.log_activity(f"Failed to generate recommendation for {market_analysis.symbol}: {str(e)}", "error")
            raise
    
    def _generate_reasoning(self, model_results: Dict[str, Any], 
                          market_insights: Dict[str, Any], total_score: float) -> str:
        """Generate human-readable reasoning for the recommendation"""
        reasoning_parts = []
        
        # Add overall assessment
        if total_score > 2:
            reasoning_parts.append("Strong positive signals across multiple analysis models.")
        elif total_score > 0:
            reasoning_parts.append("Moderately positive signals with some supporting factors.")
        elif total_score < -2:
            reasoning_parts.append("Strong negative signals indicating downside risk.")
        elif total_score < 0:
            reasoning_parts.append("Moderately negative signals with caution advised.")
        else:
            reasoning_parts.append("Mixed signals suggest a neutral stance.")
        
        # Add key model insights
        for model_name, result in model_results.items():
            if result['score'] != 0 and result['signals']:
                key_signal = result['signals'][0]  # Take the first signal
                reasoning_parts.append(f"{model_name.replace('_', ' ').title()}: {key_signal}")
        
        # Add market insights if available
        if market_insights:
            market_sentiment = market_insights.get('market_sentiment', 'neutral')
            if market_sentiment != 'neutral':
                reasoning_parts.append(f"Market sentiment analysis indicates {market_sentiment} conditions.")
        
        return " ".join(reasoning_parts)
    
    def _calculate_expected_return(self, action: str, target_price: Optional[float], 
                                 current_price: float, time_horizon: TimeHorizon) -> Optional[float]:
        """Calculate expected return for the recommendation"""
        if not target_price:
            return None
        
        if action in [RecommendationAction.BUY.value, RecommendationAction.STRONG_BUY.value]:
            return (target_price - current_price) / current_price
        elif action in [RecommendationAction.SELL.value, RecommendationAction.STRONG_SELL.value]:
            return (current_price - target_price) / current_price
        else:
            return 0.0
    
    async def generate_portfolio_recommendations(self, analyses: List[MarketAnalysis],
                                               risk_assessments: List[RiskAssessment],
                                               portfolio_constraints: Dict[str, Any] = None) -> List[Recommendation]:
        """Generate recommendations for a portfolio of securities"""
        try:
            await self.log_activity(f"Generating portfolio recommendations for {len(analyses)} securities")
            
            if len(analyses) != len(risk_assessments):
                raise ValueError("Analyses and risk assessments must have same length")
            
            # Generate individual recommendations
            individual_recommendations = []
            for analysis, risk_assessment in zip(analyses, risk_assessments):
                try:
                    recommendation = await self.generate_comprehensive_recommendation(
                        analysis, risk_assessment
                    )
                    individual_recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"Failed to generate recommendation for {analysis.symbol}: {str(e)}")
            
            # Apply portfolio-level constraints and optimizations
            if portfolio_constraints:
                individual_recommendations = self._apply_portfolio_constraints(
                    individual_recommendations, portfolio_constraints
                )
            
            # Validate portfolio allocation
            validation_status, issues = self.guardrails.validate_portfolio_allocation(
                individual_recommendations
            )
            
            if validation_status != ValidationStatus.PASSED:
                await self.log_activity(f"Portfolio validation issues: {len(issues)}", "warning")
                # Adjust recommendations if needed
                individual_recommendations = self._adjust_for_portfolio_validation(
                    individual_recommendations, issues
                )
            
            await self.log_activity(
                f"Portfolio recommendations completed",
                data={
                    'total_securities': len(analyses),
                    'recommendations_generated': len(individual_recommendations),
                    'buy_recommendations': len([r for r in individual_recommendations if r.action in ['BUY', 'STRONG_BUY']]),
                    'sell_recommendations': len([r for r in individual_recommendations if r.action in ['SELL', 'STRONG_SELL']])
                }
            )
            
            return individual_recommendations
            
        except Exception as e:
            await self.log_activity(f"Portfolio recommendation generation failed: {str(e)}", "error")
            raise
    
    def _apply_portfolio_constraints(self, recommendations: List[Recommendation],
                                   constraints: Dict[str, Any]) -> List[Recommendation]:
        """Apply portfolio-level constraints to recommendations"""
        max_positions = constraints.get('max_positions', 10)
        max_risk_allocation = constraints.get('max_risk_allocation', 0.3)
        
        # Sort by confidence and filter to max positions
        buy_recommendations = [r for r in recommendations if r.action in ['BUY', 'STRONG_BUY']]
        buy_recommendations.sort(key=lambda x: x.confidence, reverse=True)
        
        # Keep only top recommendations up to max positions
        if len(buy_recommendations) > max_positions:
            excluded_recommendations = buy_recommendations[max_positions:]
            for rec in excluded_recommendations:
                rec.action = 'HOLD'
                rec.reasoning += " Excluded due to portfolio position limits."
            buy_recommendations = buy_recommendations[:max_positions]
        
        return recommendations
    
    def _adjust_for_portfolio_validation(self, recommendations: List[Recommendation],
                                       issues: List[str]) -> List[Recommendation]:
        """Adjust recommendations based on portfolio validation issues"""
        # Simple adjustment: reduce confidence for problematic recommendations
        for recommendation in recommendations:
            if any(issue in recommendation.reasoning for issue in issues):
                recommendation.confidence *= 0.8
                recommendation.risk_factors.append("Adjusted due to portfolio constraints")
        
        return recommendations
    
    async def process(self, input_data: Dict[str, Any]) -> Recommendation:
        """Main processing method"""
        try:
            # Extract required data
            risk_assessment_dict = input_data.get('risk_assessment', {})
            market_analysis_dict = input_data.get('market_analysis', {})
            market_insights = input_data.get('market_insights', {})
            
            if not risk_assessment_dict or not market_analysis_dict:
                raise ValueError("Risk assessment and market analysis data required")
            
            # Deserialize data
            risk_assessment = self._deserialize_risk_assessment(risk_assessment_dict)
            market_analysis = self._deserialize_market_analysis(market_analysis_dict)
            
            # Generate recommendation
            recommendation = await self.generate_comprehensive_recommendation(
                market_analysis, risk_assessment, market_insights
            )
            
            # Send to Report Generation Agent
            await self.send_mcp_message(
                target_agent="ReportGenerationAgent",
                message_type=MessageType.RECOMMENDATIONS_READY,
                data={
                    'recommendation': self._serialize_recommendation(recommendation),
                    'risk_assessment': risk_assessment_dict,
                    'market_analysis': market_analysis_dict,
                    'market_insights': market_insights
                },
                priority=Priority.HIGH if recommendation.action in [RecommendationAction.STRONG_BUY.value, RecommendationAction.STRONG_SELL.value] else Priority.MEDIUM
            )
            
            return recommendation
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def _deserialize_risk_assessment(self, data_dict: Dict[str, Any]) -> RiskAssessment:
        """Deserialize risk assessment from MCP message"""
        risk_metrics = RiskMetrics(**data_dict['risk_metrics'])
        
        return RiskAssessment(
            symbol=data_dict['symbol'],
            risk_metrics=risk_metrics,
            risk_level=RiskLevel(data_dict['risk_level']),
            confidence=data_dict['confidence'],
            risk_factors=data_dict['risk_factors'],
            assessment_timestamp=data_dict['assessment_timestamp'],
            methodology=data_dict.get('methodology', 'quantitative')
        )
    
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
    
    def _serialize_recommendation(self, recommendation: Recommendation) -> Dict[str, Any]:
        """Serialize recommendation for MCP transmission"""
        return {
            'symbol': recommendation.symbol,
            'action': recommendation.action,
            'confidence': recommendation.confidence,
            'reasoning': recommendation.reasoning,
            'target_price': recommendation.target_price,
            'stop_loss': recommendation.stop_loss,
            'time_horizon': recommendation.time_horizon,
            'risk_factors': recommendation.risk_factors,
            'expected_return': recommendation.expected_return,
            'recommendation_timestamp': recommendation.recommendation_timestamp
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "technical_analysis_recommendations",
            "risk_adjusted_recommendations", 
            "momentum_based_recommendations",
            "mean_reversion_recommendations",
            "portfolio_optimization",
            "price_target_calculation",
            "stop_loss_calculation",
            "time_horizon_determination",
            "multi_model_aggregation",
            "confidence_scoring"
        ]
    
    async def get_recommendation_statistics(self) -> Dict[str, Any]:
        """Get statistics about generated recommendations"""
        # This would track recommendation performance in a real system
        return {
            "models_available": list(self.recommendation_models.keys()),
            "model_weights": {"technical": 0.3, "risk_adjusted": 0.3, "momentum": 0.2, "mean_reversion": 0.2},
            "min_confidence_threshold": self.recommendation_config["min_confidence_threshold"],
            "last_updated": datetime.now().isoformat()
        }
    
    async def update_model_weights(self, new_weights: Dict[str, float]):
        """Update model weights for recommendation aggregation"""
        if abs(sum(new_weights.values()) - 1.0) > 0.01:
            raise ValueError("Model weights must sum to 1.0")
        
        # Update weights (this would be stored in configuration)
        for model_name, weight in new_weights.items():
            if model_name in self.recommendation_models:
                # Store in config (simplified - would use proper config management)
                pass
        
        await self.log_activity("Model weights updated", data=new_weights)
