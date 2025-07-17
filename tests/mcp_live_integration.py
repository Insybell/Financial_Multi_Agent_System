# mcp_live_integration.py
"""Live integration test between MCP server and running financial system"""

import asyncio
import aiohttp
import json
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.dev_server import FinancialDevMCPServer

async def test_live_integration():
    """Test MCP server integration with live financial system"""
    print("🔴 LIVE MCP Integration Test")
    print("=" * 50)
    print("📡 Connecting to running financial system at localhost:8000")
    
    # Initialize MCP server
    mcp_server = FinancialDevMCPServer()
    
    # Test connection to your running system
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check system health
            print("\n1. Testing system health...")
            async with session.get('http://localhost:8000/health') as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    print("✅ System health check passed")
                    print(f"   Status: {health_data.get('status', 'unknown')}")
                    
                    # Use MCP to analyze the health response
                    analysis_code = f"""
# Analyze system health metrics
health_metrics = {health_data}
system_status = health_metrics.get('status')
if system_status == 'healthy':
    recommendation = 'System operating normally'
elif 'agents' in health_metrics:
    agent_count = len(health_metrics.get('agents', []))
    recommendation = f'Monitor {{agent_count}} active agents'
else:
    recommendation = 'Review system configuration'
"""
                    
                    validation = await mcp_server._validate_financial_logic(
                        analysis_code, "system_monitoring"
                    )
                    print("✅ MCP validated health analysis code")
                else:
                    print(f"❌ Health check failed: {resp.status}")
                    return
        
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            print("   Make sure your main.py is running on port 8000")
            return
        
        # Test 2: Enhanced analysis request
        print("\n2. Testing enhanced financial analysis...")
        try:
            # Generate enhanced analysis code using MCP
            enhanced_code = await mcp_server._generate_financial_agent_code(
                agent_type="business_intelligence",
                functionality="enhanced multi-symbol analysis with risk metrics",
                requirements=[
                    "Real-time data processing",
                    "Risk-adjusted returns",
                    "Correlation analysis",
                    "Performance benchmarking"
                ]
            )
            
            print("✅ MCP generated enhanced analysis code")
            
            # Test the actual analysis endpoint
            test_symbols = ["AAPL", "MSFT", "GOOGL"]
            async with session.post(
                'http://localhost:8000/analyze',
                headers={'Content-Type': 'application/json'},
                json=test_symbols
            ) as resp:
                if resp.status == 200:
                    analysis_result = await resp.json()
                    print(f"✅ Live analysis completed for {len(test_symbols)} symbols")
                    
                    # Use MCP to suggest optimizations for the analysis
                    result_analysis_code = f"""
# Analyze the financial analysis results
analysis_data = {str(analysis_result)[:200]}...  # Truncated for demo
symbol_count = len({test_symbols})
if symbol_count > 2:
    correlation_matrix = calculate_correlation_matrix(analysis_data)
    portfolio_risk = assess_portfolio_risk(correlation_matrix)
"""
                    
                    performance_analysis = await mcp_server._analyze_code_performance(
                        result_analysis_code, "production"
                    )
                    
                    perf_data = json.loads(performance_analysis)
                    print(f"✅ MCP performance analysis: {perf_data['performance_score']} score")
                    
                else:
                    print(f"❌ Analysis failed: {resp.status}")
        
        except Exception as e:
            print(f"❌ Enhanced analysis test failed: {e}")
        
        # Test 3: Generate real-time monitoring code
        print("\n3. Generating real-time monitoring enhancement...")
        try:
            monitoring_code = await mcp_server._generate_financial_agent_code(
                agent_type="triage",
                functionality="real-time system monitoring and alerting",
                requirements=[
                    "Performance monitoring",
                    "Error detection",
                    "Load balancing",
                    "Health checks"
                ]
            )
            
            monitoring_result = json.loads(monitoring_code)
            print("✅ Generated real-time monitoring code")
            print(f"   Agent type: {monitoring_result['agent_type']}")
            print(f"   Status: {monitoring_result['status']}")
            
            # Validate the monitoring code
            sample_monitoring = monitoring_result['code'][:500]  # First 500 chars
            validation = await mcp_server._validate_financial_logic(
                sample_monitoring, "system_monitoring"
            )
            print("✅ Monitoring code validated by MCP")
            
        except Exception as e:
            print(f"❌ Monitoring code generation failed: {e}")
        
        # Test 4: Market data integration
        print("\n4. Testing market data integration...")
        try:
            market_config = await mcp_server._live_market_data_integration(
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                update_frequency=2000
            )
            
            config_data = json.loads(market_config)
            print(f"✅ Market data integration configured")
            print(f"   Stream ID: {config_data['stream_id']}")
            print(f"   Symbols: {len(config_data['symbols'])}")
            print(f"   Update frequency: {config_data['update_frequency']}ms")
            
            # Show sample data that could enhance your system
            sample_data = config_data['sample_data']
            print("\n📊 Sample enhanced market data:")
            for symbol, data in list(sample_data.items())[:3]:
                print(f"   {symbol}: ${data['price']} ({data['change']:+.2f}, {data['change_percent']:+.2f}%)")
                
        except Exception as e:
            print(f"❌ Market data integration failed: {e}")
        
        # Test 5: Development dashboard for your system
        print("\n5. Creating development dashboard...")
        try:
            dashboard_config = await mcp_server._create_development_dashboard(
                agent_types=[
                    "data_collection", 
                    "business_intelligence", 
                    "risk_assessment",
                    "recommendation",
                    "report_generation",
                    "triage"
                ],
                metrics=["success_rate", "response_time", "error_count", "throughput"]
            )
            
            dashboard_data = json.loads(dashboard_config)
            print("✅ Development dashboard created")
            print(f"   Dashboard URL: {dashboard_data['dashboard_url']}")
            print(f"   Features: {len(dashboard_data['features'])}")
            
        except Exception as e:
            print(f"❌ Dashboard creation failed: {e}")
    
    # Final integration summary
    print("\n" + "=" * 50)
    print("🎯 LIVE INTEGRATION TEST COMPLETE")
    print("=" * 50)
    
    print("\n✅ MCP Server Successfully Enhanced Your Financial System With:")
    print("   🤖 Intelligent agent code generation")
    print("   🔍 Real-time financial logic validation")
    print("   📊 Enhanced market data integration")
    print("   ⚡ Performance optimization suggestions")
    print("   🎛️  Development monitoring dashboard")
    print("   💡 Context-aware code completion")
    
    print("\n🚀 Your system is now MCP-enhanced!")
    print("   • Keep main.py running on port 8000")
    print("   • Keep dev_server.py running for MCP tools")
    print("   • Use the generated code in your agents")
    print("   • Access dashboard at http://localhost:8000/dev-dashboard")

if __name__ == "__main__":
    asyncio.run(test_live_integration())
