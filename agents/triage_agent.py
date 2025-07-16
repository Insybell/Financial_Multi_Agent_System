import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from ..core.base_agent import BaseFinancialAgent
from ..core.models import TriageResult, FinancialReport, Recommendation, RiskAssessment
from ..core.enums import MessageType, Priority, RiskLevel, RecommendationAction, AgentStatus

logger = logging.getLogger(__name__)


class TriageAgent(BaseFinancialAgent):
    """Agent responsible for prioritizing and routing financial analysis requests"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("TriageAgent", config)
        
        # Triage configuration
        self.triage_config = {
            "max_concurrent_workflows": 10,
            "priority_decay_hours": 24,
            "urgent_response_time_minutes": 5,
            "normal_response_time_minutes": 30,
            "batch_processing_size": 5,
            "emergency_keywords": ["urgent", "critical", "emergency", "immediate"],
            "vip_symbols": ["SPY", "QQQ", "IWM"],  # Market indices get priority
        }
        
        # Triage state management
        self.request_queue = asyncio.PriorityQueue()
        self.active_workflows = {}
        self.completed_workflows = deque(maxlen=100)
        self.agent_status_cache = {}
        
        # Priority scoring weights
        self.priority_weights = {
            "risk_level": 0.3,
            "market_impact": 0.25,
            "time_sensitivity": 0.2,
            "data_quality": 0.15,
            "user_priority": 0.1
        }
        
        # Register message handlers
        self.register_message_handler(MessageType.REPORT_GENERATED, self._handle_report_generated)
        self.register_message_handler(MessageType.ERROR_OCCURRED, self._handle_error_occurred)
        self.register_message_handler(MessageType.HEALTH_CHECK, self._handle_health_check)
    
    async def _handle_report_generated(self, message):
        """Handle completed workflow reports"""
        report_data = message.data.get('report', {})
        report_type = message.data.get('report_type', 'unknown')
        symbol = message.data.get('symbol', 'unknown')
        
        # Mark workflow as completed
        if message.correlation_id in self.active_workflows:
            workflow = self.active_workflows[message.correlation_id]
            workflow['status'] = 'completed'
            workflow['completion_time'] = datetime.now().isoformat()
            workflow['result'] = report_data
            
            # Move to completed workflows
            self.completed_workflows.append(workflow)
            del self.active_workflows[message.correlation_id]
            
            await self.log_activity(
                f"Workflow completed for {symbol}",
                data={
                    'correlation_id': message.correlation_id,
                    'report_type': report_type,
                    'processing_time': self._calculate_processing_time(workflow)
                }
            )
    
    async def _handle_error_occurred(self, message):
        """Handle workflow errors"""
        error_data = message.data
        
        if message.correlation_id in self.active_workflows:
            workflow = self.active_workflows[message.correlation_id]
            workflow['status'] = 'failed'
            workflow['error'] = error_data
            workflow['completion_time'] = datetime.now().isoformat()
            
            # Move to completed workflows
            self.completed_workflows.append(workflow)
            del self.active_workflows[message.correlation_id]
            
            await self.log_activity(
                f"Workflow failed: {error_data.get('error', 'Unknown error')}",
                "error",
                data={'correlation_id': message.correlation_id}
            )
    
    async def _handle_health_check(self, message):
        """Handle agent health check responses"""
        agent_name = message.source_agent
        health_data = message.data
        
        self.agent_status_cache[agent_name] = {
            'status': health_data.get('status', 'unknown'),
            'last_update': datetime.now().isoformat(),
            'queue_size': health_data.get('queue_size', 0),
            'error_count': health_data.get('error_count', 0)
        }
    
    def _calculate_processing_time(self, workflow: Dict[str, Any]) -> float:
        """Calculate workflow processing time in seconds"""
        try:
            start_time = datetime.fromisoformat(workflow['start_time'])
            end_time = datetime.fromisoformat(workflow['completion_time'])
            return (end_time - start_time).total_seconds()
        except:
            return 0.0
    
    async def triage_analysis_request(self, request: Dict[str, Any]) -> TriageResult:
        """Triage an incoming analysis request"""
        try:
            symbol = request.get('symbol', 'UNKNOWN')
            request_type = request.get('type', 'individual_analysis')
            user_priority = request.get('priority', 'normal')
            metadata = request.get('metadata', {})
            
            await self.log_activity(f"Triaging analysis request for {symbol}")
            
            # Calculate priority score
            priority_score = await self._calculate_priority_score(request)
            
            # Determine urgency level
            urgency_level = self._determine_urgency_level(priority_score, request)
            
            # Estimate processing time
            estimated_time = self._estimate_processing_time(request_type, urgency_level)
            
            # Determine recommended agent routing
            recommended_agents = self._recommend_agent_routing(request, urgency_level)
            
            # Generate reasoning
            reasoning = self._generate_triage_reasoning(
                priority_score, urgency_level, request, metadata
            )
            
            triage_result = TriageResult(
                symbol=symbol,
                priority_score=priority_score,
                urgency_level=urgency_level,
                reasoning=reasoning,
                recommended_agents=recommended_agents,
                estimated_processing_time=estimated_time,
                triage_timestamp=datetime.now().isoformat()
            )
            
            await self.log_activity(
                f"Triage completed for {symbol}",
                data={
                    'priority_score': priority_score,
                    'urgency_level': urgency_level.value,
                    'estimated_time': estimated_time,
                    'recommended_agents': recommended_agents
                }
            )
            
            return triage_result
            
        except Exception as e:
            await self.log_activity(f"Triage failed for request: {str(e)}", "error")
            raise
    
    async def _calculate_priority_score(self, request: Dict[str, Any]) -> float:
        """Calculate priority score based on multiple factors"""
        score = 0.0
        
        symbol = request.get('symbol', '')
        user_priority = request.get('priority', 'normal')
        metadata = request.get('metadata', {})
        
        # Risk level factor
        risk_level = metadata.get('risk_level', 'medium')
        risk_scores = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'critical': 1.0
        }
        score += risk_scores.get(risk_level, 0.5) * self.priority_weights['risk_level']
        
        # Market impact factor
        market_impact = 0.5  # Default
        if symbol in self.triage_config['vip_symbols']:
            market_impact = 1.0
        elif symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']:  # Large caps
            market_impact = 0.8
        elif metadata.get('market_cap', 'unknown') == 'large':
            market_impact = 0.7
        
        score += market_impact * self.priority_weights['market_impact']
        
        # Time sensitivity factor
        time_sensitivity = 0.5  # Default
        request_text = ' '.join([
            request.get('description', ''),
            user_priority,
            str(metadata)
        ]).lower()
        
        # Check for urgent keywords
        if any(keyword in request_text for keyword in self.triage_config['emergency_keywords']):
            time_sensitivity = 1.0
        elif user_priority == 'high':
            time_sensitivity = 0.8
        elif user_priority == 'urgent':
            time_sensitivity = 1.0
        
        score += time_sensitivity * self.priority_weights['time_sensitivity']
        
        # Data quality factor
        data_quality = metadata.get('data_quality', 0.7)  # Default quality
        score += data_quality * self.priority_weights['data_quality']
        
        # User priority factor
        user_priority_scores = {
            'low': 0.2,
            'normal': 0.5,
            'high': 0.8,
            'urgent': 1.0,
            'critical': 1.0
        }
        score += user_priority_scores.get(user_priority, 0.5) * self.priority_weights['user_priority']
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _determine_urgency_level(self, priority_score: float, request: Dict[str, Any]) -> Priority:
        """Determine urgency level based on priority score and other factors"""
        
        # Check for explicit critical conditions
        metadata = request.get('metadata', {})
        if metadata.get('risk_level') == 'critical':
            return Priority.CRITICAL
        
        user_priority = request.get('priority', 'normal')
        if user_priority in ['urgent', 'critical']:
            return Priority.CRITICAL
        
        # Score-based classification
        if priority_score >= 0.9:
            return Priority.CRITICAL
        elif priority_score >= 0.7:
            return Priority.HIGH
        elif priority_score >= 0.4:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _estimate_processing_time(self, request_type: str, urgency_level: Priority) -> int:
        """Estimate processing time in seconds"""
        
        # Base processing times by request type
        base_times = {
            'individual_analysis': 180,  # 3 minutes
            'portfolio_analysis': 600,   # 10 minutes
            'market_overview': 300,      # 5 minutes
            'risk_assessment': 120,      # 2 minutes
            'quick_quote': 30           # 30 seconds
        }
        
        base_time = base_times.get(request_type, 180)
        
        # Adjust based on urgency (higher urgency = more resources = faster)
        urgency_multipliers = {
            Priority.CRITICAL: 0.5,  # Rush processing
            Priority.HIGH: 0.7,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 1.5        # Lower priority, longer wait
        }
        
        multiplier = urgency_multipliers.get(urgency_level, 1.0)
        
        # Add queue delay estimate
        queue_delay = len(self.active_workflows) * 30  # 30 seconds per active workflow
        
        total_time = int(base_time * multiplier + queue_delay)
        return max(total_time, 30)  # Minimum 30 seconds
    
    def _recommend_agent_routing(self, request: Dict[str, Any], urgency_level: Priority) -> List[str]:
        """Recommend agent routing based on request characteristics"""
        
        request_type = request.get('type', 'individual_analysis')
        metadata = request.get('metadata', {})
        
        # Standard routing for different request types
        if request_type == 'individual_analysis':
            agents = [
                "DataCollectionAgent",
                "BusinessIntelligenceAgent", 
                "RiskAssessmentAgent",
                "RecommendationAgent",
                "ReportGenerationAgent"
            ]
        elif request_type == 'portfolio_analysis':
            agents = [
                "DataCollectionAgent",
                "BusinessIntelligenceAgent",
                "RiskAssessmentAgent", 
                "RecommendationAgent",
                "ReportGenerationAgent"
            ]
        elif request_type == 'risk_assessment':
            agents = [
                "DataCollectionAgent",
                "RiskAssessmentAgent",
                "ReportGenerationAgent"
            ]
        elif request_type == 'quick_quote':
            agents = ["DataCollectionAgent"]
        else:
            # Default full pipeline
            agents = [
                "DataCollectionAgent",
                "BusinessIntelligenceAgent",
                "RiskAssessmentAgent", 
                "RecommendationAgent",
                "ReportGenerationAgent"
            ]
        
        # For critical urgency, might skip some agents for speed
        if urgency_level == Priority.CRITICAL and request_type == 'individual_analysis':
            # Skip detailed BI analysis for speed
            if "BusinessIntelligenceAgent" in agents:
                agents.remove("BusinessIntelligenceAgent")
        
        return agents
    
    def _generate_triage_reasoning(self, priority_score: float, urgency_level: Priority,
                                 request: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for triage decision"""
        
        reasoning_parts = []
        
        # Priority score explanation
        if priority_score >= 0.8:
            reasoning_parts.append("High priority score due to significant risk factors and market impact.")
        elif priority_score >= 0.6:
            reasoning_parts.append("Moderate priority score with some elevated risk factors.")
        else:
            reasoning_parts.append("Standard priority score with normal risk profile.")
        
        # Urgency factors
        symbol = request.get('symbol', 'UNKNOWN')
        if symbol in self.triage_config['vip_symbols']:
            reasoning_parts.append("Market index symbol receives elevated priority.")
        
        user_priority = request.get('priority', 'normal')
        if user_priority in ['high', 'urgent', 'critical']:
            reasoning_parts.append(f"User-specified {user_priority} priority increases urgency.")
        
        risk_level = metadata.get('risk_level')
        if risk_level in ['high', 'critical']:
            reasoning_parts.append(f"Risk level ({risk_level}) requires immediate attention.")
        
        # Processing approach
        if urgency_level == Priority.CRITICAL:
            reasoning_parts.append("Critical urgency - fast-track processing recommended.")
        elif urgency_level == Priority.HIGH:
            reasoning_parts.append("High urgency - prioritized processing queue.")
        else:
            reasoning_parts.append("Standard processing queue assignment.")
        
        return " ".join(reasoning_parts)
    
    async def route_workflow(self, triage_result: TriageResult, request_data: Dict[str, Any]) -> str:
        """Route workflow through the recommended agents"""
        try:
            correlation_id = f"workflow_{triage_result.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create workflow tracking
            workflow = {
                'correlation_id': correlation_id,
                'symbol': triage_result.symbol,
                'triage_result': triage_result,
                'request_data': request_data,
                'start_time': datetime.now().isoformat(),
                'status': 'active',
                'current_agent': None,
                'agents_completed': [],
                'agents_remaining': triage_result.recommended_agents.copy()
            }
            
            self.active_workflows[correlation_id] = workflow
            
            # Start the workflow with the first agent
            if triage_result.recommended_agents:
                first_agent = triage_result.recommended_agents[0]
                await self._route_to_agent(first_agent, request_data, correlation_id, triage_result.urgency_level)
                
                workflow['current_agent'] = first_agent
                workflow['agents_remaining'].remove(first_agent)
            
            await self.log_activity(
                f"Workflow routed for {triage_result.symbol}",
                data={
                    'correlation_id': correlation_id,
                    'urgency_level': triage_result.urgency_level.value,
                    'agents_count': len(triage_result.recommended_agents)
                }
            )
            
            return correlation_id
            
        except Exception as e:
            await self.log_activity(f"Workflow routing failed: {str(e)}", "error")
            raise
    
    async def _route_to_agent(self, agent_name: str, data: Dict[str, Any], 
                            correlation_id: str, priority: Priority):
        """Route request to specific agent"""
        
        # Send message to target agent
        await self.send_mcp_message(
            target_agent=agent_name,
            message_type=MessageType.DATA_COLLECTED if agent_name == "DataCollectionAgent" else MessageType.ANALYSIS_COMPLETE,
            data=data,
            priority=priority,
            correlation_id=correlation_id
        )
    
    async def manage_workflow_queue(self):
        """Manage the workflow queue and load balancing"""
        try:
            while True:
                # Check for new requests in queue
                if not self.request_queue.empty():
                    # Check if we can handle more workflows
                    if len(self.active_workflows) < self.triage_config['max_concurrent_workflows']:
                        try:
                            priority, request = await asyncio.wait_for(
                                self.request_queue.get(), timeout=1.0
                            )
                            
                            # Process the request
                            triage_result = await self.triage_analysis_request(request)
                            correlation_id = await self.route_workflow(triage_result, request)
                            
                            await self.log_activity(f"Started workflow {correlation_id}")
                            
                        except asyncio.TimeoutError:
                            continue
                        except Exception as e:
                            await self.log_activity(f"Error processing queue item: {str(e)}", "error")
                
                # Clean up old workflows
                await self._cleanup_old_workflows()
                
                # Wait before next queue check
                await asyncio.sleep(5)
                
        except Exception as e:
            await self.log_activity(f"Queue management error: {str(e)}", "error")
    
    async def _cleanup_old_workflows(self):
        """Clean up old or stale workflows"""
        current_time = datetime.now()
        stale_workflows = []
        
        for correlation_id, workflow in self.active_workflows.items():
            start_time = datetime.fromisoformat(workflow['start_time'])
            age_hours = (current_time - start_time).total_seconds() / 3600
            
            # Mark workflows older than 2 hours as stale
            if age_hours > 2:
                stale_workflows.append(correlation_id)
        
        # Clean up stale workflows
        for correlation_id in stale_workflows:
            workflow = self.active_workflows[correlation_id]
            workflow['status'] = 'timeout'
            workflow['completion_time'] = current_time.isoformat()
            
            self.completed_workflows.append(workflow)
            del self.active_workflows[correlation_id]
            
            await self.log_activity(f"Cleaned up stale workflow {correlation_id}")
    
    async def submit_analysis_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an analysis request to the triage system"""
        try:
            # Perform immediate triage
            triage_result = await self.triage_analysis_request(request)
            
            # Add to priority queue
            priority_value = -triage_result.priority_score  # Negative for max priority queue
            await self.request_queue.put((priority_value, request))
            
            return {
                'status': 'queued',
                'triage_result': {
                    'symbol': triage_result.symbol,
                    'priority_score': triage_result.priority_score,
                    'urgency_level': triage_result.urgency_level.value,
                    'estimated_processing_time': triage_result.estimated_processing_time,
                    'reasoning': triage_result.reasoning
                },
                'queue_position': self.request_queue.qsize(),
                'estimated_start_time': self._estimate_start_time(triage_result)
            }
            
        except Exception as e:
            await self.log_activity(f"Failed to submit request: {str(e)}", "error")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _estimate_start_time(self, triage_result: TriageResult) -> str:
        """Estimate when the workflow will start processing"""
        # Simple estimation based on queue size and active workflows
        queue_delay = self.request_queue.qsize() * 60  # 1 minute per queued item
        active_delay = len(self.active_workflows) * 30  # 30 seconds per active workflow
        
        # Higher priority gets faster processing
        if triage_result.urgency_level == Priority.CRITICAL:
            delay = min(queue_delay, 60)  # Max 1 minute delay for critical
        elif triage_result.urgency_level == Priority.HIGH:
            delay = queue_delay * 0.5
        else:
            delay = queue_delay + active_delay
        
        start_time = datetime.now() + timedelta(seconds=delay)
        return start_time.isoformat()
    
    async def get_workflow_status(self, correlation_id: str) -> Dict[str, Any]:
        """Get status of a specific workflow"""
        
        # Check active workflows
        if correlation_id in self.active_workflows:
            workflow = self.active_workflows[correlation_id]
            return {
                'status': workflow['status'],
                'symbol': workflow['symbol'],
                'current_agent': workflow.get('current_agent'),
                'agents_completed': workflow.get('agents_completed', []),
                'agents_remaining': workflow.get('agents_remaining', []),
                'start_time': workflow['start_time'],
                'processing_time': self._calculate_processing_time_active(workflow)
            }
        
        # Check completed workflows
        for workflow in self.completed_workflows:
            if workflow['correlation_id'] == correlation_id:
                return {
                    'status': workflow['status'],
                    'symbol': workflow['symbol'],
                    'start_time': workflow['start_time'],
                    'completion_time': workflow.get('completion_time'),
                    'processing_time': self._calculate_processing_time(workflow),
                    'result': workflow.get('result'),
                    'error': workflow.get('error')
                }
        
        return {'status': 'not_found'}
    
    def _calculate_processing_time_active(self, workflow: Dict[str, Any]) -> float:
        """Calculate processing time for active workflow"""
        try:
            start_time = datetime.fromisoformat(workflow['start_time'])
            current_time = datetime.now()
            return (current_time - start_time).total_seconds()
        except:
            return 0.0
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        
        # Queue metrics
        queue_size = self.request_queue.qsize()
        active_workflows_count = len(self.active_workflows)
        completed_workflows_count = len(self.completed_workflows)
        
        # Processing time statistics
        if self.completed_workflows:
            processing_times = [
                self._calculate_processing_time(wf) 
                for wf in self.completed_workflows 
                if wf.get('completion_time')
            ]
            
            if processing_times:
                avg_processing_time = np.mean(processing_times)
                max_processing_time = np.max(processing_times)
                min_processing_time = np.min(processing_times)
            else:
                avg_processing_time = max_processing_time = min_processing_time = 0.0
        else:
            avg_processing_time = max_processing_time = min_processing_time = 0.0
        
        # Success rate
        total_completed = len([wf for wf in self.completed_workflows if wf.get('completion_time')])
        successful_completed = len([wf for wf in self.completed_workflows if wf.get('status') == 'completed'])
        success_rate = successful_completed / total_completed if total_completed > 0 else 0.0
        
        # Agent status summary
        active_agents = len([status for status in self.agent_status_cache.values() 
                           if status.get('status') in ['active', 'idle']])
        
        return {
            'queue_metrics': {
                'queue_size': queue_size,
                'active_workflows': active_workflows_count,
                'completed_workflows': completed_workflows_count,
                'max_concurrent': self.triage_config['max_concurrent_workflows']
            },
            'performance_metrics': {
                'average_processing_time': avg_processing_time,
                'max_processing_time': max_processing_time,
                'min_processing_time': min_processing_time,
                'success_rate': success_rate
            },
            'system_health': {
                'active_agents': active_agents,
                'total_agents_monitored': len(self.agent_status_cache),
                'system_load': active_workflows_count / self.triage_config['max_concurrent_workflows']
            },
            'timestamp': datetime.now().isoformat()
        }
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing method"""
        try:
            request_type = input_data.get('action', 'submit_request')
            
            if request_type == 'submit_request':
                return await self.submit_analysis_request(input_data.get('request', {}))
            
            elif request_type == 'get_status':
                correlation_id = input_data.get('correlation_id')
                return await self.get_workflow_status(correlation_id)
            
            elif request_type == 'get_metrics':
                return await self.get_system_metrics()
            
            else:
                raise ValueError(f"Unsupported action: {request_type}")
                
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "request_prioritization",
            "workflow_routing", 
            "load_balancing",
            "queue_management",
            "performance_monitoring",
            "system_health_tracking",
            "agent_coordination",
            "priority_scoring",
            "urgency_classification",
            "processing_time_estimation"
        ]
    
    async def update_triage_config(self, new_config: Dict[str, Any]):
        """Update triage configuration"""
        self.triage_config.update(new_config)
        await self.log_activity("Triage configuration updated", data=new_config)
    
    async def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get summary of all agent statuses"""
        return {
            'agents': self.agent_status_cache,
            'last_updated': datetime.now().isoformat(),
            'total_agents': len(self.agent_status_cache)
        }
