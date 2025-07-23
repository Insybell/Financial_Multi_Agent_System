# mcp/live_data_mcp.py
"""Real-time financial data MCP integration"""

import asyncio
import json
import logging
import websockets
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np
from threading import Timer
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


@dataclass
class LiveDataPoint:
    """Single live data point"""
    symbol: str
    timestamp: str
    price: float
    volume: int
    change: float
    change_percent: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None


@dataclass
class LiveDataStream:
    """Live data stream configuration"""
    stream_id: str
    symbols: List[str]
    update_frequency: int  # milliseconds
    data_types: List[str]
    subscribers: Set[str]
    started_at: str
    last_update: Optional[str] = None
    is_active: bool = True


class LiveFinancialDataMCP:
    """Real-time financial data MCP integration"""
    
    def __init__(self):
        self.active_streams: Dict[str, LiveDataStream] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # stream_id -> subscriber_ids
        self.data_cache: Dict[str, LiveDataPoint] = {}
        self.update_tasks: Dict[str, asyncio.Task] = {}
        self.websocket_server = None
        self.server_port = 8001
        
        # Risk monitoring configuration
        self.risk_thresholds = {
            "max_daily_change": 0.1,  # 10%
            "volume_spike_threshold": 3.0,  # 3x average
            "volatility_threshold": 0.05  # 5% in short period
        }
        
        self.risk_alerts: List[Dict[str, Any]] = []
        
    async def stream_market_data(self, symbols: List[str], 
                               update_frequency: int = 5000) -> Dict[str, Any]:
        """
        Stream real-time market data for development
        
        Args:
            symbols: List of symbols to stream
            update_frequency: Update frequency in milliseconds
            
        Returns:
            Stream configuration and access details
        """
        try:
            stream_id = f"stream_{datetime.now().strftime('%H%M%S')}_{len(self.active_streams)}"
            
            # Create stream configuration
            stream = LiveDataStream(
                stream_id=stream_id,
                symbols=symbols,
                update_frequency=update_frequency,
                data_types=["price", "volume", "change"],
                subscribers=set(),
                started_at=datetime.now().isoformat()
            )
            
            self.active_streams[stream_id] = stream
            self.subscribers[stream_id] = set()
            
            # Start data collection task
            task = asyncio.create_task(self._collect_live_data(stream))
            self.update_tasks[stream_id] = task
            
            # Start WebSocket server if not running
            if not self.websocket_server:
                await self._start_websocket_server()
            
            logger.info(f"Started live data stream {stream_id} for symbols: {symbols}")
            
            return {
                "stream_id": stream_id,
                "symbols": symbols,
                "update_frequency": update_frequency,
                "websocket_url": f"ws://localhost:{self.server_port}/stream/{stream_id}",
                "rest_endpoint": f"http://localhost:{self.server_port}/data/{stream_id}",
                "status": "active",
                "started_at": stream.started_at
            }
            
        except Exception as e:
            logger.error(f"Error starting market data stream: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def live_risk_monitoring(self, portfolio: Dict[str, float], 
                                 risk_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Monitor portfolio risk in real-time
        
        Args:
            portfolio: Dictionary of symbol -> weight
            risk_thresholds: Custom risk thresholds
            
        Returns:
            Risk monitoring configuration
        """
        try:
            if risk_thresholds:
                self.risk_thresholds.update(risk_thresholds)
            
            symbols = list(portfolio.keys())
            monitor_id = f"risk_monitor_{datetime.now().strftime('%H%M%S')}"
            
            # Start monitoring stream if needed
            stream_result = await self.stream_market_data(symbols, update_frequency=2000)
            
            if "error" in stream_result:
                return stream_result
            
            # Setup risk monitoring task
            risk_task = asyncio.create_task(
                self._monitor_portfolio_risk(monitor_id, portfolio, stream_result["stream_id"])
            )
            
            self.update_tasks[f"risk_{monitor_id}"] = risk_task
            
            return {
                "monitor_id": monitor_id,
                "portfolio": portfolio,
                "risk_thresholds": self.risk_thresholds,
                "stream_id": stream_result["stream_id"],
                "alerts_endpoint": f"http://localhost:{self.server_port}/risk-alerts/{monitor_id}",
                "status": "monitoring"
            }
            
        except Exception as e:
            logger.error(f"Error setting up risk monitoring: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    async def _collect_live_data(self, stream: LiveDataStream):
        """Collect live data for a stream"""
        while stream.is_active:
            try:
                # Collect data for all symbols in the stream
                for symbol in stream.symbols:
                    data_point = await self._fetch_live_data_point(symbol)
                    if data_point:
                        self.data_cache[f"{stream.stream_id}_{symbol}"] = data_point
                        
                        # Broadcast to subscribers
                        await self._broadcast_data_update(stream.stream_id, symbol, data_point)
                
                stream.last_update = datetime.now().isoformat()
                
                # Wait for next update
                await asyncio.sleep(stream.update_frequency / 1000.0)
                
            except Exception as e:
                logger.error(f"Error collecting live data for stream {stream.stream_id}: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _fetch_live_data_point(self, symbol: str) -> Optional[LiveDataPoint]:
        """Fetch live data point for a symbol"""
        try:
            # Use yfinance for live data (in production, use proper real-time API)
            ticker = yf.Ticker(symbol)
            
            # Get current data
            hist = ticker.history(period="2d", interval="1m")
            if hist.empty:
                return None
            
            current = hist.iloc[-1]
            previous = hist.iloc[-2] if len(hist) > 1 else current
            
            change = current['Close'] - previous['Close']
            change_percent = (change / previous['Close']) * 100 if previous['Close'] != 0 else 0
            
            # Get additional real-time info if available
            info = ticker.info
            
            return LiveDataPoint(
                symbol=symbol,
                timestamp=datetime.now().isoformat(),
                price=float(current['Close']),
                volume=int(current['Volume']),
                change=float(change),
                change_percent=float(change_percent),
                bid=info.get('bid'),
                ask=info.get('ask'),
                high_24h=float(current['High']),
                low_24h=float(current['Low'])
            )
            
        except Exception as e:
            logger.error(f"Error fetching live data for {symbol}: {str(e)}")
            return None
    
    async def _broadcast_data_update(self, stream_id: str, symbol: str, data_point: LiveDataPoint):
        """Broadcast data update to all subscribers"""
        try:
            message = {
                "type": "data_update",
                "stream_id": stream_id,
                "symbol": symbol,
                "data": asdict(data_point),
                "timestamp": datetime.now().isoformat()
            }
            
            # Here you would broadcast to WebSocket clients
            # For now, we'll just log the update
            logger.debug(f"Broadcasting update for {symbol}: ${data_point.price:.2f} ({data_point.change_percent:+.2f}%)")
            
        except Exception as e:
            logger.error(f"Error broadcasting data update: {str(e)}")
    
    async def _monitor_portfolio_risk(self, monitor_id: str, portfolio: Dict[str, float], stream_id: str):
        """Monitor portfolio risk in real-time"""
        while stream_id in self.active_streams:
            try:
                # Calculate portfolio-level risk metrics
                portfolio_value = 0.0
                portfolio_change = 0.0
                risk_alerts = []
                
                for symbol, weight in portfolio.items():
                    cache_key = f"{stream_id}_{symbol}"
                    if cache_key in self.data_cache:
                        data_point = self.data_cache[cache_key]
                        
                        # Calculate weighted contribution
                        weighted_change = data_point.change_percent * weight
                        portfolio_change += weighted_change
                        
                        # Check individual symbol risk
                        if abs(data_point.change_percent) > self.risk_thresholds["max_daily_change"] * 100:
                            risk_alerts.append({
                                "type": "high_volatility",
                                "symbol": symbol,
                                "current_change": data_point.change_percent,
                                "threshold": self.risk_thresholds["max_daily_change"] * 100,
                                "severity": "high" if abs(data_point.change_percent) > 15 else "medium"
                            })
                        
                        # Check volume spikes
                        # Note: This is simplified - in production, you'd compare against historical average
                        if hasattr(data_point, 'volume_ratio') and data_point.volume > 1000000:
                            # Placeholder for volume spike detection
                            pass
                
                # Check portfolio-level risk
                if abs(portfolio_change) > self.risk_thresholds["max_daily_change"] * 100:
                    risk_alerts.append({
                        "type": "portfolio_risk",
                        "portfolio_change": portfolio_change,
                        "threshold": self.risk_thresholds["max_daily_change"] * 100,
                        "severity": "critical" if abs(portfolio_change) > 20 else "high"
                    })
                
                # Store alerts
                if risk_alerts:
                    for alert in risk_alerts:
                        alert["monitor_id"] = monitor_id
                        alert["timestamp"] = datetime.now().isoformat()
                        self.risk_alerts.append(alert)
                    
                    logger.warning(f"Risk alerts generated for monitor {monitor_id}: {len(risk_alerts)} alerts")
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in risk monitoring for {monitor_id}: {str(e)}")
                await asyncio.sleep(30)
    
    async def _start_websocket_server(self):
        """Start WebSocket server for real-time data streaming"""
        try:
            async def handle_client(websocket, path):
                try:
                    # Parse path to get stream_id
                    if path.startswith("/stream/"):
                        stream_id = path.split("/")[-1]
                        if stream_id in self.active_streams:
                            self.subscribers[stream_id].add(websocket)
                            logger.info(f"Client connected to stream {stream_id}")
                            
                            try:
                                # Send initial data
                                for symbol in self.active_streams[stream_id].symbols:
                                    cache_key = f"{stream_id}_{symbol}"
                                    if cache_key in self.data_cache:
                                        data_point = self.data_cache[cache_key]
                                        message = {
                                            "type": "initial_data",
                                            "symbol": symbol,
                                            "data": asdict(data_point)
                                        }
                                        await websocket.send(json.dumps(message))
                                
                                # Keep connection alive and send updates
                                await websocket.wait_closed()
                                
                            finally:
                                self.subscribers[stream_id].discard(websocket)
                        else:
                            await websocket.send(json.dumps({"error": "Stream not found"}))
                    else:
                        await websocket.send(json.dumps({"error": "Invalid path"}))
                        
                except Exception as e:
                    logger.error(f"WebSocket client error: {str(e)}")
            
            # Start WebSocket server
            self.websocket_server = await websockets.serve(
                handle_client,
                "localhost",
                self.server_port
            )
            
            logger.info(f"WebSocket server started on port {self.server_port}")
            
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {str(e)}")
    
    async def get_stream_data(self, stream_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get current data for a stream"""
        try:
            if stream_id not in self.active_streams:
                return {"error": "Stream not found"}
            
            stream = self.active_streams[stream_id]
            data = {}
            
            symbols = [symbol] if symbol else stream.symbols
            
            for sym in symbols:
                cache_key = f"{stream_id}_{sym}"
                if cache_key in self.data_cache:
                    data[sym] = asdict(self.data_cache[cache_key])
            
            return {
                "stream_id": stream_id,
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "stream_info": {
                    "symbols": stream.symbols,
                    "update_frequency": stream.update_frequency,
                    "started_at": stream.started_at,
                    "last_update": stream.last_update,
                    "is_active": stream.is_active
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting stream data: {str(e)}")
            return {"error": str(e)}
    
    async def stop_stream(self, stream_id: str) -> Dict[str, Any]:
        """Stop a live data stream"""
        try:
            if stream_id not in self.active_streams:
                return {"error": "Stream not found"}
            
            # Mark stream as inactive
            self.active_streams[stream_id].is_active = False
            
            # Cancel update task
            if stream_id in self.update_tasks:
                self.update_tasks[stream_id].cancel()
                del self.update_tasks[stream_id]
            
            # Remove subscribers
            if stream_id in self.subscribers:
                del self.subscribers[stream_id]
            
            # Clean up data cache
            cache_keys_to_remove = [key for key in self.data_cache.keys() if key.startswith(f"{stream_id}_")]
            for key in cache_keys_to_remove:
                del self.data_cache[key]
            
            # Remove stream
            del self.active_streams[stream_id]
            
            logger.info(f"Stopped live data stream {stream_id}")
            
            return {
                "stream_id": stream_id,
                "status": "stopped",
                "stopped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error stopping stream: {str(e)}")
            return {"error": str(e)}
    
    async def get_risk_alerts(self, monitor_id: Optional[str] = None) -> Dict[str, Any]:
        """Get risk monitoring alerts"""
        try:
            if monitor_id:
                alerts = [alert for alert in self.risk_alerts if alert.get("monitor_id") == monitor_id]
            else:
                alerts = self.risk_alerts
            
            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return {
                "alerts": alerts[:50],  # Last 50 alerts
                "total_alerts": len(alerts),
                "monitor_id": monitor_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting risk alerts: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup all streams and resources"""
        try:
            # Stop all streams
            for stream_id in list(self.active_streams.keys()):
                await self.stop_stream(stream_id)
            
            # Cancel all tasks
            for task in self.update_tasks.values():
                if not task.done():
                    task.cancel()
            
            self.update_tasks.clear()
            
            # Close WebSocket server
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            # Clear all data
            self.data_cache.clear()
            self.subscribers.clear()
            self.risk_alerts.clear()
            
            logger.info("Live data MCP cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of live data system"""
        return {
            "active_streams": len(self.active_streams),
            "total_subscribers": sum(len(subs) for subs in self.subscribers.values()),
            "cached_data_points": len(self.data_cache),
            "running_tasks": len(self.update_tasks),
            "risk_alerts": len(self.risk_alerts),
            "websocket_server_running": self.websocket_server is not None,
            "server_port": self.server_port,
            "streams": {
                stream_id: {
                    "symbols": stream.symbols,
                    "update_frequency": stream.update_frequency,
                    "subscribers": len(self.subscribers.get(stream_id, set())),
                    "is_active": stream.is_active,
                    "started_at": stream.started_at,
                    "last_update": stream.last_update
                }
                for stream_id, stream in self.active_streams.items()
            }
        }


# Global instance
live_data_mcp = LiveFinancialDataMCP()


# Convenience functions
async def start_live_stream(symbols: List[str], update_frequency: int = 5000) -> Dict[str, Any]:
    """Start a live data stream"""
    return await live_data_mcp.stream_market_data(symbols, update_frequency)


async def start_risk_monitoring(portfolio: Dict[str, float], 
                              thresholds: Dict[str, float] = None) -> Dict[str, Any]:
    """Start portfolio risk monitoring"""
    return await live_data_mcp.live_risk_monitoring(portfolio, thresholds)


async def get_live_data(stream_id: str, symbol: Optional[str] = None) -> Dict[str, Any]:
    """Get current live data"""
    return await live_data_mcp.get_stream_data(stream_id, symbol)


async def stop_live_stream(stream_id: str) -> Dict[str, Any]:
    """Stop a live data stream"""
    return await live_data_mcp.stop_stream(stream_id)


if __name__ == "__main__":
    # Test the live data system
    async def test_live_data():
        try:
            # Start a test stream
            symbols = ["AAPL", "MSFT", "GOOGL"]
            stream_result = await live_data_mcp.stream_market_data(symbols, 3000)
            print("Stream started:", stream_result)
            
            # Wait for some data
            await asyncio.sleep(10)
            
            # Get current data
            if "stream_id" in stream_result:
                data = await live_data_mcp.get_stream_data(stream_result["stream_id"])
                print("Current data:", data)
            
            # Test risk monitoring
            portfolio = {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.3}
            risk_result = await live_data_mcp.live_risk_monitoring(portfolio)
            print("Risk monitoring:", risk_result)
            
            # Wait and check alerts
            await asyncio.sleep(15)
            alerts = await live_data_mcp.get_risk_alerts()
            print("Risk alerts:", alerts)
            
            # Get system status
            status = live_data_mcp.get_status()
            print("System status:", status)
            
        except Exception as e:
            print(f"Test error: {e}")
        finally:
            await live_data_mcp.cleanup()
    
    # Run test
    asyncio.run(test_live_data())
