import asyncio
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.data_collection_agent import DataCollectionAgent
from agents.business_intelligence_agent import BusinessIntelligenceAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.recommendation_agent import RecommendationAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.triage_agent import TriageAgent

from core.models import FinancialData, MarketAnalysis, RiskAssessment, Recommendation
from core.enums import RiskLevel, Priority, MessageType, ValidationStatus
from core.guardrails import FinancialGuardrails


class TestFinancialAgents:
    """Test suite for all financial agents"""
    
    @pytest.fixture
    def sample_financial_data(self):
        """Create sample financial data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic price data
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [100.0]
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        volumes = np.random.lognormal(15, 1, len(dates))
        
        data = pd.DataFrame({
            'Open': prices,
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices,
            'Volume': volumes
        }, index=dates)
        
        return FinancialData(
            symbol="TEST",
            data=data,
            info={"symbol": "TEST", "longName": "Test Company"},
            timestamp=datetime.now().isoformat(),
            data_quality=0.95,
            source="test_data",
            metadata={"test": True}
        )
    
    @pytest.fixture
    def sample_market_analysis(self, sample_financial_data):
        """Create sample market analysis for testing"""
        from core.models import TechnicalIndicators
        
        indicators = TechnicalIndicators(
            sma_20=105.0,
            sma_50=102.0,
            sma_200=100.0,
            rsi=55.0,
            macd=0.5,
            macd_signal=0.3,
            bb_upper=110.0,
            bb_lower=95.0,
            bb_middle=102.5,
            volume_ratio=1.2
        )
        
        return MarketAnalysis(
            symbol="TEST",
            current_price=106.0,
            trend_strength="bullish",
            technical_indicators=indicators,
            volume_analysis={"trend": "increasing", "current_vs_average": 1.2},
            support_resistance={"primary_support": 95.0, "primary_resistance": 110.0},
            data_quality=0.95,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    @pytest.fixture
    def sample_risk_assessment(self):
        """Create sample risk assessment for testing"""
        from core.models import RiskMetrics
        
        metrics = RiskMetrics(
            var_95=-0.025,
            var_99=-0.035,
            sharpe_ratio=1.2,
            max_drawdown=-0.15,
            volatility=0.18,
            beta=1.1,
            information_ratio=0.8,
            sortino_ratio=1.4
        )
        
        return RiskAssessment(
            symbol="TEST",
            risk_metrics=metrics,
            risk_level=RiskLevel.MEDIUM,
            confidence=0.85,
            risk_factors=["Market volatility", "Technical uncertainty"],
            assessment_timestamp=datetime.now().isoformat(),
            methodology="comprehensive_quantitative"
        )


class TestDataCollectionAgent(TestFinancialAgents):
    """Test Data Collection Agent"""
    
    @pytest.fixture
    def data_agent(self):
        return DataCollectionAgent()
    
    @pytest.mark.asyncio
    async def test_symbol_validation(self, data_agent):
        """Test symbol validation functionality"""
        # Valid symbols
        valid_symbols = ["AAPL", "MSFT", "GOOGL"]
        for symbol in valid_symbols:
            validation, issues = data_agent.guardrails.validate_symbol(symbol)
            assert validation == ValidationStatus.PASSED
            assert len(issues) == 0
        
        # Invalid symbols
        invalid_symbols = ["", "TOOLONG", "123", "SCAM"]
        for symbol in invalid_symbols:
            validation, issues = data_agent.guardrails.validate_symbol(symbol)
            assert validation in [ValidationStatus.FAILED, ValidationStatus.WARNING]
    
    @pytest.mark.asyncio
    async def test_data_quality_check(self, data_agent, sample_financial_data):
        """Test data quality assessment"""
        quality_score = data_agent.guardrails.check_data_quality(sample_financial_data.data)
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.8  # Should be high quality for our test data
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, data_agent):
        """Test caching mechanism"""
        # Mock yfinance to avoid actual API calls
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame({
                'Open': [100], 'High': [101], 'Low': [99], 'Close': [100.5], 'Volume': [1000000]
            })
            mock_ticker.return_value.info = {"symbol": "TEST"}
            
            # First call should fetch data
            data1 = await data_agent.collect_stock_data("TEST", "1d")
            assert data1.symbol == "TEST"
            
            # Second call should use cache
            data2 = await data_agent.collect_stock_data("TEST", "1d")
            assert data2.symbol == "TEST"
            
            # Should only call API once due to caching
            assert mock_ticker.call_count == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_collection(self, data_agent):
        """Test concurrent symbol processing"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.history.return_value = pd.DataFrame({
                'Open': [100], 'High': [101], 'Low': [99], 'Close': [100.5], 'Volume': [1000000]
            })
            mock_ticker.return_value.info = {"symbol": "TEST"}
            
            symbols = ["AAPL", "MSFT", "GOOGL"]
            results = await data_agent.collect_multiple_symbols(symbols)
            
            assert len(results) == len(symbols)
            for result in results:
                assert isinstance(result, FinancialData)
                assert result.symbol in symbols


class TestBusinessIntelligenceAgent(TestFinancialAgents):
    """Test Business Intelligence Agent"""
    
    @pytest.fixture
    def bi_agent(self):
        return BusinessIntelligenceAgent()
    
    @pytest.mark.asyncio
    async def test_technical_indicators_calculation(self, bi_agent, sample_financial_data):
        """Test technical indicators calculation"""
        indicators = bi_agent.calculate_technical_indicators(sample_financial_data.data)
        
        # Check that all required indicators are present
        assert hasattr(indicators, 'sma_20')
        assert hasattr(indicators, 'rsi')
        assert hasattr(indicators, 'macd')
        
        # Validate RSI range
        assert 0 <= indicators.rsi <= 100
        
        # Validate moving averages are positive
        assert indicators.sma_20 > 0
        assert indicators.sma_50 > 0
    
    @pytest.mark.asyncio
    async def test_trend_determination(self, bi_agent, sample_market_analysis):
        """Test market trend determination"""
        indicators = sample_market_analysis.technical_indicators
        current_price = sample_market_analysis.current_price
        
        trend = bi_agent.determine_trend_strength(current_price, indicators)
        assert trend.value in ["bullish", "bearish", "neutral", "volatile", "consolidating"]
    
    @pytest.mark.asyncio
    async def test_support_resistance_calculation(self, bi_agent, sample_financial_data):
        """Test support and resistance level calculation"""
        sr_levels = bi_agent.calculate_support_resistance(sample_financial_data.data)
        
        assert 'primary_support' in sr_levels
        assert 'primary_resistance' in sr_levels
        assert sr_levels['primary_resistance'] > sr_levels['primary_support']
    
    @pytest.mark.asyncio
    async def test_market_analysis_workflow(self, bi_agent, sample_financial_data):
        """Test complete market analysis workflow"""
        analysis = await bi_agent.analyze_market_data(sample_financial_data)
        
        assert isinstance(analysis, MarketAnalysis)
        assert analysis.symbol == sample_financial_data.symbol
        assert analysis.current_price > 0
        assert analysis.data_quality == sample_financial_data.data_quality


class TestRiskAssessmentAgent(TestFinancialAgents):
    """Test Risk Assessment Agent"""
    
    @pytest.fixture
    def risk_agent(self):
        return RiskAssessmentAgent()
    
    @pytest.mark.asyncio
    async def test_var_calculation(self, risk_agent):
        """Test Value at Risk calculation"""
        # Generate test returns
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))
        
        var_95 = risk_agent._calculate_var(returns, 0.95)
        var_99 = risk_agent._calculate_var(returns, 0.99)
        
        # VaR should be negative
        assert var_95 < 0
        assert var_99 < 0
        
        # 99% VaR should be more negative than 95% VaR
        assert var_99 < var_95
    
    @pytest.mark.asyncio
    async def test_sharpe_ratio_calculation(self, risk_agent):
        """Test Sharpe ratio calculation"""
        # Generate test returns with positive expected return
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.01, 0.02, 252))
        
        sharpe_ratio = risk_agent._calculate_sharpe_ratio(returns)
        
        # Should be positive for profitable strategy
        assert sharpe_ratio > 0
        
        # Test with zero volatility
        zero_vol_returns = pd.Series([0.01] * 252)
        sharpe_zero_vol = risk_agent._calculate_sharpe_ratio(zero_vol_returns)
        assert sharpe_zero_vol == 0  # Zero volatility case
    
    @pytest.mark.asyncio
    async def test_risk_level_determination(self, risk_agent):
        """Test risk level classification"""
        from core.models import RiskMetrics
        
        # Low risk metrics
        low_risk_metrics = RiskMetrics(
            var_95=-0.01, var_99=-0.015, sharpe_ratio=2.0, max_drawdown=-0.05,
            volatility=0.1, beta=0.8, information_ratio=1.5, sortino_ratio=2.2
        )
        
        risk_level = risk_agent._determine_overall_risk_level(0.2, low_risk_metrics)
        assert risk_level == RiskLevel.LOW
        
        # High risk metrics
        high_risk_metrics = RiskMetrics(
            var_95=-0.08, var_99=-0.12, sharpe_ratio=0.2, max_drawdown=-0.4,
            volatility=0.6, beta=2.0, information_ratio=-0.5, sortino_ratio=0.1
        )
        
        risk_level = risk_agent._determine_overall_risk_level(0.9, high_risk_metrics)
        assert risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @pytest.mark.asyncio
    async def test_comprehensive_risk_assessment(self, risk_agent, sample_market_analysis):
        """Test comprehensive risk assessment workflow"""
        risk_assessment = await risk_agent.assess_comprehensive_risk(sample_market_analysis)
        
        assert isinstance(risk_assessment, RiskAssessment)
        assert risk_assessment.symbol == sample_market_analysis.symbol
        assert 0.0 <= risk_assessment.confidence <= 1.0
        assert risk_assessment.risk_level in list(RiskLevel)


class TestRecommendationAgent(TestFinancialAgents):
    """Test Recommendation Agent"""
    
    @pytest.fixture
    def rec_agent(self):
        return RecommendationAgent()
    
    @pytest.mark.asyncio
    async def test_technical_recommendation_model(self, rec_agent, sample_market_analysis, sample_risk_assessment):
        """Test technical recommendation model"""
        result = rec_agent._technical_recommendation(sample_market_analysis, sample_risk_assessment)
        
        assert 'score' in result
        assert 'signals' in result
        assert 'model' in result
        assert result['model'] == 'technical'
        assert isinstance(result['signals'], list)
    
    @pytest.mark.asyncio
    async def test_risk_adjusted_recommendation_model(self, rec_agent, sample_market_analysis, sample_risk_assessment):
        """Test risk-adjusted recommendation model"""
        result = rec_agent._risk_adjusted_recommendation(sample_market_analysis, sample_risk_assessment)
        
        assert 'score' in result
        assert 'signals' in result
        assert result['model'] == 'risk_adjusted'
    
    @pytest.mark.asyncio
    async def test_price_targets_calculation(self, rec_agent, sample_market_analysis):
        """Test price target calculation"""
        target_price, stop_loss = rec_agent._calculate_price_targets(sample_market_analysis, "BUY")
        
        if target_price and stop_loss:
            assert target_price > sample_market_analysis.current_price
            assert stop_loss < sample_market_analysis.current_price
        
        # Test sell recommendation
        target_price_sell, stop_loss_sell = rec_agent._calculate_price_targets(sample_market_analysis, "SELL")
        
        if target_price_sell and stop_loss_sell:
            assert target_price_sell < sample_market_analysis.current_price
            assert stop_loss_sell > sample_market_analysis.current_price
    
    @pytest.mark.asyncio
    async def test_comprehensive_recommendation(self, rec_agent, sample_market_analysis, sample_risk_assessment):
        """Test comprehensive recommendation generation"""
        recommendation = await rec_agent.generate_comprehensive_recommendation(
            sample_market_analysis, sample_risk_assessment
        )
        
        assert isinstance(recommendation, Recommendation)
        assert recommendation.action in ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
        assert 0.0 <= recommendation.confidence <= 1.0
        assert recommendation.symbol == sample_market_analysis.symbol
        assert len(recommendation.reasoning) > 10  # Should have meaningful reasoning


class TestReportGenerationAgent(TestFinancialAgents):
    """Test Report Generation Agent"""
    
    @pytest.fixture
    def report_agent(self):
        return ReportGenerationAgent()
    
    @pytest.fixture
    def sample_recommendation(self):
        return Recommendation(
            symbol="TEST",
            action="BUY",
            confidence=0.75,
            reasoning="Strong technical indicators and favorable risk-reward ratio",
            target_price=120.0,
            stop_loss=95.0,
            time_horizon="3-6 months",
            risk_factors=["Market volatility", "Sector rotation risk"],
            expected_return=0.15,
            recommendation_timestamp=datetime.now().isoformat()
        )
    
    @pytest.mark.asyncio
    async def test_executive_summary_creation(self, report_agent, sample_market_analysis, 
                                            sample_risk_assessment, sample_recommendation):
        """Test executive summary generation"""
        summary = await report_agent._create_executive_summary(
            sample_market_analysis, sample_risk_assessment, sample_recommendation
        )
        
        assert summary.title == "Executive Summary"
        assert len(summary.content) > 100  # Should have substantial content
        assert summary.priority == Priority.CRITICAL
    
    @pytest.mark.asyncio
    async def test_chart_generation(self, report_agent, sample_market_analysis):
        """Test chart generation functionality"""
        price_chart = report_agent._create_price_trend_chart(sample_market_analysis)
        
        assert 'type' in price_chart
        assert price_chart['type'] == 'price_trend'
        assert 'chart_html' in price_chart or 'error' in price_chart
    
    @pytest.mark.asyncio
    async def test_individual_security_report(self, report_agent, sample_market_analysis,
                                            sample_risk_assessment, sample_recommendation):
        """Test complete individual security report generation"""
        report = await report_agent.generate_individual_security_report(
            sample_market_analysis, sample_risk_assessment, sample_recommendation
        )
        
        assert report.report_type == "individual_security"
        assert sample_market_analysis.symbol in report.symbols
        assert report.executive_summary is not None
        assert report.market_analysis is not None
        assert report.risk_assessment is not None
        assert report.recommendations is not None


class TestTriageAgent(TestFinancialAgents):
    """Test Triage Agent"""
    
    @pytest.fixture
    def triage_agent(self):
        return TriageAgent()
    
    @pytest.mark.asyncio
    async def test_priority_score_calculation(self, triage_agent):
        """Test priority score calculation"""
        # High priority request
        high_priority_request = {
            "symbol": "SPY",
            "priority": "urgent",
            "metadata": {
                "risk_level": "high",
                "data_quality": 0.9
            }
        }
        
        score = await triage_agent._calculate_priority_score(high_priority_request)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high priority
        
        # Low priority request
        low_priority_request = {
            "symbol": "TEST",
            "priority": "low",
            "metadata": {
                "risk_level": "low",
                "data_quality": 0.6
            }
        }
        
        low_score = await triage_agent._calculate_priority_score(low_priority_request)
        assert low_score < score  # Should be lower than high priority
    
    @pytest.mark.asyncio
    async def test_urgency_level_determination(self, triage_agent):
        """Test urgency level classification"""
        # Critical urgency
        critical_request = {"priority": "urgent", "metadata": {"risk_level": "critical"}}
        urgency = triage_agent._determine_urgency_level(0.9, critical_request)
        assert urgency == Priority.CRITICAL
        
        # Normal urgency
        normal_request = {"priority": "normal", "metadata": {"risk_level": "medium"}}
        urgency = triage_agent._determine_urgency_level(0.5, normal_request)
        assert urgency == Priority.MEDIUM
    
    @pytest.mark.asyncio
    async def test_processing_time_estimation(self, triage_agent):
        """Test processing time estimation"""
        # Quick analysis
        quick_time = triage_agent._estimate_processing_time("quick_quote", Priority.HIGH)
        assert quick_time >= 30  # Minimum time
        
        # Comprehensive analysis
        comprehensive_time = triage_agent._estimate_processing_time("individual_analysis", Priority.MEDIUM)
        assert comprehensive_time > quick_time
    
    @pytest.mark.asyncio
    async def test_agent_routing_recommendation(self, triage_agent):
        """Test agent routing recommendations"""
        request = {"type": "individual_analysis", "symbol": "AAPL"}
        agents = triage_agent._recommend_agent_routing(request, Priority.MEDIUM)
        
        # Should include core agents for individual analysis
        expected_agents = [
            "DataCollectionAgent",
            "BusinessIntelligenceAgent", 
            "RiskAssessmentAgent",
            "RecommendationAgent",
            "ReportGenerationAgent"
        ]
        
        for agent in expected_agents:
            assert agent in agents
    
    @pytest.mark.asyncio
    async def test_triage_workflow(self, triage_agent):
        """Test complete triage workflow"""
        request = {
            "symbol": "AAPL",
            "type": "individual_analysis",
            "priority": "high",
            "metadata": {
                "risk_level": "medium",
                "data_quality": 0.8
            }
        }
        
        triage_result = await triage_agent.triage_analysis_request(request)
        
        assert triage_result.symbol == "AAPL"
        assert 0.0 <= triage_result.priority_score <= 1.0
        assert triage_result.urgency_level in list(Priority)
        assert len(triage_result.recommended_agents) > 0
        assert triage_result.estimated_processing_time > 0


class TestGuardrails(TestFinancialAgents):
    """Test Financial Guardrails"""
    
    @pytest.fixture
    def guardrails(self):
        return FinancialGuardrails()
    
    def test_symbol_validation(self, guardrails):
        """Test symbol validation guardrails"""
        # Valid symbols
        valid_symbols = ["AAPL", "MSFT", "GOOGL", "BRK.A"]
        for symbol in valid_symbols:
            status, issues = guardrails.validate_symbol(symbol)
            assert status == ValidationStatus.PASSED
        
        # Invalid symbols
        invalid_symbols = ["SCAM", "", "TOOLONG", "123456"]
        for symbol in invalid_symbols:
            status, issues = guardrails.validate_symbol(symbol)
            assert status in [ValidationStatus.FAILED, ValidationStatus.WARNING]
    
    def test_recommendation_validation(self, guardrails, sample_recommendation):
        """Test recommendation validation"""
        status, issues = guardrails.validate_recommendation(sample_recommendation)
        assert status in [ValidationStatus.PASSED, ValidationStatus.WARNING]
        
        # Test invalid recommendation
        invalid_rec = Recommendation(
            symbol="TEST",
            action="INVALID_ACTION",
            confidence=1.5,  # Invalid confidence > 1.0
            reasoning="",
            target_price=-10,  # Invalid negative price
            stop_loss=None,
            time_horizon="1-3 months",
            risk_factors=[],
            expected_return=None,
            recommendation_timestamp=datetime.now().isoformat()
        )
        
        status, issues = guardrails.validate_recommendation(invalid_rec)
        assert status == ValidationStatus.FAILED
        assert len(issues) > 0
    
    def test_data_quality_assessment(self, guardrails, sample_financial_data):
        """Test data quality assessment"""
        quality_score = guardrails.check_data_quality(sample_financial_data.data)
        assert 0.0 <= quality_score <= 1.0
        
        # Test with poor quality data
        poor_data = pd.DataFrame({
            'Close': [100, np.nan, np.nan, 100, 100],
            'Volume': [1000, 1000, 1000, 1000, 1000]
        })
        
        poor_quality = guardrails.check_data_quality(poor_data)
        assert poor_quality < quality_score


class TestIntegration(TestFinancialAgents):
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, sample_financial_data):
        """Test complete end-to-end workflow"""
        # Initialize agents
        data_agent = DataCollectionAgent()
        bi_agent = BusinessIntelligenceAgent()
        risk_agent = RiskAssessmentAgent()
        rec_agent = RecommendationAgent()
        report_agent = ReportGenerationAgent()
        
        # Mock data collection to use sample data
        with patch.object(data_agent, 'collect_stock_data', return_value=sample_financial_data):
            # Step 1: Data Collection
            financial_data = await data_agent.collect_stock_data("TEST")
            assert financial_data.symbol == "TEST"
            
            # Step 2: Business Intelligence Analysis
            market_analysis = await bi_agent.analyze_market_data(financial_data)
            assert isinstance(market_analysis, MarketAnalysis)
            
            # Step 3: Risk Assessment
            risk_assessment = await risk_agent.assess_comprehensive_risk(market_analysis)
            assert isinstance(risk_assessment, RiskAssessment)
            
            # Step 4: Recommendation Generation
            recommendation = await rec_agent.generate_comprehensive_recommendation(
                market_analysis, risk_assessment
            )
            assert isinstance(recommendation, Recommendation)
            
            # Step 5: Report Generation
            report = await report_agent.generate_individual_security_report(
                market_analysis, risk_assessment, recommendation
            )
            assert report.report_type == "individual_security"
    
    @pytest.mark.asyncio
    async def test_agent_communication_flow(self):
        """Test MCP message communication between agents"""
        from core.models import MCPMessage
        
        # Create test agents
        data_agent = DataCollectionAgent()
        bi_agent = BusinessIntelligenceAgent()
        
        # Test message sending
        message_id = await data_agent.send_mcp_message(
            target_agent="BusinessIntelligenceAgent",
            message_type=MessageType.DATA_COLLECTED,
            data={"test": "data"},
            priority=Priority.MEDIUM
        )
        
        assert isinstance(message_id, str)
        assert len(data_agent.message_history) > 0
        
        # Verify message structure
        last_message = data_agent.message_history[-1]
        assert last_message.source_agent == "DataCollectionAgent"
        assert last_message.target_agent == "BusinessIntelligenceAgent"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test system error handling and recovery"""
        data_agent = DataCollectionAgent()
        
        # Test invalid symbol handling
        try:
            await data_agent.collect_stock_data("INVALID_SYMBOL_TEST")
        except Exception as e:
            # Should handle gracefully
            assert isinstance(e, (ValueError, ConnectionError))
        
        # Test agent health after error
        health = await data_agent.health_check()
        assert 'agent_name' in health
        assert 'status' in health
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, sample_financial_data):
        """Test system performance with multiple concurrent requests"""
        data_agent = DataCollectionAgent()
        
        # Mock multiple symbol requests
        symbols = [f"TEST{i}" for i in range(10)]
        
        with patch.object(data_agent, 'collect_stock_data', return_value=sample_financial_data):
            start_time = datetime.now()
            
            # Process multiple symbols concurrently
            results = await data_agent.collect_multiple_symbols(symbols)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Should complete within reasonable time
            assert processing_time < 30  # 30 seconds max
            assert len(results) == len(symbols)


class TestMCPIntegration:
    """Test MCP protocol integration"""
    
    @pytest.mark.asyncio
    async def test_mcp_server_startup(self):
        """Test MCP server initialization"""
        from mcp.mcp_server import FinancialMCPServer
        
        server = FinancialMCPServer("test_server")
        assert server.server_name == "test_server"
        assert len(server.registered_agents) == 0
        
        # Test server info
        info = server.get_server_info()
        assert info['server_name'] == "test_server"
        assert 'capabilities' in info
    
    @pytest.mark.asyncio
    async def test_mcp_client_connection(self):
        """Test MCP client connection (mocked)"""
        from mcp.mcp_client import FinancialMCPClient
        
        # Mock the connection for testing
        client = FinancialMCPClient()
        
        # Test client initialization
        assert client.client_id is not None
        assert client.connected is False
        
        # Test health check when not connected
        health = await client.health_check()
        assert health['status'] == 'disconnected'


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow  # Mark as slow test
    async def test_data_collection_performance(self):
        """Benchmark data collection performance"""
        data_agent = DataCollectionAgent()
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Setup mock to return data quickly
            mock_ticker.return_value.history.return_value = pd.DataFrame({
                'Open': [100], 'High': [101], 'Low': [99], 
                'Close': [100.5], 'Volume': [1000000]
            })
            mock_ticker.return_value.info = {"symbol": "TEST"}
            
            # Benchmark single symbol
            start_time = datetime.now()
            await data_agent.collect_stock_data("TEST")
            single_time = (datetime.now() - start_time).total_seconds()
            
            # Benchmark multiple symbols
            symbols = ["TEST"] * 10
            start_time = datetime.now()
            await data_agent.collect_multiple_symbols(symbols)
            multi_time = (datetime.now() - start_time).total_seconds()
            
            # Concurrent should be faster than sequential
            expected_sequential_time = single_time * len(symbols)
            assert multi_time < expected_sequential_time
            
            print(f"Single symbol: {single_time:.3f}s")
            print(f"10 symbols concurrent: {multi_time:.3f}s")
            print(f"Speedup: {expected_sequential_time/multi_time:.1f}x")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_analysis_pipeline_performance(self, sample_financial_data):
        """Benchmark complete analysis pipeline"""
        # Initialize agents
        bi_agent = BusinessIntelligenceAgent()
        risk_agent = RiskAssessmentAgent()
        rec_agent = RecommendationAgent()
        
        # Benchmark each stage
        stages = []
        
        # BI Analysis
        start_time = datetime.now()
        market_analysis = await bi_agent.analyze_market_data(sample_financial_data)
        bi_time = (datetime.now() - start_time).total_seconds()
        stages.append(("Business Intelligence", bi_time))
        
        # Risk Assessment
        start_time = datetime.now()
        risk_assessment = await risk_agent.assess_comprehensive_risk(market_analysis)
        risk_time = (datetime.now() - start_time).total_seconds()
        stages.append(("Risk Assessment", risk_time))
        
        # Recommendation
        start_time = datetime.now()
        recommendation = await rec_agent.generate_comprehensive_recommendation(
            market_analysis, risk_assessment
        )
        rec_time = (datetime.now() - start_time).total_seconds()
        stages.append(("Recommendation", rec_time))
        
        total_time = sum(time for _, time in stages)
        
        # Print performance results
        print("\nAnalysis Pipeline Performance:")
        for stage, time in stages:
            print(f"  {stage}: {time:.3f}s")
        print(f"  Total: {total_time:.3f}s")
        
        # Should complete within reasonable time
        assert total_time < 10  # 10 seconds max for complete analysis


# Pytest configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test runner configuration
if __name__ == "__main__":
    # Run specific test categories
    import subprocess
    import sys
    
    print("Running Financial Multi-Agent System Tests...")
    
    # Run different test categories
    test_commands = [
        ["pytest", __file__ + "::TestDataCollectionAgent", "-v"],
        ["pytest", __file__ + "::TestBusinessIntelligenceAgent", "-v"],
        ["pytest", __file__ + "::TestRiskAssessmentAgent", "-v"],
        ["pytest", __file__ + "::TestRecommendationAgent", "-v"],
        ["pytest", __file__ + "::TestGuardrails", "-v"],
        ["pytest", __file__ + "::TestIntegration", "-v"],
    ]
    
    for cmd in test_commands:
        print(f"\nRunning: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PASSED")
            else:
                print("❌ FAILED")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"Error running tests: {e}")
    
    # Run performance benchmarks separately
    print("\nRunning Performance Benchmarks...")
    perf_cmd = ["pytest", __file__ + "::TestPerformanceBenchmarks", "-v", "-m", "slow"]
    try:
        subprocess.run(perf_cmd)
    except Exception as e:
        print(f"Performance benchmark error: {e}")
    
    print("\nTest suite completed!")
