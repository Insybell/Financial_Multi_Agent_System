import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from mcp import ClientSession, StdioServerParameters
import subprocess
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import MCPMessage
from core.enums import MessageType, Priority

logger = logging.getLogger(__name__)


class FinancialMCPClient:
    """MCP Client for Financial Multi-Agent System"""
    
    def __init__(self, server_command: Optional[List[str]] = None):
        """
        Initialize MCP client
        
        Args:
            server_command: Command to start MCP server, defaults to local server
        """
        self.server_command = server_command or [
            sys.executable, 
            os.path.join(os.path.dirname(__file__), "mcp_server.py")
        ]
        
        self.session: Optional[ClientSession] = None
        self.connected = False
        self.client_id = str(uuid.uuid4())
        
        # Client state
        self.pending_requests = {}
        self.message_history = []
        self.last_activity = None
        
        logger.info(f"Financial MCP Client {self.client_id} initialized")
    
    async def connect(self) -> bool:
        """Connect to MCP server"""
        try:
            logger.info("Connecting to Financial MCP Server...")
            
            # Setup server parameters
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] if len(self.server_command) > 1 else []
            )
            
            # Create session
            self.session = ClientSession(server_params)
            
            # Initialize connection
            await self.session.initialize()
            
            self.connected = True
            self.last_activity = datetime.now()
            
            logger.info("Successfully connected to MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {str(e)}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.connected = False
            logger.info("Disconnected from MCP server")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def analyze_symbols(self, symbols: List[str], 
                            analysis_type: str = "comprehensive",
                            priority: str = "medium") -> Dict[str, Any]:
        """
        Request financial analysis for symbols
        
        Args:
            symbols: List of stock symbols to analyze
            analysis_type: Type of analysis to perform
            priority: Priority level for the request
        
        Returns:
            Analysis workflow information
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            logger.info(f"Requesting analysis for symbols: {symbols}")
            
            # Call MCP tool
            result = await self.session.call_tool(
                name="analyze_financial_data",
                arguments={
                    "symbols": symbols,
                    "analysis_type": analysis_type,
                    "priority": priority
                }
            )
            
            self.last_activity = datetime.now()
            
            # Parse result
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    response_data = json.loads(content.text)
                    
                    # Store request for tracking
                    if 'workflow_id' in response_data:
                        self.pending_requests[response_data['workflow_id']] = {
                            'symbols': symbols,
                            'analysis_type': analysis_type,
                            'priority': priority,
                            'request_time': datetime.now().isoformat(),
                            'status': 'pending'
                        }
                    
                    return response_data
                else:
                    return {"error": "Unexpected response format"}
            else:
                return {"error": "No response from server"}
                
        except Exception as e:
            logger.error(f"Error requesting analysis: {str(e)}")
            return {"error": str(e)}
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of analysis workflow
        
        Args:
            workflow_id: ID of workflow to check
        
        Returns:
            Workflow status information
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            result = await self.session.call_tool(
                name="get_workflow_status",
                arguments={"workflow_id": workflow_id}
            )
            
            self.last_activity = datetime.now()
            
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    response_data = json.loads(content.text)
                    
                    # Update local tracking
                    if workflow_id in self.pending_requests:
                        self.pending_requests[workflow_id]['last_status'] = response_data
                        self.pending_requests[workflow_id]['last_check'] = datetime.now().isoformat()
                    
                    return response_data
                else:
                    return {"error": "Unexpected response format"}
            else:
                return {"error": "No response from server"}
                
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {"error": str(e)}
    
    async def register_agent(self, agent_name: str, 
                           capabilities: List[str],
                           status: str = "active") -> Dict[str, Any]:
        """
        Register an agent with the MCP server
        
        Args:
            agent_name: Name of agent to register
            capabilities: List of agent capabilities
            status: Current agent status
        
        Returns:
            Registration confirmation
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            result = await self.session.call_tool(
                name="register_agent",
                arguments={
                    "agent_name": agent_name,
                    "capabilities": capabilities,
                    "status": status
                }
            )
            
            self.last_activity = datetime.now()
            
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"Error registering agent: {str(e)}")
            return {"error": str(e)}
    
    async def send_agent_message(self, source_agent: str, target_agent: str,
                               message_type: str, data: Dict[str, Any],
                               priority: str = "medium") -> Dict[str, Any]:
        """
        Send message between agents via MCP
        
        Args:
            source_agent: Sending agent name
            target_agent: Receiving agent name
            message_type: Type of message
            data: Message payload
            priority: Message priority
        
        Returns:
            Message delivery confirmation
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            result = await self.session.call_tool(
                name="send_agent_message",
                arguments={
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "message_type": message_type,
                    "data": data,
                    "priority": priority
                }
            )
            
            self.last_activity = datetime.now()
            
            # Store in message history
            message_record = {
                "source_agent": source_agent,
                "target_agent": target_agent,
                "message_type": message_type,
                "priority": priority,
                "timestamp": datetime.now().isoformat(),
                "client_id": self.client_id
            }
            self.message_history.append(message_record)
            
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"Error sending agent message: {str(e)}")
            return {"error": str(e)}
    
    async def get_server_metrics(self) -> Dict[str, Any]:
        """
        Get MCP server performance metrics
        
        Returns:
            Server metrics and statistics
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            result = await self.session.call_tool(
                name="get_server_metrics",
                arguments={}
            )
            
            self.last_activity = datetime.now()
            
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"Error getting server metrics: {str(e)}")
            return {"error": str(e)}
    
    async def get_agent_capabilities(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get agent capabilities from MCP server
        
        Args:
            agent_name: Optional specific agent name
        
        Returns:
            Agent capabilities information
        """
        try:
            if not self.connected:
                raise ConnectionError("Not connected to MCP server")
            
            arguments = {}
            if agent_name:
                arguments["agent_name"] = agent_name
            
            result = await self.session.call_tool(
                name="get_agent_capabilities",
                arguments=arguments
            )
            
            self.last_activity = datetime.now()
            
            if result and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return json.loads(content.text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {str(e)}")
            return {"error": str(e)}
    
    async def wait_for_workflow_completion(self, workflow_id: str, 
                                         timeout_seconds: int = 300,
                                         polling_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for workflow to complete with polling
        
        Args:
            workflow_id: ID of workflow to monitor
            timeout_seconds: Maximum time to wait
            polling_interval: Seconds between status checks
        
        Returns:
            Final workflow status
        """
        try:
            start_time = datetime.now()
            
            while True:
                # Check workflow status
                status = await self.get_workflow_status(workflow_id)
                
                if "error" in status:
                    return status
                
                # Check if completed
                if status.get("status") in ["completed", "failed", "timeout"]:
                    return status
                
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    return {
                        "workflow_id": workflow_id,
                        "status": "timeout",
                        "message": f"Workflow timed out after {timeout_seconds} seconds"
                    }
                
                # Wait before next check
                await asyncio.sleep(polling_interval)
                
        except Exception as e:
            logger.error(f"Error waiting for workflow completion: {str(e)}")
            return {"error": str(e), "workflow_id": workflow_id}
    
    async def analyze_symbols_and_wait(self, symbols: List[str],
                                     analysis_type: str = "comprehensive",
                                     priority: str = "medium",
                                     timeout_seconds: int = 300) -> Dict[str, Any]:
        """
        Analyze symbols and wait for completion
        
        Args:
            symbols: List of symbols to analyze
            analysis_type: Type of analysis
            priority: Priority level
            timeout_seconds: Maximum wait time
        
        Returns:
            Complete analysis results
        """
        try:
            # Start analysis
            workflow_response = await self.analyze_symbols(symbols, analysis_type, priority)
            
            if "error" in workflow_response:
                return workflow_response
            
            workflow_id = workflow_response.get("workflow_id")
            if not workflow_id:
                return {"error": "No workflow ID returned"}
            
            logger.info(f"Started analysis workflow {workflow_id}, waiting for completion...")
            
            # Wait for completion
            final_status = await self.wait_for_workflow_completion(
                workflow_id, timeout_seconds
            )
            
            return {
                "workflow_id": workflow_id,
                "symbols": symbols,
                "analysis_type": analysis_type,
                "initial_response": workflow_response,
                "final_status": final_status,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_symbols_and_wait: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform client health check
        
        Returns:
            Client health status
        """
        try:
            # Check connection
            if not self.connected:
                return {
                    "status": "disconnected",
                    "connected": False,
                    "last_activity": self.last_activity.isoformat() if self.last_activity else None
                }
            
            # Try to get server metrics to test connectivity
            metrics = await self.get_server_metrics()
            
            if "error" in metrics:
                return {
                    "status": "connection_error",
                    "connected": False,
                    "error": metrics["error"]
                }
            
            return {
                "status": "healthy",
                "connected": True,
                "client_id": self.client_id,
                "last_activity": self.last_activity.isoformat() if self.last_activity else None,
                "pending_requests": len(self.pending_requests),
                "message_history_count": len(self.message_history),
                "server_responsive": True
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    def get_pending_requests(self) -> Dict[str, Any]:
        """Get list of pending analysis requests"""
        return {
            "total_pending": len(self.pending_requests),
            "requests": self.pending_requests,
            "client_id": self.client_id
        }
    
    def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent message history"""
        return self.message_history[-limit:] if self.message_history else []
    
    async def cleanup(self):
        """Cleanup client resources"""
        try:
            # Clear pending requests
            self.pending_requests.clear()
            
            # Keep only recent message history
            if len(self.message_history) > 100:
                self.message_history = self.message_history[-100:]
            
            logger.info("Client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


class FinancialMCPClientManager:
    """Manager for multiple MCP client connections"""
    
    def __init__(self):
        self.clients: Dict[str, FinancialMCPClient] = {}
        self.default_client: Optional[FinancialMCPClient] = None
    
    async def create_client(self, client_id: Optional[str] = None,
                          server_command: Optional[List[str]] = None) -> FinancialMCPClient:
        """Create and connect a new MCP client"""
        
        if client_id is None:
            client_id = f"client_{len(self.clients) + 1}"
        
        if client_id in self.clients:
            raise ValueError(f"Client {client_id} already exists")
        
        client = FinancialMCPClient(server_command)
        
        # Connect to server
        connected = await client.connect()
        if not connected:
            raise ConnectionError(f"Failed to connect client {client_id}")
        
        self.clients[client_id] = client
        
        # Set as default if first client
        if self.default_client is None:
            self.default_client = client
        
        logger.info(f"Created and connected MCP client: {client_id}")
        return client
    
    async def get_client(self, client_id: Optional[str] = None) -> FinancialMCPClient:
        """Get client by ID or default client"""
        
        if client_id is None:
            if self.default_client is None:
                # Create default client
                return await self.create_client("default")
            return self.default_client
        
        if client_id not in self.clients:
            raise ValueError(f"Client {client_id} not found")
        
        return self.clients[client_id]
    
    async def disconnect_client(self, client_id: str):
        """Disconnect and remove a client"""
        
        if client_id not in self.clients:
            return
        
        client = self.clients[client_id]
        await client.disconnect()
        await client.cleanup()
        
        del self.clients[client_id]
        
        # Update default client
        if self.default_client == client:
            self.default_client = list(self.clients.values())[0] if self.clients else None
        
        logger.info(f"Disconnected MCP client: {client_id}")
    
    async def disconnect_all_clients(self):
        """Disconnect all clients"""
        
        for client_id in list(self.clients.keys()):
            await self.disconnect_client(client_id)
        
        self.default_client = None
        logger.info("Disconnected all MCP clients")
    
    def get_client_status(self) -> Dict[str, Any]:
        """Get status of all managed clients"""
        
        return {
            "total_clients": len(self.clients),
            "client_ids": list(self.clients.keys()),
            "default_client": self.default_client.client_id if self.default_client else None,
            "timestamp": datetime.now().isoformat()
        }


# Global client manager instance
client_manager = FinancialMCPClientManager()


async def get_default_client() -> FinancialMCPClient:
    """Get or create default MCP client"""
    return await client_manager.get_client()


async def example_usage():
    """Example usage of MCP client"""
    try:
        # Create client
        client = await client_manager.create_client("example_client")
        
        # Analyze symbols
        result = await client.analyze_symbols(
            symbols=["AAPL", "MSFT"],
            analysis_type="comprehensive",
            priority="high"
        )
        
        print(f"Analysis started: {result}")
        
        if "workflow_id" in result:
            # Wait for completion
            final_result = await client.wait_for_workflow_completion(
                result["workflow_id"],
                timeout_seconds=180
            )
            print(f"Analysis completed: {final_result}")
        
        # Get server metrics
        metrics = await client.get_server_metrics()
        print(f"Server metrics: {metrics}")
        
        # Health check
        health = await client.health_check()
        print(f"Client health: {health}")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")
    
    finally:
        # Cleanup
        await client_manager.disconnect_all_clients()


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
