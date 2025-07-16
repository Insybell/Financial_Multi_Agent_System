# 🚀 Financial Multi-Agent System - Complete Testing Guide

## **Step 1: Start the Web Server**

Open your terminal and navigate to your project directory:

```bash
cd /path/to/your/Financial_Multi_Agent_System
```

Activate your virtual environment:

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

Start the server:

```bash
python main.py serve --port 8000
```

**Expected Output:**
```
Starting Financial Multi-Agent System API on localhost:8000
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
Initializing Financial Multi-Agent System...
2025-07-16 XX:XX:XX - core.base_agent - INFO - Initialized agent: DataCollectionAgent
2025-07-16 XX:XX:XX - core.base_agent - INFO - Initialized agent: BusinessIntelligenceAgent
[... more agent initialization logs ...]
Financial Multi-Agent System started successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000 (Press CTRL+C to quit)
```

**✅ Success Indicator:** You should see "Financial Multi-Agent System started successfully"

---

## **Step 2: Open a New Terminal for Testing**

**IMPORTANT:** Keep the first terminal running with the server!

Open a **NEW terminal window/tab** and activate your virtual environment:

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

---

## **Step 3: Test the Web Interface**

Open your web browser and visit:

```
http://localhost:8000
```

**Expected Result:** You should see a beautiful web interface showing:
- 🤖 Financial Multi-Agent System title
- ✅ System Status: Running
- 6 Agents Active | Real-time Analysis Ready
- API Endpoints documentation
- System Features overview

---

## **Step 4: Test System Health**

In your **second terminal**, run:

```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "system": "Financial Multi-Agent System",
  "agents": {
    "active": ["data_collection", "business_intelligence", "risk_assessment", "recommendation", "report_generation", "triage"],
    "failed": [],
    "total": 6
  },
  "message_queue_size": 0,
  "timestamp": "2025-07-16T18:XX:XX.XXXXXX",
  "performance_metrics": {
    "data_collection": {"agent_name": "DataCollectionAgent", "success_rate": 0.0, ...},
    "business_intelligence": {"agent_name": "BusinessIntelligenceAgent", "success_rate": 0.0, ...},
    ...
  }
}
```

**✅ Success Indicators:**
- `"status": "healthy"`
- `"failed": []` (empty array)
- All 6 agents in the "active" list

---

## **Step 5: Test Financial Analysis - Single Stock**

Analyze Apple (AAPL):

```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["AAPL"]'
```

**Expected Output:**
```json
{
  "workflow_id": "analysis_20250716_XXXXXX",
  "status": "completed",
  "symbols_requested": 1,
  "symbols_processed": 1,
  "symbols_failed": 0,
  "results": {
    "AAPL": {
      "financial_data": {
        "symbol": "AAPL",
        "data_quality": 1.0,
        "records_count": 250,
        "source": "yahoo_finance",
        "timestamp": "2025-07-16T18:XX:XX.XXXXXX"
      },
      "market_analysis": {
        "current_price": 209.11,
        "trend_strength": "bullish",
        "rsi": 67.83,
        "volume_trend": "stable",
        "data_quality": 1.0
      },
      "risk_assessment": {
        "risk_level": "medium",
        "volatility": 0.281,
        "var_95": -0.030,
        "sharpe_ratio": 0.701,
        "max_drawdown": -0.228,
        "confidence": 0.95,
        "risk_factors": [
          "Below-average trading volume",
          "Weak price-volume relationship",
          "Price below 200-day moving average (bearish long-term trend)",
          "Significant historical drawdown: -22.8%"
        ]
      },
      "processing_timestamp": "2025-07-16T18:XX:XX.XXXXXX"
    }
  },
  "completion_time": "2025-07-16T18:XX:XX.XXXXXX"
}
```

**✅ Success Indicators:**
- `"status": "completed"`
- `"symbols_processed": 1`
- `"symbols_failed": 0`
- Complete analysis with current price, trend, RSI, and risk metrics

---

## **Step 6: Test Multiple Stock Analysis**

Analyze multiple tech stocks:

```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["AAPL", "MSFT", "GOOGL"]'
```

**Expected Result:** Similar JSON structure but with 3 stocks analyzed

---

## **Step 7: Test Different Stock Sectors**

### **Technology Stocks:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]'
```

### **Financial Stocks:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["JPM", "BAC", "WFC", "GS"]'
```

### **Healthcare Stocks:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["JNJ", "PFE", "UNH", "ABBV"]'
```

### **Energy Stocks:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["XOM", "CVX", "COP"]'
```

---

## **Step 8: Test Additional Endpoints**

### **Get Market Summary:**
```bash
curl http://localhost:8000/market-summary
```

### **Get System Status:**
```bash
curl http://localhost:8000/status
```

### **Get Agent Information:**
```bash
curl http://localhost:8000/agents
```

### **Get Workflow History:**
```bash
curl http://localhost:8000/workflows
```

---

## **Step 9: Test Interactive API Documentation**

Open these URLs in your browser:

### **Swagger UI (Interactive Testing):**
```
http://localhost:8000/docs
```

### **ReDoc (Alternative Documentation):**
```
```
http://localhost:8000/redoc
```

**In Swagger UI, you can:**
1. Click on any endpoint (e.g., "POST /analyze")
2. Click "Try it out"
3. Enter stock symbols like `["AAPL", "MSFT"]`
4. Click "Execute"
5. See the live results

---

## **Step 10: Monitor Server Logs**

In your **first terminal** (where the server is running), you should see logs like:

```
INFO:     ::1:XXXXX - "GET /health HTTP/1.1" 200 OK
INFO:     ::1:XXXXX - "POST /analyze HTTP/1.1" 200 OK
2025-07-16 XX:XX:XX - __main__ - INFO - Starting analysis workflow analysis_XXXXXXXX for symbols: ['AAPL']
2025-07-16 XX:XX:XX - __main__ - INFO - Processing AAPL through analysis pipeline
2025-07-16 XX:XX:XX - __main__ - INFO - Successfully processed AAPL
2025-07-16 XX:XX:XX - __main__ - INFO - Analysis workflow analysis_XXXXXXXX completed
```

**✅ Success Indicators:**
- HTTP 200 OK responses
- "Successfully processed [SYMBOL]" messages
- "Analysis workflow completed" messages

---

## **Step 11: Performance Testing**

Test system performance with maximum allowed stocks:

```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN", "NFLX", "AMD", "INTC"]'
```

**Note:** Maximum 10 symbols allowed per request.

---

## **Step 12: Error Testing**

### **Test Empty Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '[]'
```
**Expected:** `{"detail":"No symbols provided"}`

### **Test Invalid Symbol:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["INVALID_SYMBOL"]'
```
**Expected:** Error in results for that symbol

### **Test Too Many Symbols:**
```bash
curl -X POST "http://localhost:8000/analyze" \
-H "Content-Type: application/json" \
-d '["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN", "NFLX", "AMD", "INTC", "CRM"]'
```
**Expected:** `{"detail":"Maximum 10 symbols allowed"}`

---

## **Step 13: Shutdown the System**

When you're done testing:

1. In the **first terminal** (server), press `Ctrl+C`
2. Wait for graceful shutdown:

```
^C
INFO:     Shutting down
INFO:     Waiting for application shutdown.
Financial Multi-Agent System stopped
INFO:     Application shutdown complete.
INFO:     Finished server process [XXXXX]
```

---

## **🎉 Congratulations!**

You've successfully tested your complete Financial Multi-Agent System! The system can:

✅ **Analyze individual stocks** with comprehensive metrics  
✅ **Process multiple stocks** simultaneously  
✅ **Provide real-time market data** from Yahoo Finance  
✅ **Calculate advanced risk metrics** (VaR, Sharpe ratio, drawdown)  
✅ **Identify market trends** and technical indicators  
✅ **Generate professional reports** with risk factors  
✅ **Handle errors gracefully** with proper HTTP responses  
✅ **Scale to analyze** up to 10 stocks per request  
✅ **Maintain system health** with 6 specialized AI agents  

Your Financial Multi-Agent System is now ready for production use! 🚀📈💼



 
