# mcp/ide_integration.py
"""Integration layer for IDE MCP functionality - Simplified Version"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our dev server instead of external MCP client
from mcp.dev_server import FinancialDevMCPServer

logger = logging.getLogger(__name__)


class IDEMCPIntegration:
    """Integration layer for IDE MCP functionality"""
    
    def __init__(self, client_id: str = "ide_client"):
        self.client_id = client_id
        self.dev_server: Optional[FinancialDevMCPServer] = None
        self.development_tools = {}
        self.autocomplete_data = {}
        self.live_sessions = {}
        self.connected = False
        
    async def setup_development_environment(self):
        """Setup MCP development environment in IDE"""
        try:
            logger.info("Setting up IDE development environment...")
            
            # Initialize our dev server
            self.dev_server = FinancialDevMCPServer()
            self.connected = True
            
            # Register development tools
            await self._register_development_tools()
            
            # Setup auto-completion data
            await self._setup_financial_autocomplete()
            
            # Initialize live data sessions
            await self._setup_live_data_sessions()
            
            logger.info("IDE development environment setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup development environment: {str(e)}")
            raise
    
    async def _register_development_tools(self):
        """Register financial development tools"""
        tools = [
            {
                "name": "financial_data_analyzer",
                "description": "Analyze financial data patterns and trends",
                "parameters": ["symbol", "analysis_type", "timeframe", "indicators"],
                "capabilities": ["technical_analysis", "pattern_recognition", "trend_analysis"]
            },
            {
                "name": "risk_calculator", 
                "description": "Calculate comprehensive risk metrics",
                "parameters": ["data", "confidence_level", "time_horizon", "method"],
                "capabilities": ["var_calculation", "sharpe_ratio", "drawdown_analysis", "beta_calculation"]
            },
            {
                "name": "portfolio_optimizer",
                "description": "Optimize portfolio allocation and risk",
                "parameters": ["symbols", "constraints", "objective", "risk_tolerance"],
                "capabilities": ["mean_variance_optimization", "black_litterman", "risk_parity"]
            },
            {
                "name": "market_data_validator",
                "description": "Validate and clean market data",
                "parameters": ["data", "validation_rules", "cleaning_method"],
                "capabilities": ["outlier_detection", "missing_data_handling", "data_quality_scoring"]
            },
            {
                "name": "performance_analyzer",
                "description": "Analyze trading strategy performance",
                "parameters": ["returns", "benchmark", "frequency", "metrics"],
                "capabilities": ["attribution_analysis", "performance_metrics", "drawdown_analysis"]
            }
        ]
        
        for tool in tools:
            try:
                self.development_tools[tool['name']] = {
                    "tool_info": tool,
                    "status": "active",
                    "last_used": None
                }
                
                logger.info(f"Registered development tool: {tool['name']}")
                
            except Exception as e:
                logger.error(f"Failed to register tool {tool['name']}: {str(e)}")
    
    async def _setup_financial_autocomplete(self):
        """Setup financial auto-completion data"""
        try:
            # Financial calculation patterns
            self.autocomplete_data['calculations'] = {
                "risk_metrics": [
                    {
                        "pattern": "calculate_var",
                        "completion": "calculate_var(returns, confidence=0.95, method='historical')",
                        "description": "Calculate Value at Risk",
                        "example": "var_95 = calculate_var(portfolio_returns, confidence=0.95)"
                    },
                    {
                        "pattern": "calculate_sharpe",
                        "completion": "calculate_sharpe_ratio(returns, risk_free_rate=0.02)",
                        "description": "Calculate Sharpe ratio for risk-adjusted returns",
                        "example": "sharpe = calculate_sharpe_ratio(strategy_returns, risk_free_rate=0.025)"
                    },
                    {
                        "pattern": "calculate_drawdown",
                        "completion": "calculate_max_drawdown(cumulative_returns)",
                        "description": "Calculate maximum drawdown",
                        "example": "max_dd = calculate_max_drawdown(cum_returns)"
                    },
                    {
                        "pattern": "calculate_beta",
                        "completion": "calculate_beta(stock_returns, market_returns)",
                        "description": "Calculate beta coefficient",
                        "example": "beta = calculate_beta(aapl_returns, spy_returns)"
                    }
                ],
                "technical_indicators": [
                    {
                        "pattern": "rsi",
                        "completion": "calculate_rsi(prices, period=14)",
                        "description": "Relative Strength Index",
                        "example": "rsi = calculate_rsi(close_prices, period=14)"
                    },
                    {
                        "pattern": "macd",
                        "completion": "calculate_macd(prices, fast=12, slow=26, signal=9)",
                        "description": "Moving Average Convergence Divergence",
                        "example": "macd, signal = calculate_macd(close_prices)"
                    },
                    {
                        "pattern": "bollinger",
                        "completion": "calculate_bollinger_bands(prices, period=20, std_dev=2)",
                        "description": "Bollinger Bands",
                        "example": "upper, middle, lower = calculate_bollinger_bands(prices)"
                    }
                ],
                "agent_patterns": [
                    {
                        "pattern": "send_mcp_message",
                        "completion": "await self.send_mcp_message(target_agent, message_type, data, priority)",
                        "description": "Send MCP message to another agent",
                        "example": "await self.send_mcp_message('RiskAgent', MessageType.ANALYZE, data, Priority.HIGH)"
                    },
                    {
                        "pattern": "log_activity",
                        "completion": "await self.log_activity(activity, level='info', data=None)",
                        "description": "Log agent activity with structured data",
                        "example": "await self.log_activity('Analysis completed', 'info', {'symbol': 'AAPL'})"
                    },
                    {
                        "pattern": "validate_",
                        "completion": "validation_status, issues = self.guardrails.validate_{type}({data})",
                        "description": "Validate data using guardrails",
                        "example": "status, issues = self.guardrails.validate_symbol(symbol)"
                    }
                ]
            }
            
            # Market data patterns
            self.autocomplete_data['market_data'] = {
                "data_collection": [
                    {
                        "pattern": "collect_data",
                        "completion": "financial_data = await self.collect_stock_data(symbol, period='1y')",
                        "description": "Collect financial data for analysis"
                    },
                    {
                        "pattern": "get_live_data",
                        "completion": "live_data = await self.get_live_market_data(symbols)",
                        "description": "Get real-time market data"
                    }
                ],
                "analysis": [
                    {
                        "pattern": "analyze_market",
                        "completion": "analysis = await self.analyze_market_data(financial_data)",
                        "description": "Perform comprehensive market analysis"
                    },
                    {
                        "pattern": "assess_risk",
                        "completion": "risk_assessment = await self.assess_comprehensive_risk(market_analysis)",
                        "description": "Assess investment risk"
                    }
                ]
            }
            
            logger.info("Financial autocomplete data setup complete")
            
        except Exception as e:
            logger.error(f"Failed to setup autocomplete data: {str(e)}")
    
    async def _setup_live_data_sessions(self):
        """Setup live data streaming sessions"""
        try:
            # Create default live data session
            session_config = {
                "session_id": "ide_live_session",
                "symbols": ["AAPL", "MSFT", "GOOGL", "SPY", "QQQ"],
                "update_frequency": 5000,  # 5 seconds
                "data_types": ["price", "volume", "technical_indicators"],
                "created_at": datetime.now().isoformat()
            }
            
            self.live_sessions["default"] = session_config
            
            logger.info("Live data sessions initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup live data sessions: {str(e)}")
    
    async def get_code_completion(self, context: str, cursor_position: int, 
                                file_type: str = "python") -> Dict[str, Any]:
        """Get intelligent code completion suggestions"""
        try:
            if not self.dev_server:
                raise ConnectionError("Development server not initialized")
            
            # Use our dev server's completion method
            result = await self.dev_server._financial_code_completion(
                context=context,
                cursor_position=cursor_position,
                file_type=file_type
            )
            
            return json.loads(result) if isinstance(result, str) else result
            
        except Exception as e:
            logger.error(f"Error getting code completion: {str(e)}")
            return {"completions": [], "error": str(e)}
    
    async def validate_financial_code(self, code: str, analysis_type: str) -> Dict[str, Any]:
        """Validate financial code in real-time"""
        try:
            if not self.dev_server:
                raise ConnectionError("Development server not initialized")
            
            result = await self.dev_server._validate_financial_logic(
                code=code,
                analysis_type=analysis_type
            )
            
            return json.loads(result) if isinstance(result, str) else result
            
        except Exception as e:
            logger.error(f"Error validating code: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    async def start_live_data_stream(self, symbols: List[str], 
                                   update_frequency: int = 5000) -> Dict[str, Any]:
        """Start live market data stream for development"""
        try:
            if not self.dev_server:
                raise ConnectionError("Development server not initialized")
            
            result = await self.dev_server._live_market_data_integration(
                symbols=symbols,
                update_frequency=update_frequency
            )
            
            stream_config = json.loads(result) if isinstance(result, str) else result
            
            # Store session info
            session_id = stream_config.get("stream_id")
            if session_id:
                self.live_sessions[session_id] = {
                    "symbols": symbols,
                    "update_frequency": update_frequency,
                    "config": stream_config,
                    "started_at": datetime.now().isoformat()
                }
            
            return stream_config
            
        except Exception as e:
            logger.error(f"Error starting live data stream: {str(e)}")
            return {"error": str(e)}
    
    async def create_development_dashboard(self, agent_types: List[str] = None, 
                                         metrics: List[str] = None) -> Dict[str, Any]:
        """Create development monitoring dashboard"""
        try:
            if not self.dev_server:
                raise ConnectionError("Development server not initialized")
            
            if agent_types is None:
                agent_types = [
                    "DataCollectionAgent",
                    "BusinessIntelligenceAgent",
                    "RiskAssessmentAgent", 
                    "RecommendationAgent",
                    "ReportGenerationAgent",
                    "TriageAgent"
                ]
            
            if metrics is None:
                metrics = [
                    "processing_time",
                    "success_rate",
                    "error_count",
                    "message_volume",
                    "memory_usage"
                ]
            
            result = await self.dev_server._create_development_dashboard(
                agent_types=agent_types,
                metrics=metrics
            )
            
            return json.loads(result) if isinstance(result, str) else result
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {"error": str(e)}
    
    async def analyze_code_performance(self, code: str, 
                                     execution_context: str = "development") -> Dict[str, Any]:
        """Analyze code performance and suggest optimizations"""
        try:
            if not self.dev_server:
                raise ConnectionError("Development server not initialized")
            
            result = await self.dev_server._analyze_code_performance(
                code=code,
                execution_context=execution_context
            )
            
            return json.loads(result) if isinstance(result, str) else result
            
        except Exception as e:
            logger.error(f"Error analyzing code performance: {str(e)}")
            return {"error": str(e)}
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all registered development tools"""
        try:
            status_info = {
                "client_status": "connected" if self.connected else "disconnected",
                "registered_tools": len(self.development_tools),
                "active_sessions": len(self.live_sessions),
                "autocomplete_patterns": sum(len(patterns) for patterns in self.autocomplete_data.values()),
                "tools": {}
            }
            
            for tool_name, tool_data in self.development_tools.items():
                status_info["tools"][tool_name] = {
                    "status": tool_data.get("status", "unknown"),
                    "capabilities": tool_data["tool_info"]["capabilities"],
                    "last_used": tool_data["last_used"]
                }
            
            return status_info
            
        except Exception as e:
            logger.error(f"Error getting agent status: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources and disconnect"""
        try:
            # Stop live data sessions
            for session_id in list(self.live_sessions.keys()):
                del self.live_sessions[session_id]
            
            # Clear development tools
            self.development_tools.clear()
            
            # Reset connection status
            self.connected = False
            self.dev_server = None
            
            logger.info("IDE integration cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Global integration instance
ide_integration = IDEMCPIntegration()


async def get_ide_integration() -> IDEMCPIntegration:
    """Get or create IDE integration instance"""
    if not ide_integration.connected:
        await ide_integration.setup_development_environment()
    return ide_integration


# Convenience functions for IDE usage
async def get_financial_completions(context: str, cursor_position: int) -> List[Dict[str, str]]:
    """Get financial code completions for IDE"""
    integration = await get_ide_integration()
    result = await integration.get_code_completion(context, cursor_position)
    return result.get("completions", [])


async def validate_financial_calculation(code: str, calc_type: str = "general") -> Dict[str, Any]:
    """Validate financial calculation code"""
    integration = await get_ide_integration()
    return await integration.validate_financial_code(code, calc_type)


async def start_development_data_feed(symbols: List[str]) -> Dict[str, Any]:
    """Start live data feed for development"""
    integration = await get_ide_integration()
    return await integration.start_live_data_stream(symbols)


if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        print("🔧 Testing IDE MCP Integration")
        print("=" * 50)
        
        integration = IDEMCPIntegration()
        await integration.setup_development_environment()
        
        # Test 1: Code completion
        print("\n1. Testing Code Completion...")
        completions = await integration.get_code_completion("calculate_", 10)
        print(f"✅ Generated {len(completions.get('completions', []))} completions")
        
        # Show some completions
        for i, comp in enumerate(completions.get('completions', [])[:3], 1):
            print(f"   {i}. {comp.get('label', 'N/A')}: {comp.get('detail', 'N/A')}")
        
        # Test 2: Code validation
        print("\n2. Testing Code Validation...")
        test_code = "sharpe_ratio = calculate_sharpe_ratio(returns, risk_free_rate=0.02)"
        validation = await integration.validate_financial_code(test_code, "risk_analysis")
        print(f"✅ Validation result: {validation.get('valid', False)}")
        
        if validation.get('warnings'):
            print("   Warnings:")
            for warning in validation['warnings']:
                print(f"   • {warning}")
        
        # Test 3: Live data stream
        print("\n3. Testing Live Data Stream...")
        stream_config = await integration.start_live_data_stream(["AAPL", "MSFT"])
        print(f"✅ Stream configured: {stream_config.get('stream_id', 'N/A')}")
        
        # Test 4: Development dashboard
        print("\n4. Testing Development Dashboard...")
        dashboard = await integration.create_development_dashboard()
        print(f"✅ Dashboard created: {dashboard.get('dashboard_url', 'N/A')}")
        
        # Test 5: Performance analysis
        print("\n5. Testing Performance Analysis...")
        test_perf_code = """
def calculate_returns(prices):
    returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] - prices[i-1]) / prices[i-1]
        returns.append(ret)
    return returns
"""
        perf_analysis = await integration.analyze_code_performance(test_perf_code)
        print(f"✅ Performance score: {perf_analysis.get('performance_score', 'N/A')}")
        
        # Test 6: Agent status
        print("\n6. Getting Agent Status...")
        status = await integration.get_agent_status()
        print(f"✅ Connection status: {status.get('client_status', 'unknown')}")
        print(f"✅ Registered tools: {status.get('registered_tools', 0)}")
        print(f"✅ Active sessions: {status.get('active_sessions', 0)}")
        
        await integration.cleanup()
        
        print("\n" + "=" * 50)
        print("🎉 IDE Integration Test Complete!")
        print("=" * 50)
        print("✅ Your Cursor IDE now has enhanced financial development features!")
    
    asyncio.run(test_integration())
