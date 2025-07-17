function initializeChartsWithData() {
    console.log('Initializing charts with sample data...');
    
    // Price Chart
    const priceChart = document.getElementById('price-chart');
    if (priceChart) {
        const dates = [];
        const prices_aapl = [];
        const prices_msft = [];
        const prices_googl = [];
        
        // Generate sample data for last 30 days
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            dates.push(date.toISOString().split('T')[0]);
            
            // Sample price movements
            prices_aapl.push(210 + Math.sin(i * 0.1) * 5 + Math.random() * 3);
            prices_msft.push(505 + Math.cos(i * 0.1) * 8 + Math.random() * 4);
            prices_googl.push(183 + Math.sin(i * 0.15) * 6 + Math.random() * 3);
        }
        
        const traces = [
            {
                x: dates,
                y: prices_aapl,
                type: 'scatter',
                mode: 'lines',
                name: 'AAPL',
                line: { color: '#1f77b4' }
            },
            {
                x: dates,
                y: prices_msft,
                type: 'scatter',
                mode: 'lines',
                name: 'MSFT',
                line: { color: '#ff7f0e' }
            },
            {
                x: dates,
                y: prices_googl,
                type: 'scatter',
                mode: 'lines',
                name: 'GOOGL',
                line: { color: '#2ca02c' }
            }
        ];
        
        const layout = {
            title: 'Stock Price Trends',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Price ($)' },
            margin: { t: 50, r: 50, b: 50, l: 50 }
        };
        
        Plotly.newPlot(priceChart, traces, layout);
        console.log('✅ Price chart initialized');
    }
    
    // RSI Chart
    const rsiChart = document.getElementById('rsi-chart');
    if (rsiChart) {
        const rsiDates = dates.slice(-14); // Last 14 days
        const rsiValues = Array.from({length: 14}, (_, i) => 50 + Math.sin(i * 0.3) * 20);
        
        const trace = {
            x: rsiDates,
            y: rsiValues,
            type: 'scatter',
            mode: 'lines',
            name: 'RSI',
            line: { color: 'purple' }
        };
        
        const layout = {
            title: 'RSI (14)',
            xaxis: { title: 'Date' },
            yaxis: { title: 'RSI', range: [0, 100] },
            margin: { t: 30, r: 20, b: 30, l: 40 },
            height: 150,
            shapes: [
                // Overbought line
                {
                    type: 'line',
                    x0: rsiDates[0],
                    y0: 70,
                    x1: rsiDates[rsiDates.length-1],
                    y1: 70,
                    line: { color: 'red', dash: 'dash' }
                },
                // Oversold line
                {
                    type: 'line',
                    x0: rsiDates[0],
                    y0: 30,
                    x1: rsiDates[rsiDates.length-1],
                    y1: 30,
                    line: { color: 'green', dash: 'dash' }
                }
            ]
        };
        
        Plotly.newPlot(rsiChart, [trace], layout);
        console.log('✅ RSI chart initialized');
    }
    
    // MACD Chart
    const macdChart = document.getElementById('macd-chart');
    if (macdChart) {
        const macdValues = Array.from({length: 14}, (_, i) => Math.sin(i * 0.2) * 2);
        const signalValues = Array.from({length: 14}, (_, i) => Math.sin(i * 0.2 + 0.1) * 1.8);
        
        const traces = [
            {
                x: rsiDates,
                y: macdValues,
                type: 'scatter',
                mode: 'lines',
                name: 'MACD',
                line: { color: 'blue' }
            },
            {
                x: rsiDates,
                y: signalValues,
                type: 'scatter',
                mode: 'lines',
                name: 'Signal',
                line: { color: 'red', dash: 'dash' }
            }
        ];
        
        const layout = {
            title: 'MACD',
            xaxis: { title: 'Date' },
            yaxis: { title: 'MACD' },
            margin: { t: 30, r: 20, b: 30, l: 40 },
            height: 150
        };
        
        Plotly.newPlot(macdChart, traces, layout);
        console.log('✅ MACD chart initialized');
    }
    
    // Performance Chart
    const perfChart = document.getElementById('performance-chart');
    if (perfChart) {
        const perfDates = Array.from({length: 20}, (_, i) => {
            const date = new Date();
            date.setMinutes(date.getMinutes() - (20-i) * 5);
            return date.toLocaleTimeString();
        });
        
        const processingTimes = Array.from({length: 20}, () => 30 + Math.random() * 40);
        
        const trace = {
            x: perfDates,
            y: processingTimes,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Processing Time',
            line: { color: 'orange' },
            marker: { size: 6 }
        };
        
        const layout = {
            title: 'System Performance',
            xaxis: { title: 'Time' },
            yaxis: { title: 'Processing Time (ms)' },
            margin: { t: 50, r: 50, b: 50, l: 50 }
        };
        
        Plotly.newPlot(perfChart, [trace], layout);
        console.log('✅ Performance chart initialized');
    }
}

// Fix 2: Update live market data
function updateLiveMarketData() {
    // This function will be called to update the market data table
    const tableBody = document.getElementById('live-data-body');
    if (tableBody) {
        // Sample current data (this would come from your API in production)
        const marketData = {
            'AAPL': { price: 210.31, change: -0.19, change_percent: -0.09, volume: 1992273 },
            'MSFT': { price: 509.25, change: 3.45, change_percent: 0.68, volume: 1601802 },
            'GOOGL': { price: 187.16, change: 3.91, change_percent: 2.13, volume: 1332798 }
        };
        
        tableBody.innerHTML = '';
        
        Object.entries(marketData).forEach(([symbol, data]) => {
            const row = document.createElement('tr');
            const changeClass = data.change >= 0 ? 'price-positive' : 'price-negative';
            const changeSign = data.change >= 0 ? '+' : '';
            
            row.innerHTML = `
                <td>${symbol}</td>
                <td>$${data.price.toFixed(2)}</td>
                <td class="${changeClass}">${changeSign}${data.change.toFixed(2)}</td>
                <td class="${changeClass}">${changeSign}${data.change_percent.toFixed(2)}%</td>
                <td>${data.volume.toLocaleString()}</td>
                <td>${new Date().toLocaleTimeString()}</td>
            `;
            
            tableBody.appendChild(row);
        });
        
        console.log('✅ Market data table updated');
    }
}

// Fix 3: Update performance metrics
function updatePerformanceMetrics() {
    // Update the performance metrics at the bottom
    const avgTimeElement = document.getElementById('avg-processing-time');
    const successRateElement = document.getElementById('success-rate');
    const throughputElement = document.getElementById('throughput');
    
    if (avgTimeElement) avgTimeElement.textContent = `${(45 + Math.random() * 20).toFixed(1)}ms`;
    if (successRateElement) successRateElement.textContent = `${(96 + Math.random() * 3).toFixed(1)}%`;
    if (throughputElement) throughputElement.textContent = `${(15 + Math.random() * 5).toFixed(1)} req/min`;
}

// Fix 4: Update risk metrics
function updateRiskMetrics() {
    const varElement = document.getElementById('var-95');
    const sharpeElement = document.getElementById('sharpe-ratio');
    const drawdownElement = document.getElementById('max-drawdown');
    const volatilityElement = document.getElementById('volatility');
    
    if (varElement) varElement.textContent = '-2.34%';
    if (sharpeElement) sharpeElement.textContent = '1.45';
    if (drawdownElement) drawdownElement.textContent = '-8.92%';
    if (volatilityElement) volatilityElement.textContent = '15.67%';
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded, initializing charts...');
    
    // Wait a moment for Plotly to load
    setTimeout(() => {
        initializeChartsWithData();
        updateLiveMarketData();
        updatePerformanceMetrics();
        updateRiskMetrics();
        
        // Set up periodic updates
        setInterval(updateLiveMarketData, 10000); // Update every 10 seconds
        setInterval(updatePerformanceMetrics, 15000); // Update every 15 seconds
    }, 1000);
});

// Fix 5: Manual refresh function
function refreshDashboard() {
    console.log('Manual refresh triggered');
    updateLiveMarketData();
    updatePerformanceMetrics();
    updateRiskMetrics();
    
    // Update timestamp
    document.getElementById('last-update').textContent = 
        `Last updated: ${new Date().toLocaleTimeString()}`;
}

// Export for global access
window.refreshDashboard = refreshDashboard;
