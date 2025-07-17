# tests/mcp_integration_demo.py
"""Demonstration of MCP integration with existing financial agents"""

import asyncio
import json
import sys
import os

# Add the project root to the path (going up one level from tests/ to project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp.dev_server import FinancialDevMCPServer

async def demonstrate_mcp_integration():
    """Demonstrate how MCP enhances the financial multi-agent system"""
    print("🔗 MCP Integration Demonstration")
    print("=" * 60)
    
    server = FinancialDevMCPServer()
    
    # Scenario 1: Generate enhanced agent code
    print("\n📝 Scenario 1: Generate Enhanced Data Collection Agent")
    print("-" * 50)
    
    enhanced_agent_code = await server._generate_financial_agent_code(
        agent_type="data_collection",
        functionality="real-time market data with ML preprocessing",
        requirements=[
            "Multi-source data aggregation",
            "Real-time validation",
            "Automated quality scoring",
            "Cache optimization",
            "Error recovery"
        ]
    )
    
    code_result = json.loads(enhanced_agent_code)
    print(f"✅ Generated {code_result['agent_type']} agent")
    print(f"📦 Includes: imports, code, tests, documentation")
    print(f"🎯 Functionality: {code_result['functionality']}")
    
    # Scenario 2: Validate existing financial calculations
    print("\n🔍 Scenario 2: Validate Financial Calculations")
    print("-" * 50)
    
    # Sample code that might exist in your current agents
    sample_financial_code = """
import numpy as np
import pandas as pd

def calculate_portfolio_metrics(returns_data):
    # Calculate Sharpe ratio
    excess_returns = returns_data - 0.02  # Missing risk_free_rate parameter
    sharpe_ratio = excess_returns.mean() / excess_returns.std()
    
    # Calculate VaR without confidence level specification
    var = np.percentile(returns_data, 5)
    
    # Calculate maximum drawdown
    cumulative_returns = (1 + returns_data).cumprod()
    rolling_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    return {
        'sharpe_ratio': sharpe_ratio,
        'var': var,
        'max_drawdown': max_drawdown
    }
"""
    
    validation_result = await server._validate_financial_logic(
        sample_financial_code, 
        "portfolio_analysis"
    )
    
    validation_data = json.loads(validation_result)
    print(f"✅ Validation completed")
    print(f"🚨 Warnings: {len(validation_data.get('warnings', []))}")
    print(f"💡 Suggestions: {len(validation_data.get('suggestions', []))}")
    
    if validation_data.get('warnings'):
        print("\n⚠️  Warnings found:")
        for warning in validation_data['warnings']:
            print(f"   • {warning}")
    
    # Scenario 3: Get intelligent code completions
    print("\n💡 Scenario 3: Intelligent Code Completion")
    print("-" * 50)
    
    completion_result = await server._financial_code_completion(
        context="def calculate_risk_",
        cursor_position=20,
        file_type="python"
    )
    
    completion_data = json.loads(completion_result)
    print(f"✅ Generated {len(completion_data['completions'])} completions")
    
    # Show some completions
    for i, completion in enumerate(completion_data['completions'][:3], 1):
        print(f"   {i}. {completion['label']}: {completion['detail']}")
    
    # Scenario 4: Live market data for development
    print("\n📊 Scenario 4: Live Market Data Integration")
    print("-" * 50)
    
    market_data_config = await server._live_market_data_integration(
        symbols=["AAPL", "MSFT", "GOOGL", "TSLA"],
        update_frequency=3000
    )
    
    market_config = json.loads(market_data_config)
    print(f"✅ Market data stream configured")
    print(f"🔗 WebSocket: {market_config['websocket_url']}")
    print(f"📡 REST API: {market_config['rest_endpoint']}")
    print(f"📈 Tracking: {len(market_config['symbols'])} symbols")
    print(f"⏱️  Update frequency: {market_config['update_frequency']}ms")
    
    # Show sample data
    print("\n📋 Sample Market Data:")
    for symbol, data in list(market_config['sample_data'].items())[:2]:
        print(f"   {symbol}: ${data['price']} ({data['change']:+.2f})")
    
    # Scenario 5: Performance analysis
    print("\n⚡ Scenario 5: Code Performance Analysis")
    print("-" * 50)
    
    # Sample code with potential performance issues
    performance_test_code = """
import pandas as pd
import numpy as np

def analyze_returns(price_data):
    returns = []
    for i in range(1, len(price_data)):
        daily_return = (price_data[i] - price_data[i-1]) / price_data[i-1]
        returns.append(daily_return)
    
    # Calculate rolling statistics in a loop
    rolling_means = []
    window = 20
    for i in range(window, len(returns)):
        window_data = returns[i-window:i]
        rolling_means.append(np.mean(window_data))
    
    return returns, rolling_means
"""
    
    performance_analysis = await server._analyze_code_performance(
        performance_test_code,
        "production"
    )
    
    perf_data = json.loads(performance_analysis)
    print(f"✅ Performance analysis completed")
    print(f"📊 Performance score: {perf_data['performance_score']}")
    print(f"💾 Memory usage: {perf_data['memory_usage']}")
    print(f"⏱️  Execution estimate: {perf_data['execution_time_estimate']}")
    print(f"📈 Scalability: {perf_data['scalability_rating']}")
    
    if perf_data.get('optimizations'):
        print("\n🚀 Optimization suggestions:")
        for opt in perf_data['optimizations']:
            print(f"   • {opt['description']} ({opt['impact']} impact)")
            print(f"     💡 {opt['suggestion']}")
    
    # Scenario 6: Development dashboard
    print("\n🎛️  Scenario 6: Development Dashboard")
    print("-" * 50)
    
    dashboard_config = await server._create_development_dashboard(
        agent_types=["data_collection", "business_intelligence", "risk_assessment"],
        metrics=["performance", "accuracy", "throughput"]
    )
    
    dashboard_data = json.loads(dashboard_config)
    print(f"✅ Development dashboard created")
    print(f"🌐 Dashboard URL: {dashboard_data['dashboard_url']}")
    print(f"🔌 WebSocket: {dashboard_data['websocket_endpoint']}")
    print(f"⚡ Update interval: {dashboard_data['update_interval']}ms")
    
    print("\n🎯 Dashboard Features:")
    for feature in dashboard_data['features']:
        print(f"   • {feature}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 MCP Integration Demonstration Complete!")
    print("=" * 60)
    print(f"🛠️  Total tools available: {len(server.tools)}")
    print(f"🧠 Intelligence features: {len(server.intelligence_tools)}")
    print(f"📅 Server started: {server.server_metrics['uptime_start']}")
    
    print("\n🚀 Your MCP-enhanced system now provides:")
    print("   • Intelligent code generation for financial agents")
    print("   • Real-time validation of financial calculations")
    print("   • Context-aware code completion")
    print("   • Live market data integration")
    print("   • Performance optimization suggestions")
    print("   • Interactive development dashboard")
    
    print(f"\n💡 Next steps:")
    print("   1. Integrate MCP tools into your existing agents")
    print("   2. Use the development dashboard for monitoring")
    print("   3. Leverage code completion in Cursor IDE")
    print("   4. Validate financial logic in real-time")

if __name__ == "__main__":
    asyncio.run(demonstrate_mcp_integration())
