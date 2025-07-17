# tests/test_mcp_integration.py
"""Test MCP integration with IDE development features"""

import asyncio
import pytest
import json
import logging
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MCP modules
from mcp.mcp_client import FinancialMCPClient, client_manager
from mcp.dev_server import FinancialDevMCPServer
from mcp.ide_integration import IDEMCPIntegration
from mcp.live_data_mcp import LiveFinancialDataMCP
from mcp.interactive_dashboard import InteractiveDashboard

logger = logging.getLogger(__name__)


class TestMCPIntegration:
    """Test MCP integration with IDE development features"""
    
    @pytest.fixture
    async def mcp_server(self):
        """Create test MCP server"""
        server = FinancialDevMCPServer("test_server")
        return server
    
    @pytest.fixture
    async def mcp_client(self):
        """Create test MCP client"""
        client = FinancialMCPClient()
        # Mock the connection for testing
        client.connected = True
        client.session = AsyncMock()
        return client
    
    @pytest.fixture
    async def ide_integration(self):
        """Create test IDE integration"""
        integration = IDEMCPIntegration("test_ide_client")
        # Mock the client connection
        integration.client = AsyncMock()
        integration.client.connected = True
        return integration
    
    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self, mcp_server):
        """Test MCP server initialization"""
        assert mcp_server.server_name == "test_server"
        assert len(mcp_server.registered_agents) == 0
        assert len(mcp_server.active_workflows) == 0
        
        # Test server info
        info = mcp_server.get_server_info()
        assert info['server_name'] == "test_server"
        assert 'capabilities' in info
        assert len(info['capabilities']) > 0
    
    @pytest.mark.asyncio
    async def test_mcp_client_connection(self, mcp_client):
        """Test MCP client connection functionality"""
        # Test client initialization
        assert mcp_client.client_id is not None
        assert mcp_client.connected is True
        
        # Test health check
        with patch.object(mcp_client, 'get_server_metrics', return_value={"status": "healthy"}):
            health = await mcp_client.health_check()
            assert health['status'] == 'healthy'
            assert health['connected'] is True
    
    @pytest.mark.asyncio
    async def test_financial_code_generation(self, ide_integration):
        """Test MCP financial code generation capabilities"""
        # Mock the tool call response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "status": "success",
            "agent_type": "risk_calculator",
            "code": "def calculate_var(returns, confidence=0.95):\n    return np.percentile(returns, (1-confidence)*100)",
            "imports": ["import numpy as np"],
            "tests": "def test_calculate_var():\n    pass"
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await ide_integration.get_code_completion(
            "def calculate_var", 15, "python"
        )
        
        assert "completions" in result
        # Verify the tool was called correctly
        ide_integration.client.session.call_tool.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_financial_code_validation(self, ide_integration):
        """Test real-time financial code validation"""
        # Mock validation response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "valid": True,
            "errors": [],
            "warnings": ["Consider specifying risk_free_rate parameter"],
            "suggestions": ["Add error handling for empty returns"]
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        test_code = "sharpe_ratio = calculate_sharpe_ratio(returns)"
        result = await ide_integration.validate_financial_code(test_code, "risk_analysis")
        
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert "risk_free_rate" in result["warnings"][0]
    
    @pytest.mark.asyncio
    async def test_live_data_streaming(self, ide_integration):
        """Test real-time data streaming via MCP"""
        # Mock live data stream response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "stream_id": "test_stream_123",
            "symbols": ["AAPL", "MSFT"],
            "websocket_url": "ws://localhost:8001/stream/test_stream_123",
            "status": "active"
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await ide_integration.start_live_data_stream(["AAPL", "MSFT"], 1000)
        
        assert result["status"] == "active"
        assert "stream_id" in result
        assert "websocket_url" in result
        assert result["symbols"] == ["AAPL", "MSFT"]
    
    @pytest.mark.asyncio
    async def test_development_dashboard_creation(self, ide_integration):
        """Test development dashboard creation"""
        # Mock dashboard creation response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "dashboard_url": "http://localhost:8000/dev-dashboard",
            "dashboard_html": "<html>Dashboard Content</html>",
            "websocket_endpoint": "ws://localhost:8000/dev-ws",
            "features": ["agent_monitoring", "live_data", "performance_metrics"]
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        agent_types = ["DataCollectionAgent", "RiskAssessmentAgent"]
        result = await ide_integration.create_development_dashboard(agent_types)
        
        assert "dashboard_url" in result
        assert "dashboard_html" in result
        assert "websocket_endpoint" in result
    
    @pytest.mark.asyncio
    async def test_code_performance_analysis(self, ide_integration):
        """Test code performance analysis"""
        # Mock performance analysis response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "performance_score": 0.85,
            "bottlenecks": ["Loop in pandas operation"],
            "optimizations": [{
                "type": "vectorization",
                "description": "Use pandas built-in methods",
                "impact": "high"
            }],
            "execution_time_estimate": "< 50ms"
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        test_code = """
        for i in range(len(df)):
            df.loc[i, 'result'] = df.loc[i, 'value'] * 2
        """
        
        result = await ide_integration.analyze_code_performance(test_code)
        
        assert result["performance_score"] == 0.85
        assert len(result["optimizations"]) > 0
        assert "vectorization" in result["optimizations"][0]["type"]
    
    @pytest.mark.asyncio
    async def test_agent_registration_and_communication(self, mcp_client):
        """Test agent registration and communication flow"""
        # Mock agent registration
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "status": "registered",
            "agent_name": "TestAgent",
            "capabilities_count": 3
        })
        
        mcp_client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await mcp_client.register_agent(
            agent_name="TestAgent",
            capabilities=["data_analysis", "risk_calculation", "reporting"],
            status="active"
        )
        
        assert result["status"] == "registered"
        assert result["agent_name"] == "TestAgent"
    
    @pytest.mark.asyncio
    async def test_workflow_management(self, mcp_client):
        """Test workflow creation and monitoring"""
        # Mock workflow creation
        mock_workflow_response = Mock()
        mock_workflow_response.content = [Mock()]
        mock_workflow_response.content[0].text = json.dumps({
            "workflow_id": "test_workflow_123",
            "status": "initiated",
            "symbols": ["AAPL"],
            "estimated_completion_time": "3-5 minutes"
        })
        
        # Mock workflow status check
        mock_status_response = Mock()
        mock_status_response.content = [Mock()]
        mock_status_response.content[0].text = json.dumps({
            "workflow_id": "test_workflow_123",
            "status": "completed",
            "progress": "100%",
            "current_step": "completed"
        })
        
        mcp_client.session.call_tool = AsyncMock(side_effect=[mock_workflow_response, mock_status_response])
        
        # Start workflow
        workflow_result = await mcp_client.analyze_symbols(["AAPL"], "comprehensive", "high")
        assert workflow_result["status"] == "initiated"
        assert "workflow_id" in workflow_result
        
        # Check workflow status
        status_result = await mcp_client.get_workflow_status(workflow_result["workflow_id"])
        assert status_result["status"] == "completed"
        assert status_result["progress"] == "100%"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, ide_integration):
        """Test error handling in MCP integration"""
        # Test connection error handling
        ide_integration.client = None
        
        result = await ide_integration.get_code_completion("test", 0)
        assert "error" in result
        assert "not initialized" in result["error"]
        
        # Test with mock client that raises exception
        ide_integration.client = AsyncMock()
        ide_integration.client.session.call_tool.side_effect = Exception("Network error")
        
        result = await ide_integration.validate_financial_code("test code", "test")
        assert "error" in result
        assert "Network error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_live_data_mcp_functionality(self):
        """Test live data MCP functionality"""
        live_data = LiveFinancialDataMCP()
        
        try:
            # Test stream creation
            symbols = ["AAPL", "MSFT"]
            stream_result = await live_data.stream_market_data(symbols, 5000)
            
            assert "stream_id" in stream_result
            assert stream_result["symbols"] == symbols
            assert stream_result["status"] == "active"
            
            # Test stream data retrieval
            stream_id = stream_result["stream_id"]
            data_result = await live_data.get_stream_data(stream_id)
            
            assert data_result["stream_id"] == stream_id
            assert "stream_info" in data_result
            
            # Test risk monitoring
            portfolio = {"AAPL": 0.6, "MSFT": 0.4}
            risk_result = await live_data.live_risk_monitoring(portfolio)
            
            assert "monitor_id" in risk_result
            assert risk_result["status"] == "monitoring"
            
            # Test stream cleanup
            stop_result = await live_data.stop_stream(stream_id)
            assert stop_result["status"] == "stopped"
            
        finally:
            await live_data.cleanup()
    
    @pytest.mark.asyncio
    async def test_interactive_dashboard_generation(self):
        """Test interactive dashboard generation"""
        dashboard = InteractiveDashboard()
        
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        # Test comprehensive dashboard
        result = await dashboard.create_analysis_dashboard(symbols, "comprehensive")
        
        assert "dashboard_id" in result
        assert "dashboard_html" in result
        assert "websocket_endpoint" in result
        assert result["symbols"] == symbols
        assert result["dashboard_type"] == "comprehensive"
        
        # Verify HTML contains required components
        html_content = result["dashboard_html"]
        assert "price-chart" in html_content
        assert "technical-indicators" in html_content
        assert "risk-metrics" in html_content
        assert "agent-status" in html_content
        
        # Test risk monitoring dashboard
        risk_result = await dashboard.create_analysis_dashboard(symbols, "risk_monitoring")
        assert risk_result["dashboard_type"] == "risk_monitoring"
        
        # Test development dashboard
        dev_result = await dashboard.create_analysis_dashboard(symbols, "development")
        assert dev_result["dashboard_type"] == "development"
    
    @pytest.mark.asyncio
    async def test_financial_autocomplete_patterns(self, ide_integration):
        """Test financial autocomplete pattern matching"""
        await ide_integration._setup_financial_autocomplete()
        
        # Test calculation patterns
        calc_patterns = ide_integration.autocomplete_data['calculations']['risk_metrics']
        assert len(calc_patterns) > 0
        
        # Find Sharpe ratio pattern
        sharpe_pattern = next((p for p in calc_patterns if 'sharpe' in p['pattern']), None)
        assert sharpe_pattern is not None
        assert 'risk_free_rate' in sharpe_pattern['completion']
        
        # Test technical indicator patterns
        tech_patterns = ide_integration.autocomplete_data['calculations']['technical_indicators']
        assert len(tech_patterns) > 0
        
        # Find RSI pattern
        rsi_pattern = next((p for p in tech_patterns if 'rsi' in p['pattern']), None)
        assert rsi_pattern is not None
        assert 'period=14' in rsi_pattern['completion']
    
    @pytest.mark.asyncio
    async def test_mcp_message_flow(self, mcp_client):
        """Test MCP message flow between agents"""
        # Mock message sending
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "status": "delivered",
            "message_id": "msg_123",
            "source_agent": "TestSource",
            "target_agent": "TestTarget"
        })
        
        mcp_client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await mcp_client.send_agent_message(
            source_agent="TestSource",
            target_agent="TestTarget",
            message_type="TEST_MESSAGE",
            data={"test": "data"},
            priority="medium"
        )
        
        assert result["status"] == "delivered"
        assert result["source_agent"] == "TestSource"
        assert result["target_agent"] == "TestTarget"
        
        # Verify message was stored in client history
        assert len(mcp_client.message_history) > 0
        last_message = mcp_client.message_history[-1]
        assert last_message["source_agent"] == "TestSource"
        assert last_message["target_agent"] == "TestTarget"
    
    @pytest.mark.asyncio
    async def test_server_metrics_collection(self, mcp_client):
        """Test MCP server metrics collection"""
        # Mock server metrics response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "server_info": {
                "server_name": "test_server",
                "uptime_hours": 1.5
            },
            "processing_metrics": {
                "messages_processed": 150,
                "workflows_completed": 12,
                "errors_encountered": 2
            },
            "agent_metrics": {
                "total_registered": 6,
                "active_agents": 5
            }
        })
        
        mcp_client.session.call_tool = AsyncMock(return_value=mock_response)
        
        metrics = await mcp_client.get_server_metrics()
        
        assert "server_info" in metrics
        assert "processing_metrics" in metrics
        assert "agent_metrics" in metrics
        assert metrics["processing_metrics"]["messages_processed"] == 150
        assert metrics["agent_metrics"]["total_registered"] == 6
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_handling(self, mcp_client):
        """Test handling of concurrent workflows"""
        # Mock multiple workflow responses
        workflow_responses = []
        for i in range(3):
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = json.dumps({
                "workflow_id": f"workflow_{i}",
                "status": "initiated",
                "symbols": [f"TEST{i}"]
            })
            workflow_responses.append(mock_response)
        
        mcp_client.session.call_tool = AsyncMock(side_effect=workflow_responses)
        
        # Start multiple workflows concurrently
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                mcp_client.analyze_symbols([f"TEST{i}"], "quick", "normal")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Verify all workflows were created
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result["workflow_id"] == f"workflow_{i}"
            assert result["status"] == "initiated"
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, ide_integration):
        """Test system performance under load"""
        start_time = datetime.now()
        
        # Simulate multiple concurrent requests
        tasks = []
        for i in range(10):
            # Mock responses for concurrent requests
            mock_response = Mock()
            mock_response.content = [Mock()]
            mock_response.content[0].text = json.dumps({
                "completions": [{"label": f"completion_{i}", "code": f"code_{i}"}],
                "context_aware": True
            })
            
            ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
            
            task = asyncio.create_task(
                ide_integration.get_code_completion(f"test_context_{i}", i * 10)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Verify all requests completed
        assert len(results) == 10
        for result in results:
            assert "completions" in result
        
        # Performance should be reasonable (under 5 seconds for 10 concurrent requests)
        assert processing_time < 5.0
        
        print(f"Processed 10 concurrent requests in {processing_time:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_data_validation_and_guardrails(self, ide_integration):
        """Test data validation and guardrails integration"""
        # Test invalid financial code
        invalid_code = "var_95 = calculate_var(returns)"  # Missing confidence parameter
        
        # Mock validation response with errors
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "valid": False,
            "errors": ["VaR calculation requires confidence level"],
            "warnings": [],
            "suggestions": ["Add confidence parameter, e.g., confidence=0.95"]
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await ide_integration.validate_financial_code(invalid_code, "risk_calculation")
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "confidence level" in result["errors"][0]
        assert len(result["suggestions"]) > 0
    
    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self, ide_integration, mcp_client):
        """Test proper cleanup and resource management"""
        # Test IDE integration cleanup
        await ide_integration.setup_development_environment()
        
        # Add some test data
        ide_integration.live_sessions["test"] = {"test": "data"}
        ide_integration.development_tools["test_tool"] = {"info": "test"}
        
        # Perform cleanup
        await ide_integration.cleanup()
        
        # Verify cleanup
        assert len(ide_integration.live_sessions) == 0
        assert len(ide_integration.development_tools) == 0
        
        # Test client cleanup
        mcp_client.pending_requests["test"] = {"data": "test"}
        mcp_client.message_history = [{"msg": "test"} for _ in range(200)]
        
        await mcp_client.cleanup()
        
        # Verify client cleanup
        assert len(mcp_client.pending_requests) == 0
        assert len(mcp_client.message_history) <= 100  # Should keep only last 100


class TestMCPIntegrationEdgeCases:
    """Test edge cases and error conditions"""
    
    @pytest.mark.asyncio
    async def test_malformed_responses(self):
        """Test handling of malformed MCP responses"""
        ide_integration = IDEMCPIntegration()
        ide_integration.client = AsyncMock()
        
        # Mock malformed JSON response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "invalid json {"
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        result = await ide_integration.get_code_completion("test", 0)
        assert "error" in result or result.get("completions") == []
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self):
        """Test network timeout handling"""
        mcp_client = FinancialMCPClient()
        mcp_client.connected = True
        mcp_client.session = AsyncMock()
        
        # Mock timeout exception
        mcp_client.session.call_tool.side_effect = asyncio.TimeoutError("Request timeout")
        
        result = await mcp_client.analyze_symbols(["TEST"], "quick", "normal")
        assert "error" in result
        assert "timeout" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_large_data_handling(self):
        """Test handling of large data sets"""
        live_data = LiveFinancialDataMCP()
        
        # Test with large symbol list
        large_symbol_list = [f"TEST{i:04d}" for i in range(100)]
        
        try:
            result = await live_data.stream_market_data(large_symbol_list, 10000)
            
            # Should handle large lists gracefully
            assert "stream_id" in result or "error" in result
            
        finally:
            await live_data.cleanup()


class TestMCPPerformanceBenchmarks:
    """Performance benchmark tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_code_completion_performance(self):
        """Benchmark code completion performance"""
        ide_integration = IDEMCPIntegration()
        ide_integration.client = AsyncMock()
        
        # Mock fast response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = json.dumps({
            "completions": [{"label": "test", "code": "test_code"}]
        })
        
        ide_integration.client.session.call_tool = AsyncMock(return_value=mock_response)
        
        # Benchmark multiple requests
        start_time = datetime.now()
        
        tasks = [
            ide_integration.get_code_completion(f"test_{i}", i)
            for i in range(50)
        ]
        
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds()
        avg_time_per_request = processing_time / 50
        
        print(f"Code completion benchmark: {avg_time_per_request:.3f}s per request")
        
        # Should complete 50 requests in under 2 seconds
        assert processing_time < 2.0
        assert len(results) == 50
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_dashboard_generation_performance(self):
        """Benchmark dashboard generation performance"""
        dashboard = InteractiveDashboard()
        
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        start_time = datetime.now()
        result = await dashboard.create_analysis_dashboard(symbols, "comprehensive")
        end_time = datetime.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        print(f"Dashboard generation time: {generation_time:.3f}s")
        
        # Should generate dashboard in under 1 second
        assert generation_time < 1.0
        assert "dashboard_html" in result
        assert len(result["dashboard_html"]) > 1000  # Substantial HTML content


# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Main test runner
if __name__ == "__main__":
    # Run specific test categories
    print("🧪 Running Financial MCP Integration Tests...")
    
    # Basic functionality tests
    print("\n📋 Basic Functionality Tests:")
    pytest.main([__file__ + "::TestMCPIntegration", "-v"])
    
    # Edge case tests
    print("\n⚠️ Edge Case Tests:")
    pytest.main([__file__ + "::TestMCPIntegrationEdgeCases", "-v"])
    
    # Performance benchmarks
    print("\n⚡ Performance Benchmarks:")
    pytest.main([__file__ + "::TestMCPPerformanceBenchmarks", "-v", "-m", "slow"])
    
    print("\n✅ MCP Integration Tests Completed!")
    print("💡 Run from project root: python -m pytest tests/test_mcp_integration.py -v")
