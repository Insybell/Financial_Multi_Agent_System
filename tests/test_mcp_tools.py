# tests/test_mcp_tools.py
"""Test script for MCP development server tools"""

import asyncio
import sys
import os

# Add the project root to the path (going up one level from tests/ to project root)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp.dev_server import FinancialDevMCPServer

async def test_mcp_tools():
    """Test the MCP development server tools"""
    print("🧪 Testing MCP Development Server Tools")
    print("=" * 50)
    
    # Initialize the server (but don't start the main loop)
    server = FinancialDevMCPServer()
    
    # Test 1: Generate Data Collection Agent Code
    print("\n1. Testing Code Generation...")
    try:
        result = await server._generate_financial_agent_code(
            agent_type="data_collection",
            functionality="real-time data fetching",
            requirements=["yfinance integration", "error handling", "caching"]
        )
        print("✅ Code generation successful")
        print(f"Generated code length: {len(result)} characters")
    except Exception as e:
        print(f"❌ Code generation failed: {e}")
    
    # Test 2: Validate Financial Logic
    print("\n2. Testing Financial Logic Validation...")
    try:
        sample_code = """
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    excess_returns = returns - risk_free_rate
    return excess_returns.mean() / excess_returns.std()
"""
        result = await server._validate_financial_logic(sample_code, "risk_analysis")
        print("✅ Logic validation successful")
        print("Validation result preview:", result[:100] + "...")
    except Exception as e:
        print(f"❌ Logic validation failed: {e}")
    
    # Test 3: Code Completion
    print("\n3. Testing Code Completion...")
    try:
        result = await server._financial_code_completion(
            context="def calculate_",
            cursor_position=15,
            file_type="python"
        )
        print("✅ Code completion successful")
        print("Number of completions generated:", result.count("label"))
    except Exception as e:
        print(f"❌ Code completion failed: {e}")
    
    # Test 4: Market Data Integration
    print("\n4. Testing Market Data Integration...")
    try:
        result = await server._live_market_data_integration(
            symbols=["AAPL", "MSFT"],
            update_frequency=5000
        )
        print("✅ Market data integration successful")
        print("Stream configuration generated")
    except Exception as e:
        print(f"❌ Market data integration failed: {e}")
    
    # Test 5: Development Dashboard
    print("\n5. Testing Development Dashboard...")
    try:
        result = await server._create_development_dashboard(
            agent_types=["data_collection", "risk_assessment"],
            metrics=["performance", "accuracy"]
        )
        print("✅ Development dashboard successful")
        print("Dashboard HTML generated")
    except Exception as e:
        print(f"❌ Development dashboard failed: {e}")
    
    # Test 6: Performance Analysis
    print("\n6. Testing Performance Analysis...")
    try:
        sample_code = """
import pandas as pd
import numpy as np

def analyze_portfolio(data):
    for i in range(len(data)):
        result = data.iloc[i] * 2
    return result
"""
        result = await server._analyze_code_performance(sample_code, "development")
        print("✅ Performance analysis successful")
        print("Analysis completed with suggestions")
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
    
    # Display server info
    print("\n" + "=" * 50)
    print("📊 MCP Server Information:")
    server_info = server.get_server_info()
    for key, value in server_info.items():
        print(f"   {key}: {value}")
    
    print("\n🎉 MCP Tools Testing Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
