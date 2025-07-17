# mcp/interactive_dashboard.py
"""Interactive analysis dashboard for financial development"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class InteractiveDashboard:
    """Interactive financial analysis dashboard generator"""
    
    def __init__(self):
        self.dashboard_templates = {}
        self.active_dashboards = {}
        self.dashboard_data = {}
        
        # Load dashboard templates
        self._setup_dashboard_templates()
    
    def _setup_dashboard_templates(self):
        """Setup predefined dashboard templates"""
        
        # Comprehensive financial analysis dashboard
        self.dashboard_templates["comprehensive"] = {
            "title": "Financial Multi-Agent Analysis Dashboard",
            "components": [
                "price_chart",
                "technical_indicators",
                "risk_metrics",
                "agent_status",
                "performance_monitor",
                "live_data_feed"
            ],
            "layout": "grid",
            "refresh_interval": 5000
        }
        
        # Risk monitoring dashboard
        self.dashboard_templates["risk_monitoring"] = {
            "title": "Risk Monitoring Dashboard",
            "components": [
                "risk_metrics",
                "var_chart",
                "portfolio_allocation",
                "risk_alerts",
                "correlation_heatmap"
            ],
            "layout": "risk_focused",
            "refresh_interval": 2000
        }
        
        # Development monitoring dashboard
        self.dashboard_templates["development"] = {
            "title": "Development Monitoring Dashboard",
            "components": [
                "agent_status",
                "message_flow",
                "performance_metrics",
                "error_tracking",
                "system_health"
            ],
            "layout": "development_focused",
            "refresh_interval": 3000
        }
        
        # Market overview dashboard
        self.dashboard_templates["market_overview"] = {
            "title": "Market Overview Dashboard",
            "components": [
                "market_indices",
                "sector_performance",
                "market_breadth",
                "top_movers",
                "economic_indicators"
            ],
            "layout": "market_focused",
            "refresh_interval": 10000
        }
    
    async def create_analysis_dashboard(self, symbols: List[str], 
                                     dashboard_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Create interactive financial analysis dashboard
        
        Args:
            symbols: List of symbols to include in dashboard
            dashboard_type: Type of dashboard to create
            
        Returns:
            Dashboard configuration and HTML
        """
        try:
            dashboard_id = f"dashboard_{dashboard_type}_{datetime.now().strftime('%H%M%S')}"
            
            if dashboard_type not in self.dashboard_templates:
                dashboard_type = "comprehensive"
            
            template = self.dashboard_templates[dashboard_type]
            
            # Generate dashboard HTML
            dashboard_html = self._generate_dashboard_html(
                dashboard_id, symbols, template
            )
            
            # Store dashboard configuration
            self.active_dashboards[dashboard_id] = {
                "symbols": symbols,
                "dashboard_type": dashboard_type,
                "template": template,
                "created_at": datetime.now().isoformat(),
                "last_updated": None
            }
            
            return {
                "dashboard_id": dashboard_id,
                "dashboard_url": f"http://localhost:8000/dashboard/{dashboard_id}",
                "dashboard_html": dashboard_html,
                "websocket_endpoint": f"ws://localhost:8000/dashboard-ws/{dashboard_id}",
                "symbols": symbols,
                "dashboard_type": dashboard_type,
                "refresh_interval": template["refresh_interval"],
                "components": template["components"]
            }
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {str(e)}")
            return {"error": str(e)}
    
    def _generate_dashboard_html(self, dashboard_id: str, symbols: List[str], 
                               template: Dict[str, Any]) -> str:
        """Generate dashboard HTML based on template"""
        
        components_html = self._generate_components_html(symbols, template["components"])
        
        dashboard_html = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{template["title"]}</title>
    
    <!-- External Libraries -->
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <style>
        {self._generate_dashboard_css(template["layout"])}
    </style>
</head>
<body>
    <div class="dashboard-container" id="dashboard-{dashboard_id}">
        <header class="dashboard-header">
            <h1>{template["title"]}</h1>
            <div class="dashboard-controls">
                <div class="status-indicator" id="connection-status">
                    <span class="status-dot"></span>
                    <span class="status-text">Connecting...</span>
                </div>
                <div class="symbol-selector">
                    <span>Symbols: {", ".join(symbols)}</span>
                </div>
                <div class="refresh-control">
                    <button id="refresh-btn" onclick="refreshDashboard()">Refresh</button>
                    <span id="last-update">Last updated: Never</span>
                </div>
            </div>
        </header>
        
        <main class="dashboard-content">
            {components_html}
        </main>
        
        <footer class="dashboard-footer">
            <div class="footer-info">
                <span>Dashboard ID: {dashboard_id}</span>
                <span>Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
                <span>Update Interval: {template["refresh_interval"]}ms</span>
            </div>
        </footer>
    </div>
    
    <script>
        {self._generate_dashboard_javascript(dashboard_id, symbols, template)}
    </script>
    
    <script>
        {self._generate_chart_initialization_script(symbols)}
    </script>
</body>
</html>
        '''
        
        return dashboard_html
    
    def _generate_chart_initialization_script(self, symbols: List[str]) -> str:
        """Generate chart initialization script with sample data"""
        symbols_json = json.dumps(symbols)
        
        return f'''
        // Chart initialization with sample data
        function initializeChartsWithData() {{
            console.log('Initializing charts with sample data...');
            
            // Generate sample dates
            const dates = [];
            for (let i = 29; i >= 0; i--) {{
                const date = new Date();
                date.setDate(date.getDate() - i);
                dates.push(date.toISOString().split('T')[0]);
            }}
            
            // Price Chart with real sample data
            const priceChart = document.getElementById('price-chart');
            if (priceChart && typeof Plotly !== 'undefined') {{
                const symbols = {symbols_json};
                const traces = [];
                const colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'];
                
                symbols.forEach((symbol, index) => {{
                    const prices = [];
                    let basePrice = symbol === 'AAPL' ? 210 : symbol === 'MSFT' ? 505 : 183;
                    
                    for (let i = 0; i < 30; i++) {{
                        basePrice = basePrice * (1 + (Math.random() - 0.5) * 0.02);
                        prices.push(basePrice);
                    }}
                    
                    traces.push({{
                        x: dates,
                        y: prices,
                        type: 'scatter',
                        mode: 'lines',
                        name: symbol,
                        line: {{ color: colors[index % colors.length], width: 2 }}
                    }});
                }});
                
                const layout = {{
                    title: 'Stock Price Trends (30 Days)',
                    xaxis: {{ title: 'Date' }},
                    yaxis: {{ title: 'Price ($)' }},
                    margin: {{ t: 50, r: 50, b: 50, l: 50 }},
                    showlegend: true
                }};
                
                Plotly.newPlot(priceChart, traces, layout);
                console.log('✅ Price chart initialized');
            }}
            
            // RSI Chart
            const rsiChart = document.getElementById('rsi-chart');
            if (rsiChart && typeof Plotly !== 'undefined') {{
                const rsiDates = dates.slice(-14);
                const rsiValues = [];
                
                for (let i = 0; i < 14; i++) {{
                    const rsi = 50 + Math.sin(i * 0.3) * 20 + (Math.random() - 0.5) * 10;
                    rsiValues.push(Math.max(0, Math.min(100, rsi)));
                }}
                
                const traces = [{{
                    x: rsiDates,
                    y: rsiValues,
                    type: 'scatter',
                    mode: 'lines',
                    name: 'RSI',
                    line: {{ color: 'purple', width: 2 }}
                }}];
                
                const layout = {{
                    title: 'RSI (14)',
                    xaxis: {{ title: 'Date' }},
                    yaxis: {{ title: 'RSI', range: [0, 100] }},
                    margin: {{ t: 30, r: 20, b: 30, l: 40 }},
                    height: 150,
                    shapes: [
                        {{
                            type: 'line',
                            x0: rsiDates[0],
                            y0: 70,
                            x1: rsiDates[rsiDates.length-1],
                            y1: 70,
                            line: {{ color: 'red', dash: 'dash', width: 1 }}
                        }},
                        {{
                            type: 'line',
                            x0: rsiDates[0],
                            y0: 30,
                            x1: rsiDates[rsiDates.length-1],
                            y1: 30,
                            line: {{ color: 'green', dash: 'dash', width: 1 }}
                        }}
                    ]
                }};
                
                Plotly.newPlot(rsiChart, traces, layout);
                console.log('✅ RSI chart initialized');
            }}
            
            // MACD Chart
            const macdChart = document.getElementById('macd-chart');
            if (macdChart && typeof Plotly !== 'undefined') {{
                const macdValues = [];
                const signalValues = [];
                
                for (let i = 0; i < 14; i++) {{
                    const macd = Math.sin(i * 0.2) * 2 + (Math.random() - 0.5) * 0.5;
                    const signal = Math.sin(i * 0.2 + 0.1) * 1.8 + (Math.random() - 0.5) * 0.3;
                    macdValues.push(macd);
                    signalValues.push(signal);
                }}
                
                const traces = [
                    {{
                        x: rsiDates,
                        y: macdValues,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'MACD',
                        line: {{ color: 'blue', width: 2 }}
                    }},
                    {{
                        x: rsiDates,
                        y: signalValues,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Signal',
                        line: {{ color: 'red', dash: 'dash', width: 2 }}
                    }}
                ];
                
                const layout = {{
                    title: 'MACD',
                    xaxis: {{ title: 'Date' }},
                    yaxis: {{ title: 'MACD' }},
                    margin: {{ t: 30, r: 20, b: 30, l: 40 }},
                    height: 150,
                    showlegend: true
                }};
                
                Plotly.newPlot(macdChart, traces, layout);
                console.log('✅ MACD chart initialized');
            }}
            
            // Performance Chart
            const perfChart = document.getElementById('performance-chart');
            if (perfChart && typeof Plotly !== 'undefined') {{
                const perfDates = [];
                const processingTimes = [];
                
                for (let i = 19; i >= 0; i--) {{
                    const date = new Date();
                    date.setMinutes(date.getMinutes() - i * 5);
                    perfDates.push(date.toLocaleTimeString());
                    processingTimes.push(30 + Math.random() * 40);
                }}
                
                const trace = {{
                    x: perfDates,
                    y: processingTimes,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'Processing Time',
                    line: {{ color: 'orange', width: 2 }},
                    marker: {{ size: 6, color: 'orange' }}
                }};
                
                const layout = {{
                    title: 'System Performance',
                    xaxis: {{ title: 'Time' }},
                    yaxis: {{ title: 'Processing Time (ms)' }},
                    margin: {{ t: 50, r: 50, b: 50, l: 50 }}
                }};
                
                Plotly.newPlot(perfChart, [trace], layout);
                console.log('✅ Performance chart initialized');
            }}
            
            // Update other components with sample data
            updateRiskMetricsWithSampleData();
            updatePerformanceMetricsWithSampleData();
            updateAgentStatusWithSampleData();
        }}
        
        function updateRiskMetricsWithSampleData() {{
            const varElement = document.getElementById('var-95');
            const sharpeElement = document.getElementById('sharpe-ratio');
            const drawdownElement = document.getElementById('max-drawdown');
            const volatilityElement = document.getElementById('volatility');
            
            if (varElement) varElement.textContent = '-2.34%';
            if (sharpeElement) sharpeElement.textContent = '1.45';
            if (drawdownElement) drawdownElement.textContent = '-8.92%';
            if (volatilityElement) volatilityElement.textContent = '15.67%';
            
            console.log('✅ Risk metrics updated');
        }}
        
        function updatePerformanceMetricsWithSampleData() {{
            const avgTimeElement = document.getElementById('avg-processing-time');
            const successRateElement = document.getElementById('success-rate');
            const throughputElement = document.getElementById('throughput');
            
            if (avgTimeElement) avgTimeElement.textContent = '45.2ms';
            if (successRateElement) successRateElement.textContent = '96.7%';
            if (throughputElement) throughputElement.textContent = '15.7 req/min';
            
            console.log('✅ Performance metrics updated');
        }}
        
        function updateAgentStatusWithSampleData() {{
            const agents = ['datacollectionagent', 'businessintelligenceagent', 'riskassessmentagent', 
                           'recommendationagent', 'reportgenerationagent', 'triageagent'];
            
            agents.forEach(agent => {{
                const statusElement = document.getElementById(`status-${{agent}}`);
                const queueElement = document.getElementById(`queue-${{agent}}`);
                const processedElement = document.getElementById(`processed-${{agent}}`);
                const agentCard = document.getElementById(`agent-${{agent}}`);
                
                if (statusElement) statusElement.textContent = 'Active';
                if (queueElement) queueElement.textContent = Math.floor(Math.random() * 5).toString();
                if (processedElement) processedElement.textContent = Math.floor(Math.random() * 200 + 50).toString();
                if (agentCard) agentCard.classList.add('active');
            }});
            
            console.log('✅ Agent status updated');
        }}
        
        // Initialize charts after page load and Plotly is ready
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Dashboard loaded, waiting for Plotly...');
            
            // Check if Plotly is loaded, if not wait
            function waitForPlotly() {{
                if (typeof Plotly !== 'undefined') {{
                    console.log('Plotly loaded, initializing charts...');
                    setTimeout(initializeChartsWithData, 1000);
                }} else {{
                    console.log('Waiting for Plotly to load...');
                    setTimeout(waitForPlotly, 500);
                }}
            }}
            
            waitForPlotly();
        }});
        
        // Update charts periodically
        setInterval(() => {{
            console.log('Periodic update...');
            updateRiskMetricsWithSampleData();
            updatePerformanceMetricsWithSampleData();
        }}, 10000);
        '''
    
    def _generate_components_html(self, symbols: List[str], components: List[str]) -> str:
        """Generate HTML for dashboard components"""
        
        component_generators = {
            "price_chart": self._generate_price_chart_html,
            "technical_indicators": self._generate_technical_indicators_html,
            "risk_metrics": self._generate_risk_metrics_html,
            "agent_status": self._generate_agent_status_html,
            "performance_monitor": self._generate_performance_monitor_html,
            "live_data_feed": self._generate_live_data_feed_html,
            "var_chart": self._generate_var_chart_html,
            "portfolio_allocation": self._generate_portfolio_allocation_html,
            "risk_alerts": self._generate_risk_alerts_html,
            "correlation_heatmap": self._generate_correlation_heatmap_html,
            "message_flow": self._generate_message_flow_html,
            "error_tracking": self._generate_error_tracking_html,
            "system_health": self._generate_system_health_html,
            "market_indices": self._generate_market_indices_html,
            "sector_performance": self._generate_sector_performance_html,
            "market_breadth": self._generate_market_breadth_html,
            "top_movers": self._generate_top_movers_html,
            "economic_indicators": self._generate_economic_indicators_html
        }
        
        components_html = []
        for component in components:
            if component in component_generators:
                html = component_generators[component](symbols)
                components_html.append(html)
        
        return "\n".join(components_html)
    
    def _generate_price_chart_html(self, symbols: List[str]) -> str:
        """Generate price chart component HTML"""
        return f'''
        <div class="dashboard-component price-chart-component">
            <div class="component-header">
                <h3>Price Charts</h3>
                <div class="component-controls">
                    <select id="price-timeframe">
                        <option value="1D">1 Day</option>
                        <option value="1W">1 Week</option>
                        <option value="1M" selected>1 Month</option>
                        <option value="3M">3 Months</option>
                    </select>
                </div>
            </div>
            <div class="component-content">
                <div id="price-chart" class="chart-container"></div>
            </div>
        </div>
        '''
    
    def _generate_technical_indicators_html(self, symbols: List[str]) -> str:
        """Generate technical indicators component HTML"""
        return f'''
        <div class="dashboard-component technical-indicators-component">
            <div class="component-header">
                <h3>Technical Indicators</h3>
            </div>
            <div class="component-content">
                <div class="indicators-grid">
                    <div id="rsi-chart" class="indicator-chart"></div>
                    <div id="macd-chart" class="indicator-chart"></div>
                    <div id="bb-chart" class="indicator-chart"></div>
                    <div id="volume-chart" class="indicator-chart"></div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_risk_metrics_html(self, symbols: List[str]) -> str:
        """Generate risk metrics component HTML"""
        return f'''
        <div class="dashboard-component risk-metrics-component">
            <div class="component-header">
                <h3>Risk Metrics</h3>
            </div>
            <div class="component-content">
                <div class="risk-metrics-grid">
                    <div class="risk-metric-card">
                        <div class="metric-label">VaR (95%)</div>
                        <div class="metric-value" id="var-95">-</div>
                        <div class="metric-change" id="var-95-change">-</div>
                    </div>
                    <div class="risk-metric-card">
                        <div class="metric-label">Sharpe Ratio</div>
                        <div class="metric-value" id="sharpe-ratio">-</div>
                        <div class="metric-change" id="sharpe-change">-</div>
                    </div>
                    <div class="risk-metric-card">
                        <div class="metric-label">Max Drawdown</div>
                        <div class="metric-value" id="max-drawdown">-</div>
                        <div class="metric-change" id="drawdown-change">-</div>
                    </div>
                    <div class="risk-metric-card">
                        <div class="metric-label">Volatility</div>
                        <div class="metric-value" id="volatility">-</div>
                        <div class="metric-change" id="volatility-change">-</div>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_agent_status_html(self, symbols: List[str]) -> str:
        """Generate agent status component HTML"""
        agent_names = [
            "DataCollectionAgent",
            "BusinessIntelligenceAgent", 
            "RiskAssessmentAgent",
            "RecommendationAgent",
            "ReportGenerationAgent",
            "TriageAgent"
        ]
        
        agent_cards = []
        for agent in agent_names:
            agent_cards.append(f'''
            <div class="agent-card" id="agent-{agent.lower()}">
                <div class="agent-name">{agent}</div>
                <div class="agent-status" id="status-{agent.lower()}">Unknown</div>
                <div class="agent-metrics">
                    <span class="metric">Queue: <span id="queue-{agent.lower()}">0</span></span>
                    <span class="metric">Processed: <span id="processed-{agent.lower()}">0</span></span>
                </div>
            </div>
            ''')
        
        return f'''
        <div class="dashboard-component agent-status-component">
            <div class="component-header">
                <h3>Agent Status</h3>
            </div>
            <div class="component-content">
                <div class="agents-grid">
                    {"".join(agent_cards)}
                </div>
            </div>
        </div>
        '''
    
    def _generate_performance_monitor_html(self, symbols: List[str]) -> str:
        """Generate performance monitor component HTML"""
        return f'''
        <div class="dashboard-component performance-monitor-component">
            <div class="component-header">
                <h3>Performance Monitor</h3>
            </div>
            <div class="component-content">
                <div id="performance-chart" class="chart-container"></div>
                <div class="performance-metrics">
                    <div class="perf-metric">
                        <span class="label">Avg Processing Time:</span>
                        <span class="value" id="avg-processing-time">-</span>
                    </div>
                    <div class="perf-metric">
                        <span class="label">Success Rate:</span>
                        <span class="value" id="success-rate">-</span>
                    </div>
                    <div class="perf-metric">
                        <span class="label">Throughput:</span>
                        <span class="value" id="throughput">-</span>
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def _generate_live_data_feed_html(self, symbols: List[str]) -> str:
        """Generate live data feed component HTML"""
        return f'''
        <div class="dashboard-component live-data-component">
            <div class="component-header">
                <h3>Live Market Data</h3>
            </div>
            <div class="component-content">
                <div class="live-data-table">
                    <table id="live-data-table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Price</th>
                                <th>Change</th>
                                <th>Change %</th>
                                <th>Volume</th>
                                <th>Time</th>
                            </tr>
                        </thead>
                        <tbody id="live-data-body">
                            <!-- Live data rows will be inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        '''
    
    # Add placeholder generators for other components
    def _generate_var_chart_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>VaR Analysis</h3><div id="var-chart"></div></div>'
    
    def _generate_portfolio_allocation_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Portfolio Allocation</h3><div id="allocation-chart"></div></div>'
    
    def _generate_risk_alerts_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Risk Alerts</h3><div id="risk-alerts-list"></div></div>'
    
    def _generate_correlation_heatmap_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Correlation Heatmap</h3><div id="correlation-heatmap"></div></div>'
    
    def _generate_message_flow_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Message Flow</h3><div id="message-flow-chart"></div></div>'
    
    def _generate_error_tracking_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Error Tracking</h3><div id="error-log"></div></div>'
    
    def _generate_system_health_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>System Health</h3><div id="system-health-metrics"></div></div>'
    
    def _generate_market_indices_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Market Indices</h3><div id="market-indices-table"></div></div>'
    
    def _generate_sector_performance_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Sector Performance</h3><div id="sector-chart"></div></div>'
    
    def _generate_market_breadth_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Market Breadth</h3><div id="market-breadth-chart"></div></div>'
    
    def _generate_top_movers_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Top Movers</h3><div id="top-movers-list"></div></div>'
    
    def _generate_economic_indicators_html(self, symbols: List[str]) -> str:
        return '<div class="dashboard-component"><h3>Economic Indicators</h3><div id="econ-indicators"></div></div>'
    
    def _generate_dashboard_css(self, layout: str) -> str:
        """Generate CSS for dashboard layout"""
        return '''
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #333;
        }
        
        .dashboard-container {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .dashboard-header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .dashboard-header h1 {
            font-size: 1.5rem;
            font-weight: 300;
        }
        
        .dashboard-controls {
            display: flex;
            align-items: center;
            gap: 2rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #e74c3c;
            animation: pulse 2s infinite;
        }
        
        .status-dot.connected {
            background: #27ae60;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .dashboard-content {
            flex: 1;
            padding: 2rem;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 1.5rem;
        }
        
        .dashboard-component {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .component-header {
            background: #34495e;
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .component-header h3 {
            font-size: 1.1rem;
            font-weight: 400;
        }
        
        .component-content {
            padding: 1.5rem;
        }
        
        .chart-container {
            height: 300px;
            width: 100%;
        }
        
        .indicators-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        
        .indicator-chart {
            height: 150px;
        }
        
        .risk-metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .risk-metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .metric-change {
            font-size: 0.8rem;
            margin-top: 0.3rem;
        }
        
        .metric-change.positive {
            color: #27ae60;
        }
        
        .metric-change.negative {
            color: #e74c3c;
        }
        
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }
        
        .agent-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        
        .agent-card.active {
            border-left-color: #27ae60;
        }
        
        .agent-card.error {
            border-left-color: #e74c3c;
        }
        
        .agent-name {
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .agent-status {
            color: #666;
            margin-bottom: 0.5rem;
        }
        
        .agent-metrics {
            display: flex;
            gap: 1rem;
            font-size: 0.9rem;
        }
        
        .live-data-table {
            overflow-x: auto;
        }
        
        .live-data-table table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .live-data-table th,
        .live-data-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .live-data-table th {
            background: #f8f9fa;
            font-weight: 600;
        }
        
        .price-positive {
            color: #27ae60;
        }
        
        .price-negative {
            color: #e74c3c;
        }
        
        .dashboard-footer {
            background: #ecf0f1;
            padding: 1rem 2rem;
            border-top: 1px solid #bdc3c7;
        }
        
        .footer-info {
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            color: #666;
        }
        
        .performance-metrics {
            display: flex;
            justify-content: space-around;
            margin-top: 1rem;
        }
        
        .perf-metric {
            text-align: center;
        }
        
        .perf-metric .label {
            display: block;
            font-size: 0.9rem;
            color: #666;
        }
        
        .perf-metric .value {
            display: block;
            font-size: 1.2rem;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 0.3rem;
        }
        
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        button:hover {
            background: #2980b9;
        }
        
        select {
            padding: 0.3rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
        }
        '''
    
    def _generate_dashboard_javascript(self, dashboard_id: str, symbols: List[str], 
                                     template: Dict[str, Any]) -> str:
        """Generate JavaScript for dashboard functionality"""
        return f'''
        // Dashboard configuration
        const dashboardConfig = {{
            dashboardId: '{dashboard_id}',
            symbols: {json.dumps(symbols)},
            refreshInterval: {template["refresh_interval"]},
            components: {json.dumps(template["components"])}
        }};
        
        // WebSocket connection
        let socket = null;
        let isConnected = false;
        
        // Data storage
        let dashboardData = {{}};
        let chartInstances = {{}};
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            initializeDashboard();
            connectWebSocket();
        }});
        
        function initializeDashboard() {{
            console.log('Initializing dashboard:', dashboardConfig.dashboardId);
            
            // Initialize charts based on components
            dashboardConfig.components.forEach(component => {{
                switch(component) {{
                    case 'price_chart':
                        initializePriceChart();
                        break;
                    case 'technical_indicators':
                        initializeTechnicalIndicators();
                        break;
                    case 'risk_metrics':
                        initializeRiskMetrics();
                        break;
                    case 'agent_status':
                        initializeAgentStatus();
                        break;
                    case 'performance_monitor':
                        initializePerformanceMonitor();
                        break;
                    case 'live_data_feed':
                        initializeLiveDataFeed();
                        break;
                }}
            }});
            
            // Set up periodic refresh
            setInterval(refreshDashboard, dashboardConfig.refreshInterval);
        }}
        
        function connectWebSocket() {{
            const wsUrl = `ws://localhost:8000/dashboard-ws/${{dashboardConfig.dashboardId}}`;
            
            try {{
                socket = io(wsUrl);
                
                socket.on('connect', function() {{
                    console.log('Connected to dashboard WebSocket');
                    isConnected = true;
                    updateConnectionStatus(true);
                }});
                
                socket.on('disconnect', function() {{
                    console.log('Disconnected from dashboard WebSocket');
                    isConnected = false;
                    updateConnectionStatus(false);
                }});
                
                socket.on('data_update', function(data) {{
                    handleDataUpdate(data);
                }});
                
                socket.on('agent_status', function(data) {{
                    updateAgentStatus(data);
                }});
                
                socket.on('risk_metrics', function(data) {{
                    updateRiskMetrics(data);
                }});
                
                socket.on('performance_metrics', function(data) {{
                    updatePerformanceMetrics(data);
                }});
                
            }} catch (error) {{
                console.error('WebSocket connection error:', error);
                updateConnectionStatus(false);
            }}
        }}
        
        function updateConnectionStatus(connected) {{
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-text');
            
            if (connected) {{
                statusDot.classList.add('connected');
                statusText.textContent = 'Connected';
            }} else {{
                statusDot.classList.remove('connected');
                statusText.textContent = 'Disconnected';
            }}
        }}
        
        function initializePriceChart() {{
            const chartDiv = document.getElementById('price-chart');
            if (!chartDiv) return;
            
            const layout = {{
                title: 'Price Chart',
                xaxis: {{ title: 'Time' }},
                yaxis: {{ title: 'Price ($)' }},
                margin: {{ t: 50, r: 50, b: 50, l: 50 }}
            }};
            
            // Create placeholder data
            const traces = dashboardConfig.symbols.map(symbol => ({{
                x: [],
                y: [],
                type: 'scatter',
                mode: 'lines',
                name: symbol
            }}));
            
            Plotly.newPlot(chartDiv, traces, layout);
            chartInstances['price-chart'] = chartDiv;
        }}
        
        function initializeTechnicalIndicators() {{
            // Initialize RSI chart
            const rsiDiv = document.getElementById('rsi-chart');
            if (rsiDiv) {{
                const layout = {{
                    title: 'RSI',
                    height: 150,
                    margin: {{ t: 30, r: 20, b: 30, l: 40 }}
                }};
                
                const trace = {{
                    x: [],
                    y: [],
                    type: 'scatter',
                    mode: 'lines',
                    name: 'RSI'
                }};
                
                Plotly.newPlot(rsiDiv, [trace], layout);
            }}
            
            // Initialize MACD chart
            const macdDiv = document.getElementById('macd-chart');
            if (macdDiv) {{
                const layout = {{
                    title: 'MACD',
                    height: 150,
                    margin: {{ t: 30, r: 20, b: 30, l: 40 }}
                }};
                
                const traces = [
                    {{ x: [], y: [], type: 'scatter', mode: 'lines', name: 'MACD' }},
                    {{ x: [], y: [], type: 'scatter', mode: 'lines', name: 'Signal' }}
                ];
                
                Plotly.newPlot(macdDiv, traces, layout);
            }}
        }}
        
        function initializeRiskMetrics() {{
            // Risk metrics are updated via data updates
            console.log('Risk metrics component initialized');
        }}
        
        function initializeAgentStatus() {{
            // Agent status is updated via WebSocket
            console.log('Agent status component initialized');
        }}
        
        function initializePerformanceMonitor() {{
            const chartDiv = document.getElementById('performance-chart');
            if (!chartDiv) return;
            
            const layout = {{
                title: 'System Performance',
                xaxis: {{ title: 'Time' }},
                yaxis: {{ title: 'Processing Time (ms)' }},
                margin: {{ t: 50, r: 50, b: 50, l: 50 }}
            }};
            
            const trace = {{
                x: [],
                y: [],
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Processing Time'
            }};
            
            Plotly.newPlot(chartDiv, [trace], layout);
        }}
        
        function initializeLiveDataFeed() {{
            // Live data feed table is updated via data updates
            console.log('Live data feed component initialized');
        }}
        
        function handleDataUpdate(data) {{
            dashboardData = {{ ...dashboardData, ...data }};
            
            // Update live data table
            updateLiveDataTable(data);
            
            // Update charts
            updateCharts(data);
            
            // Update last updated time
            document.getElementById('last-update').textContent = 
                `Last updated: ${{new Date().toLocaleTimeString()}}`;
        }}
        
        function updateLiveDataTable(data) {{
            const tbody = document.getElementById('live-data-body');
            if (!tbody || !data.market_data) return;
            
            tbody.innerHTML = '';
            
            Object.entries(data.market_data).forEach(([symbol, info]) => {{
                const row = document.createElement('tr');
                const changeClass = info.change >= 0 ? 'price-positive' : 'price-negative';
                const changeSign = info.change >= 0 ? '+' : '';
                
                row.innerHTML = `
                    <td>${{symbol}}</td>
                    <td>${{info.price.toFixed(2)}}</td>
                    <td class="${{changeClass}}">${{changeSign}}${{info.change.toFixed(2)}}</td>
                    <td class="${{changeClass}}">${{changeSign}}${{info.change_percent.toFixed(2)}}%</td>
                    <td>${{info.volume.toLocaleString()}}</td>
                    <td>${{new Date().toLocaleTimeString()}}</td>
                `;
                
                tbody.appendChild(row);
            }});
        }}
        
        function updateCharts(data) {{
            // Update price chart
            if (chartInstances['price-chart'] && data.price_data) {{
                // Add new price data points
                // This is a simplified implementation
                console.log('Updating price chart with new data');
            }}
        }}
        
        function updateAgentStatus(agentData) {{
            Object.entries(agentData).forEach(([agentName, status]) => {{
                const agentCard = document.getElementById(`agent-${{agentName.toLowerCase()}}`);
                if (agentCard) {{
                    const statusElement = document.getElementById(`status-${{agentName.toLowerCase()}}`);
                    const queueElement = document.getElementById(`queue-${{agentName.toLowerCase()}}`);
                    const processedElement = document.getElementById(`processed-${{agentName.toLowerCase()}}`);
                    
                    if (statusElement) statusElement.textContent = status.status || 'Unknown';
                    if (queueElement) queueElement.textContent = status.queue_size || '0';
                    if (processedElement) processedElement.textContent = status.processed || '0';
                    
                    // Update card styling based on status
                    agentCard.className = 'agent-card';
                    if (status.status === 'active') {{
                        agentCard.classList.add('active');
                    }} else if (status.status === 'error') {{
                        agentCard.classList.add('error');
                    }}
                }}
            }});
        }}
        
        function updateRiskMetrics(riskData) {{
            if (riskData.var_95) {{
                const varElement = document.getElementById('var-95');
                if (varElement) varElement.textContent = `${{(riskData.var_95 * 100).toFixed(2)}}%`;
            }}
            
            if (riskData.sharpe_ratio) {{
                const sharpeElement = document.getElementById('sharpe-ratio');
                if (sharpeElement) sharpeElement.textContent = riskData.sharpe_ratio.toFixed(2);
            }}
            
            if (riskData.max_drawdown) {{
                const ddElement = document.getElementById('max-drawdown');
                if (ddElement) ddElement.textContent = `${{(riskData.max_drawdown * 100).toFixed(2)}}%`;
            }}
            
            if (riskData.volatility) {{
                const volElement = document.getElementById('volatility');
                if (volElement) volElement.textContent = `${{(riskData.volatility * 100).toFixed(2)}}%`;
            }}
        }}
        
        function updatePerformanceMetrics(perfData) {{
            if (perfData.avg_processing_time) {{
                const avgTimeElement = document.getElementById('avg-processing-time');
                if (avgTimeElement) avgTimeElement.textContent = `${{perfData.avg_processing_time.toFixed(2)}}ms`;
            }}
            
            if (perfData.success_rate) {{
                const successRateElement = document.getElementById('success-rate');
                if (successRateElement) successRateElement.textContent = `${{(perfData.success_rate * 100).toFixed(1)}}%`;
            }}
            
            if (perfData.throughput) {{
                const throughputElement = document.getElementById('throughput');
                if (throughputElement) throughputElement.textContent = `${{perfData.throughput.toFixed(1)}} req/min`;
            }}
        }}
        
        function refreshDashboard() {{
            if (isConnected && socket) {{
                socket.emit('request_update', {{
                    dashboard_id: dashboardConfig.dashboardId,
                    symbols: dashboardConfig.symbols
                }});
            }} else {{
                // Fallback: fetch data via HTTP
                fetchDashboardData();
            }}
        }}
        
        async function fetchDashboardData() {{
            try {{
                const response = await fetch(`/api/dashboard-data/${{dashboardConfig.dashboardId}}`);
                const data = await response.json();
                handleDataUpdate(data);
            }} catch (error) {{
                console.error('Error fetching dashboard data:', error);
            }}
        }}
        
        // Global functions for UI interactions
        window.refreshDashboard = refreshDashboard;
        
        window.changePriceTimeframe = function(timeframe) {{
            console.log('Changing price timeframe to:', timeframe);
            // Implement timeframe change logic
        }};
        '''


# Global dashboard instance
interactive_dashboard = InteractiveDashboard()


# Convenience functions for creating dashboards
async def create_comprehensive_dashboard(symbols: List[str]) -> Dict[str, Any]:
    """Create a comprehensive financial analysis dashboard"""
    return await interactive_dashboard.create_analysis_dashboard(symbols, "comprehensive")


async def create_risk_dashboard(symbols: List[str]) -> Dict[str, Any]:
    """Create a risk monitoring dashboard"""
    return await interactive_dashboard.create_analysis_dashboard(symbols, "risk_monitoring")


async def create_development_dashboard(symbols: List[str]) -> Dict[str, Any]:
    """Create a development monitoring dashboard"""
    return await interactive_dashboard.create_analysis_dashboard(symbols, "development")


async def create_market_dashboard(symbols: List[str]) -> Dict[str, Any]:
    """Create a market overview dashboard"""
    return await interactive_dashboard.create_analysis_dashboard(symbols, "market_overview")


if __name__ == "__main__":
    # Test dashboard generation
    async def test_dashboard():
        symbols = ["AAPL", "MSFT", "GOOGL"]
        
        # Test comprehensive dashboard
        result = await interactive_dashboard.create_analysis_dashboard(symbols, "comprehensive")
        print("Dashboard created:", result.get("dashboard_id"))
        
        # Save HTML for testing
        if "dashboard_html" in result:
            with open("test_dashboard.html", "w") as f:
                f.write(result["dashboard_html"])
            print("Test dashboard saved to test_dashboard.html")
    
    asyncio.run(test_dashboard())
