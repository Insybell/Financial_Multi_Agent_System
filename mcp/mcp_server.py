# mcp/mcp_server.py
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

# Fix the MCP imports
try:
    from mcp.server import Server
except ImportError:
    try:
        from mcp import ServerSession as Server
    except ImportError:
        # Fallback - create a mock Server for development
        class Server:
            def __init__(self, name):
                self.name = name
            def tool(self):
                def decorator(func):
                    return func
                return decorator

try:
    from mcp import types
except ImportError:
    # Create basic types if not available
    class types:
        Tool = dict
        TextContent = dict
        Resource = dict

try:
    from mcp.server import stdio
except ImportError:
    # Mock stdio for development
    class stdio:
        @staticmethod
        async def stdio_server():
            pass

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import MCPMessage, AgentPerformance
from core.enums import MessageType, Priority, AgentStatus

logger = logging.getLogger(__name__)


class FinancialMCPServer:
    """MCP Server for Financial Multi-Agent System"""
    
    def __init__(self, server_name: str = "financial-multi-agent-system"):
        """Initialize MCP server"""
        self.server = Server(server_name)
        self.server_name = server_name
        
        # Agent registry
        self.registered_agents = {}
        self.agent_capabilities = {}
        self.message_history = []
        self.active_workflows = {}
        
        # Performance tracking
        self.server_metrics = {
            "messages_processed": 0,
            "workflows_completed": 0,
            "errors_encountered": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        # Setup MCP tools
        self._setup_tools()
        self._setup_resources()
        
        logger.info(f"Financial MCP Server '{server_name}' initialized")
    
    def _setup_tools(self):
        """Setup MCP tools for financial operations"""
        
        @self.server.tool()
        async def analyze_financial_data(
            symbols: List[str],
            analysis_type: str = "comprehensive",
            priority: str = "medium"
        ) -> str:
            """
            Analyze financial data for given symbols
            
            Args:
                symbols: List of stock symbols to analyze
                analysis_type: Type of analysis (comprehensive, quick, risk_only)
                priority: Priority level (low, medium, high, critical)
            
            Returns:
                JSON string with analysis workflow ID and status
            """
            try:
                workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
                
                # Create workflow tracking
                workflow = {
                    "workflow_id": workflow_id,
                    "symbols": symbols,
                    "analysis_type": analysis_type,
                    "priority": priority,
                    "status": "initiated",
                    "start_time": datetime.now().isoformat(),
                    "agents_involved": [],
                    "current_step": "data_collection"
                }
                
                self.active_workflows[workflow_id] = workflow
                
                # Route to Triage Agent for processing
                triage_message = {
                    "action": "submit_request",
                    "request": {
                        "symbols": symbols,
                        "type": analysis_type,
                        "priority": priority,
                        "metadata": {
                            "workflow_id": workflow_id,
                            "request_time": datetime.now().isoformat()
                        }
                    }
                }
                
                # Simulate routing to triage agent
                await self._route_to_agent("TriageAgent", triage_message, workflow_id)
                
                self.server_metrics["workflows_completed"] += 1
                
                return json.dumps({
                    "workflow_id": workflow_id,
                    "status": "initiated",
                    "symbols": symbols,
                    "estimated_completion_time": "3-5 minutes",
                    "tracking_url": f"/workflow/{workflow_id}"
                })
                
            except Exception as e:
                self.server_metrics["errors_encountered"] += 1
                logger.error(f"Error in analyze_financial_data: {str(e)}")
                return json.dumps({"error": str(e), "status": "failed"})
        
        @self.server.tool()
        async def get_workflow_status(workflow_id: str) -> str:
            """
            Get status of a financial analysis workflow
            
            Args:
                workflow_id: ID of the workflow to check
            
            Returns:
                JSON string with workflow status and progress
            """
            try:
                if workflow_id in self.active_workflows:
                    workflow = self.active_workflows[workflow_id]
                    
                    # Calculate progress
                    total_steps = 5  # Data collection, BI analysis, Risk assessment, Recommendations, Report
                    current_step_map = {
                        "data_collection": 1,
                        "business_intelligence": 2,
                        "risk_assessment": 3,
                        "recommendations": 4,
                        "report_generation": 5,
                        "completed": 5
                    }
                    
                    progress = current_step_map.get(workflow["current_step"], 0) / total_steps * 100
                    
                    return json.dumps({
                        "workflow_id": workflow_id,
                        "status": workflow["status"],
                        "progress": f"{progress:.0f}%",
                        "current_step": workflow["current_step"],
                        "symbols": workflow["symbols"],
                        "start_time": workflow["start_time"],
                        "agents_involved": workflow["agents_involved"]
                    })
                else:
                    # Check completed workflows (simplified - would use database in production)
                    return json.dumps({
                        "workflow_id": workflow_id,
                        "status": "not_found",
                        "message": "Workflow not found or has been archived"
                    })
                    
            except Exception as e:
                logger.error(f"Error getting workflow status: {str(e)}")
                return json.dumps({"error": str(e), "workflow_id": workflow_id})
        
        @self.server.tool()
        async def register_agent(
            agent_name: str,
            capabilities: List[str],
            status: str = "active"
        ) -> str:
            """
            Register a financial agent with the MCP server
            
            Args:
                agent_name: Name of the agent to register
                capabilities: List of agent capabilities
                status: Current status of the agent
            
            Returns:
                JSON string with registration confirmation
            """
            try:
                agent_info = {
                    "agent_name": agent_name,
                    "capabilities": capabilities,
                    "status": status,
                    "registered_at": datetime.now().isoformat(),
                    "message_count": 0,
                    "last_activity": datetime.now().isoformat()
                }
                
                self.registered_agents[agent_name] = agent_info
                self.agent_capabilities[agent_name] = capabilities
                
                logger.info(f"Agent {agent_name} registered with capabilities: {capabilities}")
                
                return json.dumps({
                    "status": "registered",
                    "agent_name": agent_name,
                    "capabilities_count": len(capabilities),
                    "registration_time": agent_info["registered_at"]
                })
                
            except Exception as e:
                logger.error(f"Error registering agent {agent_name}: {str(e)}")
                return json.dumps({"error": str(e), "agent_name": agent_name})
        
        @self.server.tool()
        async def send_agent_message(
            source_agent: str,
            target_agent: str,
            message_type: str,
            data: Dict[str, Any],
            priority: str = "medium"
        ) -> str:
            """
            Send message between agents via MCP
            
            Args:
                source_agent: Name of sending agent
                target_agent: Name of receiving agent
                message_type: Type of message
                data: Message data payload
                priority: Message priority level
            
            Returns:
                JSON string with message delivery confirmation
            """
            try:
                message_id = str(uuid.uuid4())
                
                message = {
                    "message_id": message_id,
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "message_type": message_type,
                    "data": data,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store message in history
                self.message_history.append(message)
                
                # Update agent activity
                if source_agent in self.registered_agents:
                    self.registered_agents[source_agent]["message_count"] += 1
                    self.registered_agents[source_agent]["last_activity"] = datetime.now().isoformat()
                
                self.server_metrics["messages_processed"] += 1
                
                # Route message to target agent
                await self._route_message(message)
                
                return json.dumps({
                    "status": "delivered",
                    "message_id": message_id,
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "delivery_time": datetime.now().isoformat()
                })
                
            except Exception as e:
                self.server_metrics["errors_encountered"] += 1
                logger.error(f"Error sending message: {str(e)}")
                return json.dumps({"error": str(e), "status": "failed"})
        
        @self.server.tool()
        async def get_server_metrics() -> str:
            """
            Get MCP server performance metrics
            
            Returns:
                JSON string with server metrics and statistics
            """
            try:
                # Calculate uptime
                uptime_start = datetime.fromisoformat(self.server_metrics["uptime_start"])
                uptime_seconds = (datetime.now() - uptime_start).total_seconds()
                
                # Agent statistics
                active_agents = len([a for a in self.registered_agents.values() if a["status"] == "active"])
                total_capabilities = sum(len(caps) for caps in self.agent_capabilities.values())
                
                # Message statistics
                recent_messages = len([m for m in self.message_history[-100:]])  # Last 100 messages
                
                metrics = {
                    "server_info": {
                        "server_name": self.server_name,
                        "uptime_seconds": uptime_seconds,
                        "uptime_hours": uptime_seconds / 3600
                    },
                    "processing_metrics": self.server_metrics,
                    "agent_metrics": {
                        "total_registered": len(self.registered_agents),
                        "active_agents": active_agents,
                        "total_capabilities": total_capabilities
                    },
                    "workflow_metrics": {
                        "active_workflows": len(self.active_workflows),
                        "total_completed": self.server_metrics["workflows_completed"]
                    },
                    "message_metrics": {
                        "total_processed": self.server_metrics["messages_processed"],
                        "recent_activity": recent_messages,
                        "error_rate": self.server_metrics["errors_encountered"] / max(self.server_metrics["messages_processed"], 1)
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                return json.dumps(metrics, indent=2)
                
            except Exception as e:
                logger.error(f"Error getting server metrics: {str(e)}")
                return json.dumps({"error": str(e)})
        
        @self.server.tool()
        async def get_agent_capabilities(agent_name: Optional[str] = None) -> str:
            """
            Get capabilities of specific agent or all agents
            
            Args:
                agent_name: Optional specific agent name
            
            Returns:
                JSON string with agent capabilities
            """
            try:
                if agent_name:
                    if agent_name in self.agent_capabilities:
                        return json.dumps({
                            "agent_name": agent_name,
                            "capabilities": self.agent_capabilities[agent_name],
                            "status": self.registered_agents[agent_name]["status"],
                            "last_activity": self.registered_agents[agent_name]["last_activity"]
                        })
                    else:
                        return json.dumps({"error": f"Agent {agent_name} not found"})
                else:
                    # Return all agent capabilities
                    all_capabilities = {}
                    for agent, caps in self.agent_capabilities.items():
                        all_capabilities[agent] = {
                            "capabilities": caps,
                            "status": self.registered_agents[agent]["status"],
                            "message_count": self.registered_agents[agent]["message_count"]
                        }
                    
                    return json.dumps({
                        "total_agents": len(all_capabilities),
                        "agents": all_capabilities,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except Exception as e:
                logger.error(f"Error getting agent capabilities: {str(e)}")
                return json.dumps({"error": str(e)})
    
    def _setup_resources(self):
        """Setup MCP resources"""
        
        @self.server.resource("workflows")
        async def get_workflows() -> List[Resource]:
            """Get list of active workflows"""
            resources = []
            
            for workflow_id, workflow in self.active_workflows.items():
                resources.append(Resource(
                    uri=f"workflow://{workflow_id}",
                    name=f"Workflow {workflow_id}",
                    mimeType="application/json",
                    description=f"Financial analysis workflow for {', '.join(workflow['symbols'])}"
                ))
            
            return resources
        
        @self.server.resource("agents")
        async def get_agents() -> List[Resource]:
            """Get list of registered agents"""
            resources = []
            
            for agent_name, agent_info in self.registered_agents.items():
                resources.append(Resource(
                    uri=f"agent://{agent_name}",
                    name=f"Agent {agent_name}",
                    mimeType="application/json", 
                    description=f"Financial agent with {len(agent_info['capabilities'])} capabilities"
                ))
            
            return resources
    
    async def _route_to_agent(self, agent_name: str, data: Dict[str, Any], correlation_id: str):
        """Route message to specific agent"""
        # In a real implementation, this would route to actual agent instances
        logger.info(f"Routing message to {agent_name} with correlation_id {correlation_id}")
        
        # Update workflow status
        if correlation_id in self.active_workflows:
            workflow = self.active_workflows[correlation_id]
            if agent_name not in workflow["agents_involved"]:
                workflow["agents_involved"].append(agent_name)
    
    async def _route_message(self, message: Dict[str, Any]):
        """Route message between agents"""
        target_agent = message["target_agent"]
        
        # In a real implementation, this would deliver to actual agent
        logger.info(f"Routing message {message['message_id']} to {target_agent}")
        
        # Simulate message delivery delay
        await asyncio.sleep(0.1)
    
    async def start_server(self):
        """Start the MCP server"""
        try:
            logger.info(f"Starting Financial MCP Server: {self.server_name}")
            
            # Start server with stdio transport
            async with stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
                
        except Exception as e:
            logger.error(f"Error starting MCP server: {str(e)}")
            raise
    
    async def shutdown_server(self):
        """Gracefully shutdown the server"""
        logger.info("Shutting down Financial MCP Server")
        
        # Save active workflows (in production, would persist to database)
        for workflow_id, workflow in self.active_workflows.items():
            workflow["shutdown_time"] = datetime.now().isoformat()
            workflow["status"] = "interrupted"
        
        # Clear resources
        self.active_workflows.clear()
        self.registered_agents.clear()
        self.agent_capabilities.clear()
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "server_name": self.server_name,
            "registered_agents": len(self.registered_agents),
            "active_workflows": len(self.active_workflows),
            "total_messages": len(self.message_history),
            "uptime_start": self.server_metrics["uptime_start"],
            "capabilities": [
                "financial_data_analysis",
                "multi_agent_orchestration", 
                "workflow_management",
                "real_time_communication",
                "performance_monitoring"
            ]
        }


async def main():
    """Main entry point for MCP server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Financial Multi-Agent MCP Server")
    parser.add_argument("--name", default="financial-multi-agent-system", help="Server name")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start server
    server = FinancialMCPServer(args.name)
    
    try:
        await server.start_server()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        await server.shutdown_server()


if __name__ == "__main__":
    asyncio.run(main())

