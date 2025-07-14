# core/base_agent.py
"""
Base agent class for the Financial Multi-Agent System
Author: Zhang Weiling (Insybell)
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from langchain_openai import ChatOpenAI
from .models import MCPMessage, AgentPerformance
from .enums import MessageType, Priority, AgentStatus, ErrorSeverity
from .guardrails import FinancialGuardrails

logger = logging.getLogger(__name__)


class BaseFinancialAgent(ABC):
    """Base class for all financial agents in the multi-agent system"""
    
    def __init__(self, agent_name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the base agent"""
        self.agent_name = agent_name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.guardrails = FinancialGuardrails()
        self.llm = ChatOpenAI(
            model=self.config.get("llm_model", "gpt-4"),
            temperature=self.config.get("temperature", 0.1)
        )
        
        # Message handling
        self.message_history: List[MCPMessage] = []
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        # Performance tracking
        self.performance = AgentPerformance(
            agent_name=agent_name,
            success_rate=0.0,
            average_processing_time=0.0,
            error_count=0,
            last_execution="",
            total_executions=0
        )
        
        # Event callbacks
        self.on_message_received: Optional[Callable] = None
        self.on_processing_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        logger.info(f"Initialized agent: {agent_name}")
    
    async def send_mcp_message(self, target_agent: str, message_type: MessageType, 
                              data: Dict[str, Any], priority: Priority = Priority.MEDIUM,
                              correlation_id: Optional[str] = None) -> str:
        """Send MCP message to another agent"""
        message = MCPMessage(
            message_type=message_type,
            source_agent=self.agent_name,
            target_agent=target_agent,
            data=data,
            timestamp=datetime.now().isoformat(),
            message_id=str(uuid.uuid4()),
            priority=priority,
            correlation_id=correlation_id
        )
        
        self.message_history.append(message)
        
        # Put message in queue for processing
        await self.message_queue.put(message)
        
        logger.info(f"{self.agent_name} -> {target_agent}: {message_type.value} (ID: {message.message_id})")
        
        if self.on_message_received:
            await self.on_message_received(message)
        
        return message.message_id
    
    async def receive_message(self, message: MCPMessage) -> bool:
        """Receive and handle incoming MCP message"""
        try:
            self.status = AgentStatus.BUSY
            
            # Check if we have a handler for this message type
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message)
            else:
                # Default handling - process the message data
                await self.process(message.data)
            
            logger.info(f"{self.agent_name} processed message {message.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {str(e)}")
            self.performance.error_count += 1
            
            if self.on_error:
                await self.on_error(e, message)
            
            return False
        finally:
            self.status = AgentStatus.IDLE
    
    def register_message_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for specific message type"""
        self.message_handlers[message_type] = handler
        logger.info(f"{self.agent_name} registered handler for {message_type.value}")
    
    async def start_message_processing(self):
        """Start the message processing loop"""
        logger.info(f"{self.agent_name} starting message processing loop")
        
        while True:
            try:
                # Wait for messages with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=self.config.get("message_timeout", 60)
                )
                
                # Process the message
                await self.receive_message(message)
                self.message_queue.task_done()
                
            except asyncio.TimeoutError:
                # No messages received, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error in message processing loop: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the agent"""
        health_status = {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "queue_size": self.message_queue.qsize(),
            "total_messages_processed": len(self.message_history),
            "error_count": self.performance.error_count,
            "success_rate": self.calculate_success_rate(),
            "last_activity": self.performance.last_execution,
            "memory_usage": self._get_memory_usage(),
            "timestamp": datetime.now().isoformat()
        }
        
        return health_status
    
    def calculate_success_rate(self) -> float:
        """Calculate agent success rate"""
        if self.performance.total_executions == 0:
            return 0.0
        
        successful_executions = self.performance.total_executions - self.performance.error_count
        return successful_executions / self.performance.total_executions
    
    def _get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics"""
        return {
            "message_history_size": len(self.message_history),
            "message_queue_size": self.message_queue.qsize(),
            "handlers_registered": len(self.message_handlers)
        }
    
    async def cleanup(self):
        """Cleanup agent resources"""
        logger.info(f"Cleaning up agent: {self.agent_name}")
        
        # Clear message queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # Clear message history (keep last 100 for debugging)
        if len(self.message_history) > 100:
            self.message_history = self.message_history[-100:]
        
        self.status = AgentStatus.OFFLINE
    
    def update_performance_metrics(self, processing_time: float, success: bool):
        """Update agent performance metrics"""
        self.performance.total_executions += 1
        self.performance.last_execution = datetime.now().isoformat()
        
        if not success:
            self.performance.error_count += 1
        
        # Update average processing time
        if self.performance.average_processing_time == 0:
            self.performance.average_processing_time = processing_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.performance.average_processing_time = (
                alpha * processing_time + 
                (1 - alpha) * self.performance.average_processing_time
            )
        
        self.performance.success_rate = self.calculate_success_rate()
    
    async def log_activity(self, activity: str, level: str = "info", data: Optional[Dict[str, Any]] = None):
        """Log agent activity with structured data"""
        log_entry = {
            "agent": self.agent_name,
            "activity": activity,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"{self.agent_name}: {activity}", extra=log_entry)
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Main processing method - must be implemented by subclasses"""
        pass
    
    async def validate_input(self, input_data: Any) -> bool:
        """Validate input data before processing"""
        if input_data is None:
            logger.warning(f"{self.agent_name}: Received None input data")
            return False
        
        return True
    
    async def process_with_monitoring(self, input_data: Any) -> Any:
        """Process data with performance monitoring and error handling"""
        start_time = datetime.now()
        success = False
        result = None
        
        try:
            # Validate input
            if not await self.validate_input(input_data):
                raise ValueError("Input validation failed")
            
            # Set status to busy
            self.status = AgentStatus.BUSY
            
            # Process the data
            result = await self.process(input_data)
            success = True
            
            await self.log_activity("Processing completed successfully")
            
            if self.on_processing_complete:
                await self.on_processing_complete(result)
            
            return result
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            
            if self.on_error:
                await self.on_error(e, input_data)
            
            raise
        
        finally:
            # Update performance metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_performance_metrics(processing_time, success)
            
            # Reset status
            self.status = AgentStatus.IDLE
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive agent information"""
        return {
            "name": self.agent_name,
            "status": self.status.value,
            "config": self.config,
            "performance": {
                "success_rate": self.performance.success_rate,
                "average_processing_time": self.performance.average_processing_time,
                "total_executions": self.performance.total_executions,
                "error_count": self.performance.error_count,
                "last_execution": self.performance.last_execution
            },
            "capabilities": self.get_capabilities(),
            "message_handlers": list(self.message_handlers.keys()),
            "created_at": getattr(self, 'created_at', datetime.now().isoformat())
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass
