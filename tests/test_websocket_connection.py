# tests/test_websocket_connection.py
"""Test WebSocket connections for dashboard updates"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_connections():
    """Test various WebSocket endpoints"""
    
    websocket_urls = [
        "ws://localhost:8000/dashboard-ws/test",  # Your dashboard WebSocket
        "ws://localhost:8000/ws",
        "ws://localhost:8000/dev-ws",
        "ws://localhost:8001/stream",  # From your live data MCP
    ]
    
    print("🔌 Testing WebSocket Connections")
    print("=" * 50)
    
    for url in websocket_urls:
        try:
            print(f"\n🧪 Testing: {url}")
            
            async with websockets.connect(url, timeout=5) as websocket:
                print(f"✅ Connected to {url}")
                
                # Send a test message
                test_message = {
                    "type": "test",
                    "timestamp": datetime.now().isoformat(),
                    "data": "Hello from test client"
                }
                
                await websocket.send(json.dumps(test_message))
                print("📤 Sent test message")
                
                # Try to receive a response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    print(f"📥 Received: {response[:100]}...")
                except asyncio.TimeoutError:
                    print("⏰ No immediate response (this might be normal for dashboard WebSocket)")
                    
        except ConnectionRefusedError:
            print(f"❌ Connection refused to {url} - endpoint may not be available")
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ Invalid status code for {url}: {e}")
        except Exception as e:
            print(f"❌ Failed to connect to {url}: {str(e)[:50]}...")
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("✅ = WebSocket endpoint is available and responding")
    print("❌ = WebSocket endpoint needs to be added or is not running")
    print("⏰ = Connected but no immediate response (normal for some endpoints)")

if __name__ == "__main__":
    asyncio.run(test_websocket_connections())
