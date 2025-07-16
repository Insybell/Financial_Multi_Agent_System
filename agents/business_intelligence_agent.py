import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from ..core.base_agent import BaseFinancialAgent
from ..core.models import FinancialData, MarketAnalysis, TechnicalIndicators
from ..core.enums import MessageType, Priority, MarketTrend, AnalysisType

logger = logging.getLogger(__name__)


class BusinessIntelligenceAgent(BaseFinancialAgent):
    """Agent responsible for market analysis and business intelligence generation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("BusinessIntelligenceAgent", config)
        self.analysis_cache = {}
        self.trend_history = {}
        
        # Technical analysis configuration
        self.ta_config = {
            "sma_periods": [20, 50, 200],
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "bb_period": 20,
            "bb_std": 2
        }
        
        # Register message handlers
        self.register_message_handler(MessageType.DATA_COLLECTED, self._handle_data_collected)
    
    async def _handle_data_collected(self, message):
        """Handle incoming data collection messages"""
        financial_data_dict = message.data.get('financial_data', {})
        financial_data = self._deserialize_financial_data(financial_data_dict)
        
        # Perform analysis
        analysis = await self.analyze_market_data(financial_data)
        
        # Send to next agent
        await self.send_mcp_message(
            target_agent="RiskAssessmentAgent",
            message_type=MessageType.ANALYSIS_COMPLETE,
            data={'market_analysis': self._serialize_market_analysis(analysis)},
            priority=Priority.MEDIUM,
            correlation_id=message.correlation_id
        )
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> TechnicalIndicators:
        """Calculate comprehensive technical indicators"""
        try:
            close_prices = data['Close']
            high_prices = data['High']
            low_prices = data['Low']
            volume = data['Volume'] if 'Volume' in data.columns else pd.Series([0] * len(data))
            
            # Simple Moving Averages
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1] if len(close_prices) >= 20 else close_prices.iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1] if len(close_prices) >= 50 else close_prices.iloc[-1]
            sma_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else close_prices.iloc[-1]
            
            # RSI Calculation
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not rsi.empty and not np.isnan(rsi.iloc[-1]) else 50.0
            
            # MACD Calculation
            exp1 = close_prices.ewm(span=12).mean()
            exp2 = close_prices.ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            macd_value = macd.iloc[-1] if not macd.empty else 0.0
            macd_signal_value = signal.iloc[-1] if not signal.empty else 0.0
            
            # Bollinger Bands
            bb_sma = close_prices.rolling(window=20).mean()
            bb_std = close_prices.rolling(window=20).std()
            bb_upper = (bb_sma + 2 * bb_std).iloc[-1] if len(close_prices) >= 20 else close_prices.iloc[-1] * 1.02
            bb_lower = (bb_sma - 2 * bb_std).iloc[-1] if len(close_prices) >= 20 else close_prices.iloc[-1] * 0.98
            bb_middle = bb_sma.iloc[-1] if len(close_prices) >= 20 else close_prices.iloc[-1]
            
            # Volume Analysis
            avg_volume = volume.rolling(window=20).mean().iloc[-1] if len(volume) >= 20 else volume.iloc[-1]
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            return TechnicalIndicators(
                sma_20=float(sma_20),
                sma_50=float(sma_50),
                sma_200=float(sma_200),
                rsi=float(rsi_value),
                macd=float(macd_value),
                macd_signal=float(macd_signal_value),
                bb_upper=float(bb_upper),
                bb_lower=float(bb_lower),
                bb_middle=float(bb_middle),
                volume_ratio=float(volume_ratio)
            )
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            # Return default indicators on error
            current_price = data['Close'].iloc[-1] if not data.empty else 100.0
            return TechnicalIndicators(
                sma_20=current_price,
                sma_50=current_price,
                sma_200=current_price,
                rsi=50.0,
                macd=0.0,
                macd_signal=0.0,
                bb_upper=current_price * 1.02,
                bb_lower=current_price * 0.98,
                bb_middle=current_price,
                volume_ratio=1.0
            )
    
    def determine_trend_strength(self, current_price: float, indicators: TechnicalIndicators) -> MarketTrend:
        """Determine market trend based on technical indicators"""
        trend_score = 0
        
        # Moving average trend analysis
        if current_price > indicators.sma_20 > indicators.sma_50:
            trend_score += 2
        elif current_price > indicators.sma_20:
            trend_score += 1
        elif current_price < indicators.sma_20 < indicators.sma_50:
            trend_score -= 2
        elif current_price < indicators.sma_20:
            trend_score -= 1
        
        # RSI momentum analysis
        if 30 < indicators.rsi < 70:
            trend_score += 1  # Healthy momentum
        elif indicators.rsi > 80:
            trend_score -= 1  # Overbought
        elif indicators.rsi < 20:
            trend_score -= 1  # Oversold
        
        # MACD analysis
        if indicators.macd > indicators.macd_signal and indicators.macd > 0:
            trend_score += 1
        elif indicators.macd < indicators.macd_signal and indicators.macd < 0:
            trend_score -= 1
        
        # Volume confirmation
        if indicators.volume_ratio > 1.2:
            # High volume strengthens the trend
            if trend_score > 0:
                trend_score += 1
            elif trend_score < 0:
                trend_score -= 1
        
        # Determine final trend
        if trend_score >= 3:
            return MarketTrend.BULLISH
        elif trend_score <= -3:
            return MarketTrend.BEARISH
        elif abs(trend_score) <= 1:
            return MarketTrend.NEUTRAL
        elif indicators.volume_ratio > 1.5:
            return MarketTrend.VOLATILE
        else:
            return MarketTrend.CONSOLIDATING
    
    def calculate_support_resistance(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        try:
            high_prices = data['High']
            low_prices = data['Low']
            close_prices = data['Close']
            
            # Recent highs and lows (last 50 periods)
            recent_data = data.tail(50) if len(data) > 50 else data
            
            # Resistance levels
            resistance_1 = recent_data['High'].max()
            resistance_2 = recent_data['High'].quantile(0.95)
            
            # Support levels
            support_1 = recent_data['Low'].min()
            support_2 = recent_data['Low'].quantile(0.05)
            
            current_price = close_prices.iloc[-1]
            
            return {
                'primary_resistance': float(resistance_1),
                'secondary_resistance': float(resistance_2),
                'primary_support': float(support_1),
                'secondary_support': float(support_2),
                'distance_to_resistance': float((resistance_1 - current_price) / current_price),
                'distance_to_support': float((current_price - support_1) / current_price)
            }
            
        except Exception as e:
            logger.error(f"Error calculating support/resistance: {str(e)}")
            current_price = data['Close'].iloc[-1] if not data.empty else 100.0
            return {
                'primary_resistance': current_price * 1.1,
                'secondary_resistance': current_price * 1.05,
                'primary_support': current_price * 0.9,
                'secondary_support': current_price * 0.95,
                'distance_to_resistance': 0.1,
                'distance_to_support': 0.1
            }
    
    def analyze_volume_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns and trends"""
        try:
            if 'Volume' not in data.columns:
                return {"trend": "no_data", "analysis": "Volume data not available"}
            
            volume = data['Volume']
            close_prices = data['Close']
            
            # Volume moving averages
            volume_ma_20 = volume.rolling(window=20).mean()
            current_volume = volume.iloc[-1]
            avg_volume = volume_ma_20.iloc[-1] if len(volume) >= 20 else volume.mean()
            
            # Volume trend analysis
            recent_volume_trend = volume.tail(10).mean() / volume.tail(20).head(10).mean() if len(volume) >= 20 else 1.0
            
            # Price-volume relationship
            price_changes = close_prices.pct_change()
            volume_price_correlation = price_changes.corr(volume.pct_change()) if len(volume) > 1 else 0.0
            
            # Volume breakout detection
            volume_breakout = current_volume > (avg_volume * 2) if avg_volume > 0 else False
            
            # Volume trend classification
            if recent_volume_trend > 1.2:
                volume_trend = "increasing"
            elif recent_volume_trend < 0.8:
                volume_trend = "decreasing"
            else:
                volume_trend = "stable"
            
            return {
                'trend': volume_trend,
                'current_vs_average': float(current_volume / avg_volume) if avg_volume > 0 else 1.0,
                'breakout_detected': volume_breakout,
                'price_volume_correlation': float(volume_price_correlation) if not np.isnan(volume_price_correlation) else 0.0,
                'trend_strength': float(recent_volume_trend),
                'analysis': f"Volume is {volume_trend} with {current_volume / avg_volume:.1f}x average volume"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing volume patterns: {str(e)}")
            return {"trend": "error", "analysis": f"Volume analysis failed: {str(e)}"}
    
    async def analyze_market_data(self, financial_data: FinancialData) -> MarketAnalysis:
        """Perform comprehensive market analysis"""
        try:
            await self.log_activity(f"Starting market analysis for {financial_data.symbol}")
            
            data = financial_data.data
            current_price = float(data['Close'].iloc[-1])
            
            # Calculate technical indicators
            technical_indicators = self.calculate_technical_indicators(data)
            
            # Determine trend
            trend = self.determine_trend_strength(current_price, technical_indicators)
            
            # Calculate support and resistance
            support_resistance = self.calculate_support_resistance(data)
            
            # Analyze volume patterns
            volume_analysis = self.analyze_volume_patterns(data)
            
            # Store trend history
            self.trend_history[financial_data.symbol] = {
                'timestamp': datetime.now().isoformat(),
                'trend': trend.value,
                'price': current_price
            }
            
            analysis = MarketAnalysis(
                symbol=financial_data.symbol,
                current_price=current_price,
                trend_strength=trend.value,
                technical_indicators=technical_indicators,
                volume_analysis=volume_analysis,
                support_resistance=support_resistance,
                data_quality=financial_data.data_quality,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            await self.log_activity(
                f"Market analysis completed for {financial_data.symbol}",
                data={
                    'trend': trend.value,
                    'current_price': current_price,
                    'rsi': technical_indicators.rsi,
                    'volume_trend': volume_analysis['trend']
                }
            )
            
            return analysis
            
        except Exception as e:
            await self.log_activity(f"Market analysis failed for {financial_data.symbol}: {str(e)}", "error")
            raise
    
    async def generate_market_insights(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Generate AI-powered market insights"""
        try:
            prompt = f"""
            Analyze the following financial market data and provide comprehensive business insights:
            
            Symbol: {analysis.symbol}
            Current Price: ${analysis.current_price:.2f}
            Market Trend: {analysis.trend_strength}
            RSI: {analysis.technical_indicators.rsi:.2f}
            MACD: {analysis.technical_indicators.macd:.4f}
            Volume Trend: {analysis.volume_analysis['trend']}
            Volume vs Average: {analysis.volume_analysis.get('current_vs_average', 1.0):.1f}x
            
            Support Levels: ${analysis.support_resistance['primary_support']:.2f}, ${analysis.support_resistance['secondary_support']:.2f}
            Resistance Levels: ${analysis.support_resistance['primary_resistance']:.2f}, ${analysis.support_resistance['secondary_resistance']:.2f}
            
            Please provide insights on:
            1. Current market sentiment and momentum
            2. Key technical levels and price targets
            3. Potential market catalysts or risks
            4. Trading opportunities and entry/exit points
            5. Short-term and medium-term outlook
            
            Format the response as JSON with the following structure:
            {{
                "market_sentiment": "bullish/bearish/neutral",
                "momentum_strength": "strong/moderate/weak",
                "key_levels": {{"support": [prices], "resistance": [prices]}},
                "opportunities": ["list of opportunities"],
                "risks": ["list of risks"],
                "short_term_outlook": "outlook description",
                "medium_term_outlook": "outlook description",
                "confidence_score": 0.0-1.0
            }}
            """
            
            response = await self.llm.ainvoke(prompt)
            insights = json.loads(response.content)
            
            # Add metadata
            insights['generated_at'] = datetime.now().isoformat()
            insights['analysis_type'] = AnalysisType.TECHNICAL.value
            insights['data_quality'] = analysis.data_quality
            
            return insights
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return self._generate_fallback_insights(analysis)
        except Exception as e:
            logger.error(f"Error generating market insights: {str(e)}")
            return self._generate_fallback_insights(analysis)
    
    def _generate_fallback_insights(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Generate basic insights when LLM fails"""
        sentiment = "neutral"
        if analysis.trend_strength == "bullish":
            sentiment = "bullish"
        elif analysis.trend_strength == "bearish":
            sentiment = "bearish"
        
        momentum = "moderate"
        if analysis.technical_indicators.rsi > 70 or analysis.technical_indicators.rsi < 30:
            momentum = "strong"
        elif 40 < analysis.technical_indicators.rsi < 60:
            momentum = "weak"
        
        return {
            "market_sentiment": sentiment,
            "momentum_strength": momentum,
            "key_levels": {
                "support": [analysis.support_resistance['primary_support']],
                "resistance": [analysis.support_resistance['primary_resistance']]
            },
            "opportunities": [f"Monitor {analysis.trend_strength} trend continuation"],
            "risks": ["Market volatility", "Technical breakdown"],
            "short_term_outlook": f"Price trending {analysis.trend_strength}",
            "medium_term_outlook": "Depends on volume confirmation",
            "confidence_score": analysis.data_quality * 0.8,
            "generated_at": datetime.now().isoformat(),
            "analysis_type": "fallback",
            "data_quality": analysis.data_quality
        }
    
    async def compare_market_performance(self, analyses: List[MarketAnalysis]) -> Dict[str, Any]:
        """Compare performance across multiple securities"""
        if not analyses:
            return {"error": "No analyses provided for comparison"}
        
        try:
            comparison_data = []
            for analysis in analyses:
                comparison_data.append({
                    'symbol': analysis.symbol,
                    'current_price': analysis.current_price,
                    'trend': analysis.trend_strength,
                    'rsi': analysis.technical_indicators.rsi,
                    'volume_ratio': analysis.volume_analysis.get('current_vs_average', 1.0),
                    'data_quality': analysis.data_quality
                })
            
            # Sort by different criteria
            by_momentum = sorted(comparison_data, key=lambda x: abs(x['rsi'] - 50), reverse=True)
            by_volume = sorted(comparison_data, key=lambda x: x['volume_ratio'], reverse=True)
            
            # Identify patterns
            bullish_count = sum(1 for data in comparison_data if data['trend'] == 'bullish')
            bearish_count = sum(1 for data in comparison_data if data['trend'] == 'bearish')
            
            market_breadth = {
                'total_analyzed': len(comparison_data),
                'bullish_count': bullish_count,
                'bearish_count': bearish_count,
                'bullish_percentage': (bullish_count / len(comparison_data)) * 100,
                'average_rsi': np.mean([data['rsi'] for data in comparison_data]),
                'high_volume_count': sum(1 for data in comparison_data if data['volume_ratio'] > 1.5)
            }
            
            return {
                'market_breadth': market_breadth,
                'top_momentum': by_momentum[:5],
                'top_volume': by_volume[:5],
                'comparison_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in market comparison: {str(e)}")
            return {"error": f"Comparison failed: {str(e)}"}
    
    async def process(self, input_data: Dict[str, Any]) -> MarketAnalysis:
        """Main processing method"""
        try:
            # Handle both direct financial data and serialized data
            if 'financial_data' in input_data:
                financial_data = self._deserialize_financial_data(input_data['financial_data'])
            else:
                # Assume input_data is the financial data itself
                financial_data = input_data
            
            # Perform market analysis
            analysis = await self.analyze_market_data(financial_data)
            
            # Generate insights
            insights = await self.generate_market_insights(analysis)
            
            # Send to Risk Assessment Agent
            await self.send_mcp_message(
                target_agent="RiskAssessmentAgent",
                message_type=MessageType.ANALYSIS_COMPLETE,
                data={
                    'market_analysis': self._serialize_market_analysis(analysis),
                    'market_insights': insights
                },
                priority=Priority.MEDIUM
            )
            
            return analysis
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def _deserialize_financial_data(self, data_dict: Dict[str, Any]) -> FinancialData:
        """Deserialize financial data from MCP message"""
        return FinancialData(
            symbol=data_dict['symbol'],
            data=pd.DataFrame.from_dict(data_dict['data'], orient='index'),
            info=data_dict['info'],
            timestamp=data_dict['timestamp'],
            data_quality=data_dict['data_quality'],
            source=data_dict['source'],
            metadata=data_dict.get('metadata', {})
        )
    
    def _serialize_market_analysis(self, analysis: MarketAnalysis) -> Dict[str, Any]:
        """Serialize market analysis for MCP transmission"""
        return {
            'symbol': analysis.symbol,
            'current_price': analysis.current_price,
            'trend_strength': analysis.trend_strength,
            'technical_indicators': {
                'sma_20': analysis.technical_indicators.sma_20,
                'sma_50': analysis.technical_indicators.sma_50,
                'sma_200': analysis.technical_indicators.sma_200,
                'rsi': analysis.technical_indicators.rsi,
                'macd': analysis.technical_indicators.macd,
                'macd_signal': analysis.technical_indicators.macd_signal,
                'bb_upper': analysis.technical_indicators.bb_upper,
                'bb_lower': analysis.technical_indicators.bb_lower,
                'bb_middle': analysis.technical_indicators.bb_middle,
                'volume_ratio': analysis.technical_indicators.volume_ratio
            },
            'volume_analysis': analysis.volume_analysis,
            'support_resistance': analysis.support_resistance,
            'data_quality': analysis.data_quality,
            'analysis_timestamp': analysis.analysis_timestamp
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "technical_analysis",
            "market_trend_identification",
            "support_resistance_calculation",
            "volume_pattern_analysis",
            "market_sentiment_analysis",
            "ai_powered_insights",
            "comparative_market_analysis",
            "real_time_indicator_calculation"
        ]
    
    async def get_trend_history(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get historical trend data"""
        if symbol:
            return self.trend_history.get(symbol, {})
        return self.trend_history
    
    async def reset_cache(self):
        """Reset analysis cache"""
        self.analysis_cache.clear()
        await self.log_activity("Analysis cache cleared")
