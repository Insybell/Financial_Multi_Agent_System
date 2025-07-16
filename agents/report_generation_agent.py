import asyncio
import json
import logging
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from core.base_agent import BaseFinancialAgent
from core.models import (
    FinancialReport, ReportSection, Recommendation, RiskAssessment, 
    MarketAnalysis, RiskMetrics, TechnicalIndicators
)
from core.enums import MessageType, Priority, ReportFormat, RiskLevel

logger = logging.getLogger(__name__)


class ReportGenerationAgent(BaseFinancialAgent):
    """Agent responsible for generating comprehensive financial reports"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("ReportGenerationAgent", config)
        
        # Report configuration
        self.report_config = {
            "default_format": ReportFormat.JSON,
            "include_charts": True,
            "chart_theme": "plotly_white",
            "max_chart_points": 500,
            "executive_summary_length": 300,  # words
        }
        
        # Report templates
        self.report_templates = {
            "individual_security": self.generate_individual_security_report,
            "portfolio": self.generate_portfolio_report,
            "market_overview": self.generate_market_overview_report,
            "risk_summary": self.generate_risk_summary_report
        }
        
        # Register message handlers
        self.register_message_handler(MessageType.RECOMMENDATIONS_READY, self._handle_recommendations_ready)
    
    async def _handle_recommendations_ready(self, message):
        """Handle incoming recommendation messages"""
        recommendation_dict = message.data.get('recommendation', {})
        risk_assessment_dict = message.data.get('risk_assessment', {})
        market_analysis_dict = message.data.get('market_analysis', {})
        market_insights = message.data.get('market_insights', {})
        
        # Deserialize data
        recommendation = self._deserialize_recommendation(recommendation_dict)
        risk_assessment = self._deserialize_risk_assessment(risk_assessment_dict)
        market_analysis = self._deserialize_market_analysis(market_analysis_dict)
        
        # Generate comprehensive report
        report = await self.generate_individual_security_report(
            market_analysis, risk_assessment, recommendation, market_insights
        )
        
        # Send completion notification
        await self.send_mcp_message(
            target_agent="TriageAgent",
            message_type=MessageType.REPORT_GENERATED,
            data={
                'report': self._serialize_report(report),
                'report_type': 'individual_security',
                'symbol': recommendation.symbol
            },
            priority=Priority.MEDIUM,
            correlation_id=message.correlation_id
        )
    
    async def generate_individual_security_report(self, market_analysis: MarketAnalysis,
                                                risk_assessment: RiskAssessment,
                                                recommendation: Recommendation,
                                                market_insights: Dict[str, Any] = None) -> FinancialReport:
        """Generate comprehensive report for individual security"""
        try:
            await self.log_activity(f"Generating individual security report for {market_analysis.symbol}")
            
            report_id = f"report_{market_analysis.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate executive summary
            executive_summary = await self._create_executive_summary(
                market_analysis, risk_assessment, recommendation, market_insights
            )
            
            # Generate market analysis section
            market_section = await self._create_market_analysis_section(
                market_analysis, market_insights
            )
            
            # Generate risk assessment section
            risk_section = await self._create_risk_assessment_section(risk_assessment)
            
            # Generate recommendations section
            recommendations_section = await self._create_recommendations_section(recommendation)
            
            # Generate appendices
            appendices = [
                await self._create_technical_indicators_section(market_analysis),
                await self._create_data_quality_section(market_analysis, risk_assessment)
            ]
            
            # Create comprehensive report
            report = FinancialReport(
                report_id=report_id,
                symbols=[market_analysis.symbol],
                executive_summary=executive_summary,
                market_analysis=market_section,
                risk_assessment=risk_section,
                recommendations=recommendations_section,
                appendices=appendices,
                generation_timestamp=datetime.now().isoformat(),
                report_type="individual_security",
                confidence_score=min(risk_assessment.confidence, recommendation.confidence)
            )
            
            await self.log_activity(
                f"Individual security report generated for {market_analysis.symbol}",
                data={
                    'report_id': report_id,
                    'sections': len([executive_summary, market_section, risk_section, recommendations_section]),
                    'appendices': len(appendices),
                    'confidence_score': report.confidence_score
                }
            )
            
            return report
            
        except Exception as e:
            await self.log_activity(f"Failed to generate report for {market_analysis.symbol}: {str(e)}", "error")
            raise
    
    async def _create_executive_summary(self, market_analysis: MarketAnalysis,
                                      risk_assessment: RiskAssessment,
                                      recommendation: Recommendation,
                                      market_insights: Dict[str, Any] = None) -> ReportSection:
        """Create executive summary section"""
        
        # Key metrics
        current_price = market_analysis.current_price
        risk_level = risk_assessment.risk_level.value
        action = recommendation.action
        confidence = recommendation.confidence
        
        # Generate AI-powered summary
        summary_prompt = f"""
        Create a concise executive summary for {market_analysis.symbol} financial analysis:
        
        Current Price: ${current_price:.2f}
        Market Trend: {market_analysis.trend_strength}
        Risk Level: {risk_level}
        Recommendation: {action} (Confidence: {confidence:.1%})
        Expected Return: {recommendation.expected_return:.1%} if available
        Time Horizon: {recommendation.time_horizon}
        
        Key Risk Factors: {len(risk_assessment.risk_factors)} identified
        Data Quality: {market_analysis.data_quality:.1%}
        
        Generate a professional 2-3 paragraph executive summary highlighting:
        1. Current market position and trend
        2. Key risks and opportunities
        3. Investment recommendation and rationale
        
        Keep it under 300 words and make it suitable for executive decision-making.
        """
        
        try:
            response = await self.llm.ainvoke(summary_prompt)
            summary_content = response.content
        except Exception as e:
            logger.error(f"LLM summary generation failed: {str(e)}")
            # Fallback summary
            summary_content = self._generate_fallback_summary(
                market_analysis, risk_assessment, recommendation
            )
        
        # Create charts for executive summary
        charts = []
        if self.report_config["include_charts"]:
            charts.append(self._create_price_trend_chart(market_analysis))
            charts.append(self._create_risk_metrics_chart(risk_assessment))
        
        return ReportSection(
            title="Executive Summary",
            content=summary_content,
            charts=charts,
            priority=Priority.CRITICAL,
            section_type="executive_summary"
        )
    
    def _generate_fallback_summary(self, market_analysis: MarketAnalysis,
                                 risk_assessment: RiskAssessment,
                                 recommendation: Recommendation) -> str:
        """Generate fallback summary when LLM fails"""
        return f"""
        Analysis Summary for {market_analysis.symbol}:
        
        Current market position shows {market_analysis.trend_strength} trend with price at ${market_analysis.current_price:.2f}. 
        Technical indicators suggest {market_analysis.technical_indicators.rsi:.0f} RSI level indicating 
        {'overbought' if market_analysis.technical_indicators.rsi > 70 else 'oversold' if market_analysis.technical_indicators.rsi < 30 else 'neutral'} conditions.
        
        Risk assessment indicates {risk_assessment.risk_level.value} risk level with {risk_assessment.risk_metrics.volatility:.1%} annualized volatility. 
        Maximum drawdown of {risk_assessment.risk_metrics.max_drawdown:.1%} and Sharpe ratio of {risk_assessment.risk_metrics.sharpe_ratio:.2f} 
        provide context for risk-adjusted performance expectations.
        
        Investment recommendation: {recommendation.action} with {recommendation.confidence:.0%} confidence. 
        {f'Target price: ${recommendation.target_price:.2f}' if recommendation.target_price else ''}
        {f'Stop loss: ${recommendation.stop_loss:.2f}' if recommendation.stop_loss else ''}
        Time horizon: {recommendation.time_horizon}. Key risks include market volatility and technical breakdown risks.
        """
    
    async def _create_market_analysis_section(self, market_analysis: MarketAnalysis,
                                            market_insights: Dict[str, Any] = None) -> ReportSection:
        """Create market analysis section"""
        
        content_parts = []
        
        # Current market position
        content_parts.append(f"**Current Market Position**")
        content_parts.append(f"Price: ${market_analysis.current_price:.2f}")
        content_parts.append(f"Trend: {market_analysis.trend_strength.title()}")
        content_parts.append(f"Data Quality: {market_analysis.data_quality:.1%}")
        content_parts.append("")
        
        # Technical indicators summary
        indicators = market_analysis.technical_indicators
        content_parts.append("**Technical Indicators**")
        content_parts.append(f"RSI (14): {indicators.rsi:.1f}")
        content_parts.append(f"MACD: {indicators.macd:.4f}")
        content_parts.append(f"Moving Averages: 20-day ${indicators.sma_20:.2f}, 50-day ${indicators.sma_50:.2f}")
        content_parts.append("")
        
        # Volume analysis
        volume = market_analysis.volume_analysis
        content_parts.append("**Volume Analysis**")
        content_parts.append(f"Volume Trend: {volume.get('trend', 'N/A').title()}")
        content_parts.append(f"Volume vs Average: {volume.get('current_vs_average', 1.0):.1f}x")
        content_parts.append("")
        
        # Support and resistance
        sr = market_analysis.support_resistance
        content_parts.append("**Key Levels**")
        content_parts.append(f"Support: ${sr.get('primary_support', 0):.2f}")
        content_parts.append(f"Resistance: ${sr.get('primary_resistance', 0):.2f}")
        
        # Add market insights if available
        if market_insights:
            content_parts.append("")
            content_parts.append("**Market Insights**")
            content_parts.append(f"Sentiment: {market_insights.get('market_sentiment', 'neutral').title()}")
            content_parts.append(f"Momentum: {market_insights.get('momentum_strength', 'moderate').title()}")
            
            opportunities = market_insights.get('opportunities', [])
            if opportunities:
                content_parts.append(f"Opportunities: {', '.join(opportunities[:3])}")
        
        # Create charts
        charts = []
        if self.report_config["include_charts"]:
            charts.extend([
                self._create_technical_indicators_chart(market_analysis),
                self._create_volume_analysis_chart(market_analysis)
            ])
        
        return ReportSection(
            title="Market Analysis",
            content="\n".join(content_parts),
            charts=charts,
            priority=Priority.HIGH,
            section_type="analysis"
        )
    
    async def _create_risk_assessment_section(self, risk_assessment: RiskAssessment) -> ReportSection:
        """Create risk assessment section"""
        
        content_parts = []
        metrics = risk_assessment.risk_metrics
        
        # Risk level summary
        content_parts.append(f"**Overall Risk Assessment**")
        content_parts.append(f"Risk Level: {risk_assessment.risk_level.value.title()}")
        content_parts.append(f"Assessment Confidence: {risk_assessment.confidence:.1%}")
        content_parts.append("")
        
        # Key risk metrics
        content_parts.append("**Risk Metrics**")
        content_parts.append(f"Volatility (Annual): {metrics.volatility:.1%}")
        content_parts.append(f"Value at Risk (95%): {metrics.var_95:.2%}")
        content_parts.append(f"Maximum Drawdown: {metrics.max_drawdown:.1%}")
        content_parts.append(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        content_parts.append(f"Beta: {metrics.beta:.2f}")
        content_parts.append("")
        
        # Risk factors
        if risk_assessment.risk_factors:
            content_parts.append("**Identified Risk Factors**")
            for i, factor in enumerate(risk_assessment.risk_factors[:5], 1):
                content_parts.append(f"{i}. {factor}")
            if len(risk_assessment.risk_factors) > 5:
                content_parts.append(f"... and {len(risk_assessment.risk_factors) - 5} more factors")
        
        # Risk interpretation
        content_parts.append("")
        content_parts.append("**Risk Interpretation**")
        
        if risk_assessment.risk_level == RiskLevel.LOW:
            content_parts.append("Low risk profile suitable for conservative investors. Limited volatility expected.")
        elif risk_assessment.risk_level == RiskLevel.MEDIUM:
            content_parts.append("Moderate risk profile with balanced risk-return characteristics.")
        elif risk_assessment.risk_level == RiskLevel.HIGH:
            content_parts.append("High risk profile requiring careful position sizing and risk management.")
        else:  # CRITICAL
            content_parts.append("Critical risk level. Extreme caution advised. Consider avoiding or minimal allocation.")
        
        # Create charts
        charts = []
        if self.report_config["include_charts"]:
            charts.append(self._create_risk_breakdown_chart(risk_assessment))
        
        return ReportSection(
            title="Risk Assessment",
            content="\n".join(content_parts),
            charts=charts,
            priority=Priority.HIGH,
            section_type="risks"
        )
    
    async def _create_recommendations_section(self, recommendation: Recommendation) -> ReportSection:
        """Create recommendations section"""
        
        content_parts = []
        
        # Primary recommendation
        content_parts.append("**Investment Recommendation**")
        content_parts.append(f"Action: {recommendation.action}")
        content_parts.append(f"Confidence: {recommendation.confidence:.1%}")
        content_parts.append(f"Time Horizon: {recommendation.time_horizon}")
        content_parts.append("")
        
        # Price targets
        if recommendation.target_price or recommendation.stop_loss:
            content_parts.append("**Price Targets**")
            if recommendation.target_price:
                content_parts.append(f"Target Price: ${recommendation.target_price:.2f}")
            if recommendation.stop_loss:
                content_parts.append(f"Stop Loss: ${recommendation.stop_loss:.2f}")
            if recommendation.expected_return:
                content_parts.append(f"Expected Return: {recommendation.expected_return:.1%}")
            content_parts.append("")
        
        # Reasoning
        content_parts.append("**Investment Rationale**")
        content_parts.append(recommendation.reasoning)
        content_parts.append("")
        
        # Risk considerations
        if recommendation.risk_factors:
            content_parts.append("**Risk Considerations**")
            for i, factor in enumerate(recommendation.risk_factors[:5], 1):
                content_parts.append(f"{i}. {factor}")
            if len(recommendation.risk_factors) > 5:
                content_parts.append(f"... and {len(recommendation.risk_factors) - 5} additional risk factors")
        
        # Implementation guidance
        content_parts.append("")
        content_parts.append("**Implementation Guidance**")
        
        if recommendation.action in ["BUY", "STRONG_BUY"]:
            content_parts.append("• Consider dollar-cost averaging for entry")
            content_parts.append("• Monitor key technical levels for optimal entry points")
            content_parts.append("• Set stop-loss orders to manage downside risk")
        elif recommendation.action in ["SELL", "STRONG_SELL"]:
            content_parts.append("• Consider gradual exit to minimize market impact")
            content_parts.append("• Monitor for any fundamental changes that might alter thesis")
            content_parts.append("• Evaluate tax implications of the sale")
        else:  # HOLD
            content_parts.append("• Continue monitoring key catalysts and technical levels")
            content_parts.append("• Review position size relative to overall portfolio")
            content_parts.append("• Set alerts for significant price movements")
        
        return ReportSection(
            title="Investment Recommendations",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.CRITICAL,
            section_type="recommendations"
        )
    
    async def _create_technical_indicators_section(self, market_analysis: MarketAnalysis) -> ReportSection:
        """Create technical indicators appendix section"""
        
        indicators = market_analysis.technical_indicators
        
        content_parts = []
        content_parts.append("**Detailed Technical Indicators**")
        content_parts.append("")
        
        content_parts.append("**Moving Averages**")
        content_parts.append(f"20-day SMA: ${indicators.sma_20:.2f}")
        content_parts.append(f"50-day SMA: ${indicators.sma_50:.2f}")
        content_parts.append(f"200-day SMA: ${indicators.sma_200:.2f}")
        content_parts.append("")
        
        content_parts.append("**Momentum Indicators**")
        content_parts.append(f"RSI (14): {indicators.rsi:.2f}")
        content_parts.append(f"MACD: {indicators.macd:.4f}")
        content_parts.append(f"MACD Signal: {indicators.macd_signal:.4f}")
        content_parts.append("")
        
        content_parts.append("**Bollinger Bands**")
        content_parts.append(f"Upper Band: ${indicators.bb_upper:.2f}")
        content_parts.append(f"Middle Band: ${indicators.bb_middle:.2f}")
        content_parts.append(f"Lower Band: ${indicators.bb_lower:.2f}")
        content_parts.append("")
        
        content_parts.append("**Volume Analysis**")
        content_parts.append(f"Volume Ratio: {indicators.volume_ratio:.2f}")
        
        return ReportSection(
            title="Technical Indicators Detail",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.LOW,
            section_type="appendix"
        )
    
    async def _create_data_quality_section(self, market_analysis: MarketAnalysis,
                                         risk_assessment: RiskAssessment) -> ReportSection:
        """Create data quality appendix section"""
        
        content_parts = []
        content_parts.append("**Data Quality Assessment**")
        content_parts.append("")
        
        content_parts.append(f"Market Data Quality: {market_analysis.data_quality:.1%}")
        content_parts.append(f"Risk Assessment Confidence: {risk_assessment.confidence:.1%}")
        content_parts.append(f"Analysis Timestamp: {market_analysis.analysis_timestamp}")
        content_parts.append(f"Risk Assessment Timestamp: {risk_assessment.assessment_timestamp}")
        content_parts.append("")
        
        content_parts.append("**Data Sources and Methodology**")
        content_parts.append("• Market data sourced from Yahoo Finance API")
        content_parts.append(f"• Risk methodology: {risk_assessment.methodology}")
        content_parts.append("• Technical indicators calculated using standard parameters")
        content_parts.append("• All timestamps in UTC")
        
        return ReportSection(
            title="Data Quality & Methodology",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.LOW,
            section_type="appendix"
        )
    
    def _create_price_trend_chart(self, market_analysis: MarketAnalysis) -> Dict[str, Any]:
        """Create price trend chart"""
        try:
            # Create mock price data for demonstration
            dates = pd.date_range(end=datetime.now(), periods=50, freq='D')
            np.random.seed(42)  # For consistent demo data
            base_price = market_analysis.current_price
            returns = np.random.normal(0.001, 0.02, 50)
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=dates,
                y=prices,
                mode='lines',
                name='Price',
                line=dict(color='blue', width=2)
            ))
            
            # Add moving averages
            sma_20 = [market_analysis.technical_indicators.sma_20] * len(dates)
            sma_50 = [market_analysis.technical_indicators.sma_50] * len(dates)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=sma_20,
                mode='lines',
                name='SMA 20',
                line=dict(color='orange', dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=sma_50,
                mode='lines', 
                name='SMA 50',
                line=dict(color='red', dash='dot')
            ))
            
            fig.update_layout(
                title=f"{market_analysis.symbol} Price Trend",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                template=self.report_config["chart_theme"],
                height=400
            )
            
            return {
                "type": "price_trend",
                "title": f"{market_analysis.symbol} Price Trend",
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating price trend chart: {str(e)}")
            return {"type": "price_trend", "error": str(e)}
    
    def _create_risk_metrics_chart(self, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Create risk metrics visualization"""
        try:
            metrics = risk_assessment.risk_metrics
            
            # Create radar chart for risk metrics
            categories = ['Volatility', 'VaR Impact', 'Max Drawdown', 'Beta Risk', 'Sharpe Quality']
            
            # Normalize metrics to 0-1 scale for radar chart
            values = [
                min(metrics.volatility / 0.5, 1.0),  # Normalize volatility
                min(abs(metrics.var_95) / 0.1, 1.0),  # Normalize VaR
                min(abs(metrics.max_drawdown) / 0.5, 1.0),  # Normalize drawdown
                min(abs(metrics.beta - 1.0), 1.0),  # Beta deviation from 1
                max(0, 1.0 - metrics.sharpe_ratio / 2.0)  # Inverse Sharpe (lower is better)
            ]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Risk Profile',
                line_color='red'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                title="Risk Metrics Profile",
                template=self.report_config["chart_theme"],
                height=400
            )
            
            return {
                "type": "risk_metrics",
                "title": "Risk Metrics Profile", 
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating risk metrics chart: {str(e)}")
            return {"type": "risk_metrics", "error": str(e)}
    
    def _create_technical_indicators_chart(self, market_analysis: MarketAnalysis) -> Dict[str, Any]:
        """Create technical indicators chart"""
        try:
            indicators = market_analysis.technical_indicators
            
            # Create subplot with RSI and MACD
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('RSI', 'MACD'),
                vertical_spacing=0.1
            )
            
            # RSI chart
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            # Mock RSI data trending to current value
            rsi_values = np.linspace(50, indicators.rsi, 30)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=rsi_values,
                mode='lines',
                name='RSI',
                line=dict(color='purple')
            ), row=1, col=1)
            
            # Add RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
            
            # MACD chart
            macd_values = np.linspace(0, indicators.macd, 30)
            signal_values = np.linspace(0, indicators.macd_signal, 30)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=macd_values,
                mode='lines',
                name='MACD',
                line=dict(color='blue')
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=signal_values,
                mode='lines',
                name='Signal',
                line=dict(color='red', dash='dash')
            ), row=2, col=1)
            
            fig.update_layout(
                title="Technical Indicators",
                template=self.report_config["chart_theme"],
                height=500,
                showlegend=True
            )
            
            return {
                "type": "technical_indicators",
                "title": "Technical Indicators",
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating technical indicators chart: {str(e)}")
            return {"type": "technical_indicators", "error": str(e)}
    
    def _create_volume_analysis_chart(self, market_analysis: MarketAnalysis) -> Dict[str, Any]:
        """Create volume analysis chart"""
        try:
            # Mock volume data
            dates = pd.date_range(end=datetime.now(), periods=20, freq='D')
            volume_ratio = market_analysis.technical_indicators.volume_ratio
            volumes = np.random.lognormal(np.log(1000000), 0.3, 20)
            volumes[-1] = volumes[-1] * volume_ratio  # Adjust last volume
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=dates,
                y=volumes,
                name='Volume',
                marker_color='lightblue'
            ))
            
            # Add average volume line
            avg_volume = np.mean(volumes[:-1])
            fig.add_hline(
                y=avg_volume,
                line_dash="dash",
                line_color="orange",
                annotation_text="Average Volume"
            )
            
            fig.update_layout(
                title="Volume Analysis",
                xaxis_title="Date",
                yaxis_title="Volume",
                template=self.report_config["chart_theme"],
                height=300
            )
            
            return {
                "type": "volume_analysis",
                "title": "Volume Analysis",
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating volume analysis chart: {str(e)}")
            return {"type": "volume_analysis", "error": str(e)}
    
    def _create_risk_breakdown_chart(self, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Create risk breakdown chart"""
        try:
            # Risk factor categories
            risk_categories = ["Market Risk", "Volatility Risk", "Liquidity Risk", "Technical Risk"]
            
            # Calculate risk scores based on metrics
            metrics = risk_assessment.risk_metrics
            risk_scores = [
                min(abs(metrics.beta - 1.0), 1.0),  # Market risk
                min(metrics.volatility / 0.5, 1.0),  # Volatility risk
                0.3,  # Liquidity risk (placeholder)
                min(abs(metrics.var_95) / 0.1, 1.0)  # Technical risk
            ]
            
            # Create horizontal bar chart
            fig = go.Figure()
            
            colors = ['red' if score > 0.7 else 'orange' if score > 0.4 else 'green' for score in risk_scores]
            
            fig.add_trace(go.Bar(
                y=risk_categories,
                x=risk_scores,
                orientation='h',
                marker_color=colors,
                name='Risk Level'
            ))
            
            fig.update_layout(
                title="Risk Breakdown Analysis",
                xaxis_title="Risk Score (0-1)",
                yaxis_title="Risk Category",
                template=self.report_config["chart_theme"],
                height=300
            )
            
            return {
                "type": "risk_breakdown",
                "title": "Risk Breakdown Analysis",
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating risk breakdown chart: {str(e)}")
            return {"type": "risk_breakdown", "error": str(e)}
    
    async def generate_portfolio_report(self, analyses: List[MarketAnalysis],
                                      risk_assessments: List[RiskAssessment],
                                      recommendations: List[Recommendation],
                                      portfolio_data: Dict[str, Any] = None) -> FinancialReport:
        """Generate comprehensive portfolio report"""
        try:
            await self.log_activity(f"Generating portfolio report for {len(analyses)} securities")
            
            report_id = f"portfolio_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            symbols = [analysis.symbol for analysis in analyses]
            
            # Generate portfolio executive summary
            executive_summary = await self._create_portfolio_executive_summary(
                analyses, risk_assessments, recommendations, portfolio_data
            )
            
            # Generate portfolio analysis section
            portfolio_section = await self._create_portfolio_analysis_section(
                analyses, risk_assessments, recommendations
            )
            
            # Generate portfolio risk section
            portfolio_risk_section = await self._create_portfolio_risk_section(
                risk_assessments, portfolio_data
            )
            
            # Generate portfolio recommendations section
            portfolio_recommendations_section = await self._create_portfolio_recommendations_section(
                recommendations
            )
            
            # Individual security appendices
            appendices = []
            for analysis, risk_assessment, recommendation in zip(analyses, risk_assessments, recommendations):
                appendix = await self._create_individual_security_appendix(
                    analysis, risk_assessment, recommendation
                )
                appendices.append(appendix)
            
            # Calculate overall confidence
            overall_confidence = np.mean([
                analysis.data_quality for analysis in analyses
            ] + [
                risk_assessment.confidence for risk_assessment in risk_assessments
            ] + [
                recommendation.confidence for recommendation in recommendations
            ])
            
            report = FinancialReport(
                report_id=report_id,
                symbols=symbols,
                executive_summary=executive_summary,
                market_analysis=portfolio_section,
                risk_assessment=portfolio_risk_section,
                recommendations=portfolio_recommendations_section,
                appendices=appendices,
                generation_timestamp=datetime.now().isoformat(),
                report_type="portfolio",
                confidence_score=overall_confidence
            )
            
            await self.log_activity(
                f"Portfolio report generated",
                data={
                    'report_id': report_id,
                    'securities_count': len(symbols),
                    'confidence_score': overall_confidence
                }
            )
            
            return report
            
        except Exception as e:
            await self.log_activity(f"Failed to generate portfolio report: {str(e)}", "error")
            raise
    
    async def _create_portfolio_executive_summary(self, analyses: List[MarketAnalysis],
                                                risk_assessments: List[RiskAssessment],
                                                recommendations: List[Recommendation],
                                                portfolio_data: Dict[str, Any] = None) -> ReportSection:
        """Create portfolio executive summary"""
        
        symbols = [analysis.symbol for analysis in analyses]
        total_securities = len(symbols)
        
        # Portfolio statistics
        buy_count = len([r for r in recommendations if r.action in ['BUY', 'STRONG_BUY']])
        sell_count = len([r for r in recommendations if r.action in ['SELL', 'STRONG_SELL']])
        hold_count = len([r for r in recommendations if r.action == 'HOLD'])
        
        avg_confidence = np.mean([r.confidence for r in recommendations])
        
        # Risk distribution
        risk_distribution = {}
        for risk_level in RiskLevel:
            count = len([ra for ra in risk_assessments if ra.risk_level == risk_level])
            risk_distribution[risk_level.value] = count
        
        # Generate summary content
        content = f"""
        **Portfolio Analysis Summary**
        
        This portfolio analysis covers {total_securities} securities with the following recommendation distribution:
        • Buy/Strong Buy: {buy_count} securities ({buy_count/total_securities:.0%})
        • Sell/Strong Sell: {sell_count} securities ({sell_count/total_securities:.0%})
        • Hold: {hold_count} securities ({hold_count/total_securities:.0%})
        
        **Risk Profile Distribution:**
        • Low Risk: {risk_distribution.get('low', 0)} securities
        • Medium Risk: {risk_distribution.get('medium', 0)} securities  
        • High Risk: {risk_distribution.get('high', 0)} securities
        • Critical Risk: {risk_distribution.get('critical', 0)} securities
        
        **Overall Assessment:**
        Average recommendation confidence is {avg_confidence:.0%}. The portfolio shows 
        {'strong bullish sentiment' if buy_count > sell_count + hold_count else 'mixed sentiment with balanced positioning' if buy_count > sell_count else 'defensive positioning with caution advised'}.
        Risk management should focus on the {risk_distribution.get('high', 0) + risk_distribution.get('critical', 0)} higher-risk positions.
        """
        
        # Create portfolio overview chart
        charts = []
        if self.report_config["include_charts"]:
            charts.append(self._create_portfolio_overview_chart(recommendations, risk_assessments))
        
        return ReportSection(
            title="Portfolio Executive Summary",
            content=content,
            charts=charts,
            priority=Priority.CRITICAL,
            section_type="executive_summary"
        )
    
    async def _create_portfolio_analysis_section(self, analyses: List[MarketAnalysis],
                                               risk_assessments: List[RiskAssessment],
                                               recommendations: List[Recommendation]) -> ReportSection:
        """Create portfolio analysis section"""
        
        content_parts = []
        
        # Portfolio composition
        content_parts.append("**Portfolio Composition**")
        for analysis in analyses:
            content_parts.append(f"• {analysis.symbol}: ${analysis.current_price:.2f} ({analysis.trend_strength})")
        content_parts.append("")
        
        # Correlation analysis (simplified)
        content_parts.append("**Diversification Analysis**")
        content_parts.append(f"Number of securities: {len(analyses)}")
        
        # Sector exposure (would be actual sectors in production)
        tech_symbols = [s for s in [a.symbol for a in analyses] if s in ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']]
        if tech_symbols:
            content_parts.append(f"Technology exposure: {len(tech_symbols)} positions ({len(tech_symbols)/len(analyses):.0%})")
        
        content_parts.append("")
        
        # Performance summary
        content_parts.append("**Performance Indicators**")
        avg_rsi = np.mean([a.technical_indicators.rsi for a in analyses])
        content_parts.append(f"Average RSI: {avg_rsi:.1f}")
        
        trend_counts = {}
        for analysis in analyses:
            trend = analysis.trend_strength
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        for trend, count in trend_counts.items():
            content_parts.append(f"{trend.title()} trend: {count} securities")
        
        return ReportSection(
            title="Portfolio Analysis",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.HIGH,
            section_type="analysis"
        )
    
    async def _create_portfolio_risk_section(self, risk_assessments: List[RiskAssessment],
                                           portfolio_data: Dict[str, Any] = None) -> ReportSection:
        """Create portfolio risk assessment section"""
        
        content_parts = []
        
        # Portfolio risk metrics
        content_parts.append("**Portfolio Risk Summary**")
        
        avg_volatility = np.mean([ra.risk_metrics.volatility for ra in risk_assessments])
        avg_sharpe = np.mean([ra.risk_metrics.sharpe_ratio for ra in risk_assessments])
        avg_beta = np.mean([ra.risk_metrics.beta for ra in risk_assessments])
        
        content_parts.append(f"Average Volatility: {avg_volatility:.1%}")
        content_parts.append(f"Average Sharpe Ratio: {avg_sharpe:.2f}")
        content_parts.append(f"Average Beta: {avg_beta:.2f}")
        content_parts.append("")
        
        # Risk concentration
        content_parts.append("**Risk Concentration**")
        high_risk_count = len([ra for ra in risk_assessments if ra.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]])
        if high_risk_count > 0:
            content_parts.append(f"⚠️ {high_risk_count} high-risk positions require attention")
        else:
            content_parts.append("✅ No critical risk concentrations identified")
        
        # Common risk factors
        all_risk_factors = []
        for ra in risk_assessments:
            all_risk_factors.extend(ra.risk_factors)
        
        # Count common risk factors
        from collections import Counter
        common_factors = Counter(all_risk_factors).most_common(5)
        
        if common_factors:
            content_parts.append("")
            content_parts.append("**Common Risk Factors**")
            for factor, count in common_factors:
                content_parts.append(f"• {factor} ({count} securities)")
        
        return ReportSection(
            title="Portfolio Risk Assessment",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.HIGH,
            section_type="risks"
        )
    
    async def _create_portfolio_recommendations_section(self, recommendations: List[Recommendation]) -> ReportSection:
        """Create portfolio recommendations section"""
        
        content_parts = []
        
        # Action summary
        actions = {}
        for rec in recommendations:
            actions[rec.action] = actions.get(rec.action, 0) + 1
        
        content_parts.append("**Portfolio Action Summary**")
        for action, count in actions.items():
            content_parts.append(f"• {action}: {count} securities")
        content_parts.append("")
        
        # Top recommendations
        high_confidence_recs = [r for r in recommendations if r.confidence > 0.7]
        high_confidence_recs.sort(key=lambda x: x.confidence, reverse=True)
        
        if high_confidence_recs:
            content_parts.append("**High Confidence Recommendations**")
            for rec in high_confidence_recs[:5]:
                content_parts.append(f"• {rec.symbol}: {rec.action} ({rec.confidence:.0%} confidence)")
            content_parts.append("")
        
        # Portfolio rebalancing suggestions
        content_parts.append("**Portfolio Management Recommendations**")
        
        buy_recs = [r for r in recommendations if r.action in ['BUY', 'STRONG_BUY']]
        sell_recs = [r for r in recommendations if r.action in ['SELL', 'STRONG_SELL']]
        
        if buy_recs:
            content_parts.append("**Recommended Additions:**")
            for rec in buy_recs:
                content_parts.append(f"• {rec.symbol}: {rec.reasoning[:100]}...")
        
        if sell_recs:
            content_parts.append("")
            content_parts.append("**Recommended Reductions:**")
            for rec in sell_recs:
                content_parts.append(f"• {rec.symbol}: {rec.reasoning[:100]}...")
        
        return ReportSection(
            title="Portfolio Recommendations",
            content="\n".join(content_parts),
            charts=[],
            priority=Priority.CRITICAL,
            section_type="recommendations"
        )
    
    async def _create_individual_security_appendix(self, analysis: MarketAnalysis,
                                                 risk_assessment: RiskAssessment,
                                                 recommendation: Recommendation) -> ReportSection:
        """Create individual security appendix"""
        
        content = f"""
        **{analysis.symbol} - Individual Analysis**
        
        Price: ${analysis.current_price:.2f}
        Trend: {analysis.trend_strength.title()}
        Risk Level: {risk_assessment.risk_level.value.title()}
        Recommendation: {recommendation.action} ({recommendation.confidence:.0%})
        
        Key Metrics:
        • RSI: {analysis.technical_indicators.rsi:.1f}
        • Volatility: {risk_assessment.risk_metrics.volatility:.1%}
        • Sharpe Ratio: {risk_assessment.risk_metrics.sharpe_ratio:.2f}
        
        {recommendation.reasoning}
        """
        
        return ReportSection(
            title=f"{analysis.symbol} Analysis",
            content=content,
            charts=[],
            priority=Priority.LOW,
            section_type="appendix"
        )
    
    def _create_portfolio_overview_chart(self, recommendations: List[Recommendation],
                                        risk_assessments: List[RiskAssessment]) -> Dict[str, Any]:
        """Create portfolio overview chart"""
        try:
            # Create scatter plot of risk vs return
            symbols = [rec.symbol for rec in recommendations]
            risks = [ra.risk_metrics.volatility for ra in risk_assessments]
            returns = [rec.expected_return or 0 for rec in recommendations]
            
            # Color by recommendation action
            colors = []
            for rec in recommendations:
                if rec.action in ['BUY', 'STRONG_BUY']:
                    colors.append('green')
                elif rec.action in ['SELL', 'STRONG_SELL']:
                    colors.append('red')
                else:
                    colors.append('gray')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=risks,
                y=returns,
                mode='markers+text',
                text=symbols,
                textposition="top center",
                marker=dict(
                    size=12,
                    color=colors,
                    line=dict(width=2, color='black')
                ),
                name='Securities'
            ))
            
            fig.update_layout(
                title="Portfolio Risk-Return Profile",
                xaxis_title="Risk (Volatility)",
                yaxis_title="Expected Return",
                template=self.report_config["chart_theme"],
                height=400
            )
            
            return {
                "type": "portfolio_overview",
                "title": "Portfolio Risk-Return Profile",
                "chart_html": fig.to_html(include_plotlyjs=False),
                "chart_json": fig.to_json()
            }
            
        except Exception as e:
            logger.error(f"Error creating portfolio overview chart: {str(e)}")
            return {"type": "portfolio_overview", "error": str(e)}
    
    async def process(self, input_data: Dict[str, Any]) -> FinancialReport:
        """Main processing method"""
        try:
            # Determine report type and generate accordingly
            if 'recommendation' in input_data:
                # Individual security report
                recommendation = self._deserialize_recommendation(input_data['recommendation'])
                risk_assessment = self._deserialize_risk_assessment(input_data['risk_assessment'])
                market_analysis = self._deserialize_market_analysis(input_data['market_analysis'])
                market_insights = input_data.get('market_insights', {})
                
                report = await self.generate_individual_security_report(
                    market_analysis, risk_assessment, recommendation, market_insights
                )
            else:
                raise ValueError("Unsupported report generation request")
            
            return report
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def _deserialize_recommendation(self, data_dict: Dict[str, Any]) -> Recommendation:
        """Deserialize recommendation from MCP message"""
        return Recommendation(
            symbol=data_dict['symbol'],
            action=data_dict['action'],
            confidence=data_dict['confidence'],
            reasoning=data_dict['reasoning'],
            target_price=data_dict.get('target_price'),
            stop_loss=data_dict.get('stop_loss'),
            time_horizon=data_dict['time_horizon'],
            risk_factors=data_dict['risk_factors'],
            expected_return=data_dict.get('expected_return'),
            recommendation_timestamp=data_dict['recommendation_timestamp']
        )
    
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
    
    def _serialize_report(self, report: FinancialReport) -> Dict[str, Any]:
        """Serialize report for MCP transmission"""
        return {
            'report_id': report.report_id,
            'symbols': report.symbols,
            'executive_summary': {
                'title': report.executive_summary.title,
                'content': report.executive_summary.content,
                'charts_count': len(report.executive_summary.charts)
            },
            'generation_timestamp': report.generation_timestamp,
            'report_type': report.report_type,
            'confidence_score': report.confidence_score,
            'sections_count': len([
                report.market_analysis,
                report.risk_assessment, 
                report.recommendations
            ]) + len(report.appendices)
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "individual_security_reports",
            "portfolio_reports",
            "market_overview_reports",
            "executive_summaries",
            "technical_analysis_visualization",
            "risk_assessment_visualization",
            "ai_powered_insights",
            "multi_format_output",
            "interactive_charts",
            "comprehensive_documentation"
        ]
    
    async def get_report_statistics(self) -> Dict[str, Any]:
        """Get report generation statistics"""
        return {
            "supported_formats": [fmt.value for fmt in ReportFormat],
            "chart_types": ["price_trend", "risk_metrics", "technical_indicators", "volume_analysis"],
            "report_types": list(self.report_templates.keys()),
            "default_configuration": self.report_config,
            "last_updated": datetime.now().isoformat()
        }
