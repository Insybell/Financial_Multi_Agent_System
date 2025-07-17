#!/bin/bash

# start_mcp_dev.sh - Enhanced development startup script
echo "🚀 Starting Financial MCP Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check Python environment
print_status "Checking Python environment..."
if ! command -v python &> /dev/null; then
    print_error "Python not found. Please install Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Python version: $PYTHON_VERSION"

# Check required packages
print_status "Checking required packages..."
REQUIRED_PACKAGES="fastapi uvicorn pandas numpy yfinance plotly mcp"

for package in $REQUIRED_PACKAGES; do
    if ! python -c "import $package" 2>/dev/null; then
        print_warning "Package $package not found. Installing..."
        pip install $package
    fi
done

# Create necessary directories
print_status "Creating development directories..."
mkdir -p logs
mkdir -p .cursor
mkdir -p temp_data
mkdir -p evaluation_results
mkdir -p evaluation_charts

# Setup environment variables
print_status "Setting up environment variables..."
if [ -f ".env" ]; then
    source .env
    print_status "Loaded environment from .env file"
else
    print_warning "No .env file found. Creating template..."
    cat > .env << 'EOF'
# Financial Multi-Agent System Environment Variables
OPENAI_API_KEY=your_openai_api_key_here
FINANCIAL_DEV_MODE=true
LOG_LEVEL=INFO
MCP_SERVER_PORT=8001
WEB_SERVER_PORT=8000

# Development Settings
CACHE_TTL_HOURS=1
MAX_CACHE_SIZE=100
DEBUG_MODE=true

# Database (if using)
DATABASE_URL=sqlite:///financial_system.db

# External APIs (optional)
ALPHA_VANTAGE_API_KEY=your_key_here
FRED_API_KEY=your_key_here
EOF
    print_warning "Please edit .env file with your API keys"
fi

# Ensure Cursor MCP configuration exists
print_status "Setting up Cursor IDE MCP configuration..."
if [ ! -f ".cursor/mcp_config.json" ]; then
    cp cursor_ide_config.json .cursor/mcp_config.json 2>/dev/null || {
        print_warning "Cursor config not found, will use default settings"
    }
fi

# Start MCP server in development mode
print_status "Starting Financial MCP Server..."
python mcp/dev_server.py &
MCP_PID=$!
echo "MCP Server PID: $MCP_PID"

# Wait for MCP server to initialize
sleep 3

# Check if MCP server is running
if ps -p $MCP_PID > /dev/null; then
    print_status "✅ MCP Server running successfully"
else
    print_error "❌ MCP Server failed to start"
    exit 1
fi

# Start main financial system
print_status "Starting Financial Multi-Agent System..."
python main.py serve --port 8000 --host localhost &
MAIN_PID=$!
echo "Main System PID: $MAIN_PID"

# Wait for main system to initialize
sleep 5

# Health check
print_status "Performing system health check..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null || echo "failed")

if [[ $HEALTH_CHECK == *"running"* ]]; then
    print_status "✅ Financial System running successfully"
else
    print_warning "⚠️  System may not be fully initialized yet"
fi

# Display system information
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}🤖 Financial MCP Development Environment${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
print_status "System Status:"
echo "  📊 Main System:        http://localhost:8000"
echo "  🔧 Development Dashboard: http://localhost:8000/dev-dashboard"
echo "  📖 API Documentation:  http://localhost:8000/docs"
echo "  🏥 Health Check:       http://localhost:8000/health"
echo ""
print_status "MCP Integration:"
echo "  🔌 MCP Server PID:     $MCP_PID"
echo "  🎯 Main System PID:    $MAIN_PID"
echo "  📁 Logs Directory:     ./logs/"
echo ""
print_status "Development Features Enabled:"
echo "  ✨ Intelligent Code Completion"
echo "  🔍 Real-time Financial Validation"
echo "  📈 Live Market Data Integration" 
echo "  📊 Performance Monitoring Dashboard"
echo "  🤖 Agent Communication Monitoring"
echo ""
print_status "Cursor IDE Integration:"
echo "  🎨 Enhanced autocompletion for financial code"
echo "  ⚡ Real-time validation of risk calculations"
echo "  📡 Live data feeds for development testing"
echo "  🔧 Development dashboard at /dev-dashboard"
echo ""

# Create cleanup function
cleanup() {
    print_status "Shutting down development environment..."
    
    # Stop main system
    if ps -p $MAIN_PID > /dev/null; then
        print_status "Stopping Main System (PID: $MAIN_PID)..."
        kill $MAIN_PID
        wait $MAIN_PID 2>/dev/null
    fi
    
    # Stop MCP server
    if ps -p $MCP_PID > /dev/null; then
        print_status "Stopping MCP Server (PID: $MCP_PID)..."
        kill $MCP_PID
        wait $MCP_PID 2>/dev/null
    fi
    
    print_status "✅ Development environment shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Keep script running and show live status
print_status "Development environment is running. Press Ctrl+C to stop."
print_status "Monitor system status at: http://localhost:8000/health"
echo ""

# Live monitoring loop
while true; do
    sleep 30
    
    # Check if processes are still running
    if ! ps -p $MCP_PID > /dev/null; then
        print_error "MCP Server stopped unexpectedly!"
        break
    fi
    
    if ! ps -p $MAIN_PID > /dev/null; then
        print_error "Main System stopped unexpectedly!"
        break
    fi
    
    # Optional: Display brief status
    CURRENT_TIME=$(date '+%H:%M:%S')
    echo -e "${BLUE}[$CURRENT_TIME]${NC} System running - MCP: $MCP_PID | Main: $MAIN_PID"
done

# If we get here, something went wrong
print_error "One or more processes stopped unexpectedly!"
cleanup
