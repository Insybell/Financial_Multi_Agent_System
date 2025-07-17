# mcp/dev_server.py
"""Enhanced MCP Server for development experience with IDE integration"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class FinancialDevMCPServer:  # Remove inheritance temporarily
    """Enhanced MCP server with IDE specific development tools"""
    
    def __init__(self, server_name: str = "financial-dev-server"):
        self.server_name = server_name
        self.registered_agents = {}
        self.agent_capabilities = {}
        self.message_history = []
        self.active_workflows = {}
        self.development_tools = {}
        
        # Performance tracking
        self.server_metrics = {
            "messages_processed": 0,
            "workflows_completed": 0,
            "errors_encountered": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._setup_development_tools()
        self._setup_code_intelligence()
        
        logger.info("Financial Development MCP Server initialized with IDE enhancements")
    
    def _setup_development_tools(self):
        """Setup IDE specific development tools"""
        logger.info("Setting up development tools...")
        
        # Store tool definitions instead of decorating
        self.tools = {
            "generate_financial_agent_code": self._generate_financial_agent_code,
            "validate_financial_logic": self._validate_financial_logic,
            "financial_code_completion": self._financial_code_completion,
            "live_market_data_integration": self._live_market_data_integration,
            "create_development_dashboard": self._create_development_dashboard
        }
        
        logger.info(f"Registered {len(self.tools)} development tools")
    
    def _setup_code_intelligence(self):
        """Setup advanced code intelligence features"""
        logger.info("Setting up code intelligence features...")
        
        # Add code intelligence tools
        self.intelligence_tools = {
            "analyze_code_performance": self._analyze_code_performance
        }
        
        logger.info("Code intelligence features ready")
    
    async def start_server(self):
        """Start the MCP server"""
        try:
            logger.info(f"Starting Financial MCP Server: {self.server_name}")
            logger.info("✅ Enhanced development features available")
            logger.info("✅ IDE integration tools ready")
            logger.info("✅ Code intelligence features active")
            logger.info("✅ Development dashboard available")
            
            # Display available tools
            logger.info(f"Available tools: {list(self.tools.keys())}")
            
            print("\n" + "="*60)
            print("🚀 FINANCIAL MCP DEVELOPMENT SERVER READY")
            print("="*60)
            print(f"Server Name: {self.server_name}")
            print(f"Tools Available: {len(self.tools)}")
            print(f"Intelligence Features: {len(self.intelligence_tools)}")
            print("="*60)
            print("Press Ctrl+C to stop the server")
            print("="*60 + "\n")
            
            # Keep server running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down Financial MCP Development Server")
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            raise
    
    # Tool implementations
    async def _generate_financial_agent_code(self, agent_type: str, functionality: str, requirements: List[str]) -> str:
        """Generate specialized financial agent code for IDE"""
        try:
            code_templates = {
                "data_collection": self._generate_data_collection_code,
                "risk_assessment": self._generate_risk_assessment_code,
                "business_intelligence": self._generate_bi_code,
                "recommendation": self._generate_recommendation_code,
                "report_generation": self._generate_report_code,
                "triage": self._generate_triage_code
            }
            
            if agent_type not in code_templates:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            generated_code = await code_templates[agent_type](functionality, requirements)
            
            return json.dumps({
                "status": "success",
                "agent_type": agent_type,
                "functionality": functionality,
                "code": generated_code,
                "imports": self._get_required_imports(agent_type),
                "tests": self._generate_test_code(agent_type, functionality),
                "documentation": self._generate_documentation(agent_type, functionality)
            })
            
        except Exception as e:
            logger.error(f"Error generating agent code: {str(e)}")
            return json.dumps({"error": str(e), "status": "failed"})
    
    async def _validate_financial_logic(self, code: str, analysis_type: str) -> str:
        """Real-time validation of financial calculations and logic"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "suggestions": [],
                "financial_accuracy": True
            }
            
            # Validate financial calculation patterns
            validation_results = await self._validate_financial_patterns(code, analysis_type)
            
            # Check for common financial programming errors
            validation_results.update(await self._check_financial_errors(code))
            
            # Suggest optimizations
            optimizations = await self._suggest_financial_optimizations(code, analysis_type)
            validation_results["optimizations"] = optimizations
            
            return json.dumps(validation_results, indent=2)
            
        except Exception as e:
            logger.error(f"Error validating financial logic: {str(e)}")
            return json.dumps({"error": str(e), "valid": False})
    
    async def _financial_code_completion(self, context: str, cursor_position: int, file_type: str = "python") -> str:
        """Provide intelligent code completion for financial analysis"""
        try:
            completions = []
            
            # Analyze context for financial patterns
            if "calculate_" in context:
                completions.extend([
                    {
                        "label": "calculate_sharpe_ratio",
                        "detail": "Calculate Sharpe ratio for risk-adjusted returns",
                        "code": "calculate_sharpe_ratio(returns, risk_free_rate=0.02)",
                        "documentation": "Sharpe ratio = (Expected return - Risk-free rate) / Standard deviation"
                    },
                    {
                        "label": "calculate_var",
                        "detail": "Calculate Value at Risk",
                        "code": "calculate_var(returns, confidence=0.95)",
                        "documentation": "VaR estimates maximum potential loss at given confidence level"
                    },
                    {
                        "label": "calculate_max_drawdown", 
                        "detail": "Calculate maximum drawdown",
                        "code": "calculate_max_drawdown(cumulative_returns)",
                        "documentation": "Maximum peak-to-trough decline in portfolio value"
                    }
                ])
            
            if "risk_" in context:
                completions.extend([
                    {
                        "label": "risk_assessment",
                        "detail": "Comprehensive risk assessment",
                        "code": "risk_assessment = await agent.assess_comprehensive_risk(analysis)",
                        "documentation": "Performs multi-factor risk analysis"
                    },
                    {
                        "label": "risk_metrics",
                        "detail": "Risk metrics calculation",
                        "code": "risk_metrics = RiskMetrics(var_95=var, sharpe_ratio=sharpe)",
                        "documentation": "Standard risk metrics container"
                    }
                ])
            
            if "market_" in context:
                completions.extend([
                    {
                        "label": "market_analysis",
                        "detail": "Market analysis workflow",
                        "code": "market_analysis = await bi_agent.analyze_market_data(financial_data)",
                        "documentation": "Complete technical and fundamental analysis"
                    },
                    {
                        "label": "market_trends",
                        "detail": "Trend identification",
                        "code": "trend = determine_trend_strength(price, indicators)",
                        "documentation": "Identify market trend direction and strength"
                    }
                ])
            
            # Agent-specific completions
            if "agent" in context.lower():
                completions.extend(self._get_agent_completions(context))
            
            return json.dumps({
                "completions": completions,
                "context_aware": True,
                "financial_specific": True,
                "cursor_position": cursor_position
            })
            
        except Exception as e:
            logger.error(f"Error in code completion: {str(e)}")
            return json.dumps({"error": str(e), "completions": []})
    
    async def _live_market_data_integration(self, symbols: List[str], update_frequency: int = 5000) -> str:
        """Integrate live market data for development testing"""
        try:
            # Setup live data stream for development
            stream_config = {
                "stream_id": f"dev_stream_{datetime.now().strftime('%H%M%S')}",
                "symbols": symbols,
                "update_frequency": update_frequency,
                "websocket_url": "ws://localhost:8001/market-stream",
                "rest_endpoint": "http://localhost:8000/market-data",
                "sample_data": self._generate_sample_market_data(symbols)
            }
            
            return json.dumps(stream_config, indent=2)
            
        except Exception as e:
            logger.error(f"Error setting up live data: {str(e)}")
            return json.dumps({"error": str(e)})
    
    async def _create_development_dashboard(self, agent_types: List[str], metrics: List[str] = None) -> str:
        """Create interactive development dashboard for IDE"""
        try:
            dashboard_html = self._generate_dashboard_html(agent_types, metrics)
            
            return json.dumps({
                "dashboard_html": dashboard_html,
                "dashboard_url": "http://localhost:8000/dev-dashboard",
                "websocket_endpoint": "ws://localhost:8000/dev-ws",
                "update_interval": 1000,
                "features": [
                    "Real-time agent monitoring",
                    "Live financial data feeds", 
                    "Performance metrics",
                    "Error tracking",
                    "Workflow visualization"
                ]
            })
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return json.dumps({"error": str(e)})
    
    async def _analyze_code_performance(self, code: str, execution_context: str = "development") -> str:
        """Analyze code performance for financial calculations"""
        try:
            analysis = {
                "performance_score": 0.85,
                "bottlenecks": [],
                "optimizations": [],
                "memory_usage": "moderate",
                "execution_time_estimate": "< 100ms",
                "scalability_rating": "good"
            }
            
            # Analyze for common performance issues
            if "for" in code and "pandas" in code:
                analysis["optimizations"].append({
                    "type": "vectorization",
                    "description": "Consider vectorizing pandas operations",
                    "impact": "high",
                    "suggestion": "Use .apply() or built-in pandas methods instead of explicit loops"
                })
            
            if "np.random" in code and "seed" not in code:
                analysis["optimizations"].append({
                    "type": "reproducibility",
                    "description": "Add random seed for reproducible results",
                    "impact": "medium",
                    "suggestion": "Add np.random.seed(42) for consistent testing"
                })
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing code performance: {str(e)}")
            return json.dumps({"error": str(e)})
    
    # Helper methods
    async def _generate_data_collection_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate data collection agent code"""
        return f'''
async def collect_financial_data(self, symbols: List[str]) -> List[FinancialData]:
    """
    Collect financial data for given symbols
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    collected_data = []
    
    for symbol in symbols:
        try:
            # Validate symbol
            validation_status, issues = self.guardrails.validate_symbol(symbol)
            if validation_status == ValidationStatus.FAILED:
                logger.error(f"Symbol validation failed for {{symbol}}: {{issues}}")
                continue
            
            # Fetch data with caching
            data = await self._fetch_with_cache(symbol)
            
            # Quality check
            quality_score = self.guardrails.check_data_quality(data.data)
            data.data_quality = quality_score
            
            collected_data.append(data)
            
        except Exception as e:
            logger.error(f"Error collecting data for {{symbol}}: {{str(e)}}")
            
    return collected_data
'''
    
    async def _generate_risk_assessment_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate risk assessment agent code"""
        return f'''
async def assess_risk(self, financial_data: FinancialData) -> RiskAssessment:
    """
    Assess risk for financial data
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    try:
        # Calculate risk metrics
        returns = financial_data.calculate_returns()
        volatility = np.std(returns)
        var_95 = np.percentile(returns, 5)
        
        risk_assessment = RiskAssessment(
            volatility=volatility,
            var_95=var_95,
            risk_level=self._determine_risk_level(volatility),
            recommendations=self._generate_risk_recommendations(volatility, var_95)
        )
        
        return risk_assessment
        
    except Exception as e:
        logger.error(f"Error in risk assessment: {{str(e)}}")
        raise
'''
    
    async def _generate_bi_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate business intelligence agent code"""
        return f'''
async def analyze_business_intelligence(self, data: FinancialData) -> BIAnalysis:
    """
    Perform business intelligence analysis
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    try:
        analysis = BIAnalysis()
        
        # Technical analysis
        analysis.technical_indicators = self._calculate_technical_indicators(data)
        
        # Market trends
        analysis.trend_analysis = self._analyze_trends(data)
        
        # Performance metrics
        analysis.performance_metrics = self._calculate_performance_metrics(data)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in BI analysis: {{str(e)}}")
        raise
'''
    
    async def _generate_recommendation_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate recommendation agent code"""
        return f'''
async def generate_recommendations(self, analysis: Any) -> List[Recommendation]:
    """
    Generate financial recommendations
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    recommendations = []
    
    try:
        # Analyze risk-return profile
        if analysis.risk_level == "HIGH":
            recommendations.append(Recommendation(
                type="RISK_REDUCTION",
                description="Consider reducing position size due to high volatility",
                priority="HIGH",
                confidence=0.85
            ))
        
        # Portfolio optimization recommendations
        if analysis.sharpe_ratio < 1.0:
            recommendations.append(Recommendation(
                type="PORTFOLIO_OPTIMIZATION",
                description="Consider diversifying to improve risk-adjusted returns",
                priority="MEDIUM",
                confidence=0.70
            ))
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {{str(e)}}")
        raise
'''
    
    async def _generate_report_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate report generation agent code"""
        return f'''
async def generate_report(self, analysis_data: Dict[str, Any]) -> FinancialReport:
    """
    Generate comprehensive financial report
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    try:
        report = FinancialReport(
            timestamp=datetime.now(),
            analysis_period=analysis_data.get("period", "1Y"),
            executive_summary=self._generate_executive_summary(analysis_data),
            detailed_analysis=self._generate_detailed_analysis(analysis_data),
            recommendations=analysis_data.get("recommendations", []),
            risk_assessment=analysis_data.get("risk_assessment"),
            performance_metrics=analysis_data.get("performance_metrics")
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating report: {{str(e)}}")
        raise
'''
    
    async def _generate_triage_code(self, functionality: str, requirements: List[str]) -> str:
        """Generate triage agent code"""
        return f'''
async def triage_request(self, request: AgentRequest) -> TriageResult:
    """
    Triage incoming agent requests
    Functionality: {functionality}
    Requirements: {", ".join(requirements)}
    """
    try:
        # Determine priority
        priority = self._assess_priority(request)
        
        # Route to appropriate agent
        target_agent = self._determine_target_agent(request)
        
        # Validate request
        validation_result = await self._validate_request(request)
        
        triage_result = TriageResult(
            priority=priority,
            target_agent=target_agent,
            validation_status=validation_result.status,
            estimated_processing_time=self._estimate_processing_time(request),
            required_resources=self._identify_required_resources(request)
        )
        
        return triage_result
        
    except Exception as e:
        logger.error(f"Error in triage: {{str(e)}}")
        raise
'''
    
    async def _validate_financial_patterns(self, code: str, analysis_type: str) -> Dict[str, Any]:
        """Validate financial calculation patterns"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Check for common financial calculation errors
        if "sharpe_ratio" in code and "risk_free_rate" not in code:
            results["warnings"].append("Consider specifying risk_free_rate parameter for Sharpe ratio")
        
        if "var" in code.lower() and "confidence" not in code:
            results["errors"].append("VaR calculation requires confidence level parameter")
            results["valid"] = False
        
        if "return" in code and "risk" not in code:
            results["suggestions"].append("Consider risk-adjusted metrics alongside returns")
        
        return results
    
    async def _check_financial_errors(self, code: str) -> Dict[str, List[str]]:
        """Check for common financial programming errors"""
        errors = []
        warnings = []
        
        # Check for division by zero in financial ratios
        if "/=" in code or "/ " in code:
            warnings.append("Ensure denominator is not zero in financial ratio calculations")
        
        # Check for missing error handling
        if "try:" not in code and ("fetch" in code or "api" in code):
            warnings.append("Add error handling for external data sources")
        
        # Check for hardcoded financial parameters
        if any(num in code for num in ["0.02", "0.05", "252"]):
            warnings.append("Consider making financial parameters configurable")
        
        return {"errors": errors, "warnings": warnings}
    
    async def _suggest_financial_optimizations(self, code: str, analysis_type: str) -> List[Dict[str, str]]:
        """Suggest financial code optimizations"""
        optimizations = []
        
        if "pandas" in code and "for" in code:
            optimizations.append({
                "type": "performance",
                "description": "Vectorize pandas operations for better performance",
                "suggestion": "Use .apply() or built-in pandas methods instead of loops"
            })
        
        if "numpy" in code and "random" in code:
            optimizations.append({
                "type": "reproducibility",
                "description": "Set random seed for reproducible results",
                "suggestion": "Add np.random.seed(42) at the beginning"
            })
        
        return optimizations
    
    def _get_required_imports(self, agent_type: str) -> List[str]:
        """Get required imports for agent type"""
        base_imports = [
            "import asyncio",
            "import logging",
            "import numpy as np",
            "import pandas as pd",
            "from datetime import datetime",
            "from typing import Dict, List, Optional, Any"
        ]
        
        type_specific_imports = {
            "data_collection": ["import yfinance as yf", "import requests"],
            "risk_assessment": ["from scipy import stats", "import scipy.optimize"],
            "business_intelligence": ["import plotly.graph_objects as go", "import seaborn as sns"],
            "recommendation": ["from sklearn.ensemble import RandomForestRegressor"],
            "report_generation": ["import jinja2", "import matplotlib.pyplot as plt"],
            "triage": ["import uuid", "from enum import Enum"]
        }
        
        return base_imports + type_specific_imports.get(agent_type, [])
    
    def _generate_test_code(self, agent_type: str, functionality: str) -> str:
        """Generate test code for agent"""
        return f'''
import pytest
import asyncio
from unittest.mock import Mock, patch

class Test{agent_type.title().replace("_", "")}Agent:
    """Test suite for {agent_type} agent"""
    
    @pytest.fixture
    def agent(self):
        return {agent_type.title().replace("_", "")}Agent()
    
    @pytest.mark.asyncio
    async def test_{functionality.lower().replace(" ", "_")}(self, agent):
        """Test {functionality}"""
        # Mock data
        test_data = self._create_test_data()
        
        # Execute functionality
        result = await agent.main_method(test_data)
        
        # Assertions
        assert result is not None
        assert result.status == "success"
        
    def _create_test_data(self):
        """Create test data for {agent_type}"""
        return {{"test": "data"}}
'''
    
    def _generate_documentation(self, agent_type: str, functionality: str) -> str:
        """Generate documentation for agent"""
        return f'''
# {agent_type.title().replace("_", " ")} Agent

## Overview
This agent handles {functionality} for the financial multi-agent system.

## Key Features
- Asynchronous processing
- Error handling and validation
- Performance optimization
- Comprehensive logging

## Usage
```python
agent = {agent_type.title().replace("_", "")}Agent()
result = await agent.main_method(data)
```

## Configuration
- Set appropriate log levels
- Configure data sources
- Set up error handling

## Testing
Run tests with: `pytest test_{agent_type}.py`
'''
    
    def _get_agent_completions(self, context: str) -> List[Dict[str, str]]:
        """Get agent-specific code completions"""
        return [
            {
                "label": "send_mcp_message",
                "detail": "Send MCP message to another agent",
                "code": "await self.send_mcp_message(target_agent, message_type, data, priority)",
                "documentation": "Inter-agent communication via MCP protocol"
            },
            {
                "label": "log_activity",
                "detail": "Log agent activity",
                "code": "await self.log_activity(activity, level, data)",
                "documentation": "Structured activity logging for monitoring"
            }
        ]
    
    def _generate_sample_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Generate sample market data for development"""
        import random
        
        sample_data = {}
        for symbol in symbols:
            sample_data[symbol] = {
                "price": round(random.uniform(50, 300), 2),
                "change": round(random.uniform(-5, 5), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "volume": random.randint(100000, 10000000),
                "timestamp": datetime.now().isoformat()
            }
        
        return sample_data
    
    def _generate_dashboard_html(self, agent_types: List[str], metrics: List[str]) -> str:
        """Generate dashboard HTML for development monitoring"""
        return f'''
<!DOCTYPE html>
<html>
<head>
    <title>Financial Multi-Agent Development Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric {{ font-size: 24px; font-weight: bold; color: #333; }}
        .status {{ padding: 5px 10px; border-radius: 4px; color: white; }}
        .status.active {{ background: #28a745; }}
        .status.idle {{ background: #6c757d; }}
        .status.error {{ background: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Financial Multi-Agent Development Dashboard</h1>
        
        <div class="grid">
            <div class="card">
                <h3>Agent Status</h3>
                <div id="agent-status">
                    {" ".join([f'<div><span class="status active">{agent_type}</span> Active</div>' for agent_type in agent_types])}
                </div>
            </div>
            
            <div class="card">
                <h3>Available Tools</h3>
                <ul>
                    <li>Code Generation</li>
                    <li>Logic Validation</li>
                    <li>Code Completion</li>
                    <li>Live Data Integration</li>
                    <li>Performance Analysis</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>Server Metrics</h3>
                <div>
                    <div class="metric">Server: Running</div>
                    <div class="metric">Tools: {len(self.tools)}</div>
                    <div class="metric">Uptime: {self.server_metrics["uptime_start"]}</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        '''
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "server_name": self.server_name,
            "tools_available": len(self.tools),
            "intelligence_features": len(self.intelligence_tools),
            "uptime_start": self.server_metrics["uptime_start"],
            "capabilities": [
                "financial_code_generation",
                "real_time_validation",
                "code_intelligence",
                "development_dashboard",
                "performance_analysis"
            ]
        }


# Entry point for IDE integration
async def main():
    """Start IDE-enhanced MCP server"""
    server = FinancialDevMCPServer()
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
