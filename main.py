# main.py
"""
Financial Multi-Agent System - Main Application
Author: Zhang Weiling (Insybell)
Description: Complete financial analysis system using multiple AI agents
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import click

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.data_collection_agent import DataCollectionAgent
from agents.business_intelligence_agent import BusinessIntelligenceAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.recommendation_agent import RecommendationAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.triage_agent import TriageAgent
from core.enums import Priority
from core.models import SystemHealth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FinancialMultiAgentSystem:
    """Main orchestrator for the Financial Multi-Agent System"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the multi-agent system"""
        self.config = config or self._load_default_config()
        self.agents = {}
        self.system_status = "initializing"
        self.workflow_history = []
        
        # Initialize agents
        self._initialize_agents()
        
        logger.info("Financial Multi-Agent System initialized")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default system configuration"""
        return {
            "agents": {
                "data_collection": {
                    "cache_ttl_hours": 1,
                    "max_cache_size": 100,
                    "max_retries": 3
                },
                "business_intelligence": {
                    "llm_model": "gpt-4",
                    "temperature": 0.1
                },
                "risk_assessment": {
                    "confidence_threshold": 0.7,
                    "risk_free_rate": 0.02
                }
            },
            "system": {
                "max_concurrent_workflows": 10,
                "message_timeout": 60,
                "health_check_interval": 300
            }
        }
    
    def _initialize_agents(self):
        """Initialize all agents with their configurations"""
        try:
            # Data Collection Agent
            self.agents['data_collection'] = DataCollectionAgent(
                config=self.config.get('agents', {}).get('data_collection', {})
            )
            
            # Business Intelligence Agent
            self.agents['business_intelligence'] = BusinessIntelligenceAgent(
                config=self.config.get('agents', {}).get('business_intelligence', {})
            )
            
            # Risk Assessment Agent
            self.agents['risk_assessment'] = RiskAssessmentAgent(
                config=self.config.get('agents', {}).get('risk_assessment', {})
            )
            
            # Recommendation Agent
            self.agents['recommendation'] = RecommendationAgent(
                config=self.config.get('agents', {}).get('recommendation', {})
            )
            
            # Report Generation Agent
            self.agents['report_generation'] = ReportGenerationAgent(
                config=self.config.get('agents', {}).get('report_generation', {})
            )
            
            # Triage Agent
            self.agents['triage'] = TriageAgent(
                config=self.config.get('agents', {}).get('triage', {})
            )
            
            logger.info(f"Initialized {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {str(e)}")
            raise
    
    async def start_system(self):
        """Start the multi-agent system"""
        try:
            logger.info("Starting Financial Multi-Agent System...")
            
            # Start message processing for all agents
            agent_tasks = []
            for agent_name, agent in self.agents.items():
                task = asyncio.create_task(
                    agent.start_message_processing(),
                    name=f"{agent_name}_processing"
                )
                agent_tasks.append(task)
            
            # Start health monitoring
            health_task = asyncio.create_task(
                self._health_monitor(),
                name="health_monitor"
            )
            agent_tasks.append(health_task)
            
            self.system_status = "running"
            logger.info("Financial Multi-Agent System started successfully")
            
            # Wait for all tasks
            await asyncio.gather(*agent_tasks)
            
        except Exception as e:
            logger.error(f"System startup failed: {str(e)}")
            self.system_status = "error"
            raise
    
    async def analyze_symbols(self, symbols: List[str], analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze a list of financial symbols"""
        try:
            workflow_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Starting analysis workflow {workflow_id} for symbols: {symbols}")
            
            # Record workflow start
            workflow_data = {
                'workflow_id': workflow_id,
                'symbols': symbols,
                'analysis_type': analysis_type,
                'start_time': datetime.now().isoformat(),
                'status': 'running',
                'results': {}
            }
            self.workflow_history.append(workflow_data)
            
            # Start data collection
            collected_data = await self.agents['data_collection'].collect_multiple_symbols(
                symbols=symbols,
                period="1y"
            )
            
            # Process each symbol through the analysis pipeline
            results = {}
            for financial_data in collected_data:
                symbol = financial_data.symbol
                logger.info(f"Processing {symbol} through analysis pipeline")
                
                try:
                    # Business Intelligence Analysis
                    market_analysis = await self.agents['business_intelligence'].analyze_market_data(financial_data)
                    
                    # Risk Assessment
                    risk_assessment = await self.agents['risk_assessment'].assess_comprehensive_risk(market_analysis)
                    
                    # Store results
                    results[symbol] = {
                        'financial_data': {
                            'symbol': financial_data.symbol,
                            'data_quality': financial_data.data_quality,
                            'records_count': len(financial_data.data),
                            'source': financial_data.source,
                            'timestamp': financial_data.timestamp
                        },
                        'market_analysis': {
                            'current_price': market_analysis.current_price,
                            'trend_strength': market_analysis.trend_strength,
                            'rsi': market_analysis.technical_indicators.rsi,
                            'volume_trend': market_analysis.volume_analysis.get('trend', 'unknown'),
                            'data_quality': market_analysis.data_quality
                        },
                        'risk_assessment': {
                            'risk_level': risk_assessment.risk_level.value,
                            'volatility': risk_assessment.risk_metrics.volatility,
                            'var_95': risk_assessment.risk_metrics.var_95,
                            'sharpe_ratio': risk_assessment.risk_metrics.sharpe_ratio,
                            'max_drawdown': risk_assessment.risk_metrics.max_drawdown,
                            'confidence': risk_assessment.confidence,
                            'risk_factors': risk_assessment.risk_factors
                        },
                        'processing_timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Successfully processed {symbol}")
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                    results[symbol] = {
                        'error': str(e),
                        'processing_timestamp': datetime.now().isoformat()
                    }
            
            # Update workflow data
            workflow_data['status'] = 'completed'
            workflow_data['end_time'] = datetime.now().isoformat()
            workflow_data['results'] = results
            
            logger.info(f"Analysis workflow {workflow_id} completed")
            
            return {
                'workflow_id': workflow_id,
                'status': 'completed',
                'symbols_requested': len(symbols),
                'symbols_processed': len([r for r in results.values() if 'error' not in r]),
                'symbols_failed': len([r for r in results.values() if 'error' in r]),
                'results': results,
                'completion_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis workflow failed: {str(e)}")
            raise
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get current market summary"""
        try:
            return await self.agents['data_collection'].get_market_summary()
        except Exception as e:
            logger.error(f"Failed to get market summary: {str(e)}")
            return {"error": str(e)}
    
    async def get_system_health(self) -> SystemHealth:
        """Get comprehensive system health status"""
        try:
            active_agents = []
            failed_agents = []
            performance_metrics = {}
            
            for agent_name, agent in self.agents.items():
                try:
                    health = await agent.health_check()
                    if health.get('status') in ['active', 'idle']:
                        active_agents.append(agent_name)
                    else:
                        failed_agents.append(agent_name)
                    
                    performance_metrics[agent_name] = agent.performance
                    
                except Exception as e:
                    logger.error(f"Health check failed for {agent_name}: {str(e)}")
                    failed_agents.append(agent_name)
            
            # Determine overall system status
            if not failed_agents:
                status = "healthy"
            elif len(failed_agents) < len(self.agents) / 2:
                status = "degraded"
            else:
                status = "critical"
            
            return SystemHealth(
                status=status,
                active_agents=active_agents,
                failed_agents=failed_agents,
                message_queue_size=sum(agent.message_queue.qsize() for agent in self.agents.values()),
                last_health_check=datetime.now().isoformat(),
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            logger.error(f"System health check failed: {str(e)}")
            return SystemHealth(
                status="critical",
                active_agents=[],
                failed_agents=list(self.agents.keys()),
                message_queue_size=0,
                last_health_check=datetime.now().isoformat(),
                performance_metrics={}
            )
    
    async def _health_monitor(self):
        """Background health monitoring task"""
        interval = self.config.get('system', {}).get('health_check_interval', 300)
        
        while True:
            try:
                await asyncio.sleep(interval)
                health = await self.get_system_health()
                
                if health.status == "critical":
                    logger.critical(f"System health critical: {len(health.failed_agents)} agents failed")
                elif health.status == "degraded":
                    logger.warning(f"System health degraded: {len(health.failed_agents)} agents failed")
                else:
                    logger.info("System health check: All systems operational")
                
                # Log performance metrics
                for agent_name, perf in health.performance_metrics.items():
                    logger.info(f"{agent_name}: Success rate {perf.success_rate:.1%}, "
                              f"Avg time {perf.average_processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Health monitor error: {str(e)}")
                await asyncio.sleep(60)  # Shorter interval on error
    
    async def shutdown_system(self):
        """Gracefully shutdown the system"""
        try:
            logger.info("Shutting down Financial Multi-Agent System...")
            self.system_status = "shutting_down"
            
            # Cleanup all agents
            cleanup_tasks = []
            for agent_name, agent in self.agents.items():
                task = asyncio.create_task(agent.cleanup(), name=f"{agent_name}_cleanup")
                cleanup_tasks.append(task)
            
            # Wait for all cleanup tasks
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            self.system_status = "stopped"
            logger.info("System shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    async def get_workflow_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent workflow history"""
        return self.workflow_history[-limit:] if self.workflow_history else []
    
    def get_agent_info(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about agents"""
        if agent_name:
            if agent_name in self.agents:
                return self.agents[agent_name].get_agent_info()
            else:
                return {"error": f"Agent {agent_name} not found"}
        else:
            return {name: agent.get_agent_info() for name, agent in self.agents.items()}


# CLI Interface
@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--log-level', default='INFO', help='Logging level')
@click.pass_context
def cli(ctx, config, log_level):
    """Financial Multi-Agent System CLI"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['log_level'] = log_level
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))


@cli.command()
@click.option('--symbols', '-s', multiple=True, required=True, help='Stock symbols to analyze')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def analyze(ctx, symbols, output):
    """Analyze financial symbols"""
    async def run_analysis():
        system = FinancialMultiAgentSystem()
        
        try:
            # Start system in background
            system_task = asyncio.create_task(system.start_system())
            
            # Wait a moment for system to initialize
            await asyncio.sleep(2)
            
            # Run analysis
            results = await system.analyze_symbols(list(symbols))
            
            # Output results
            if output:
                import json
                with open(output, 'w') as f:
                    json.dump(results, f, indent=2)
                click.echo(f"Results saved to {output}")
            else:
                click.echo("Analysis Results:")
                for symbol, result in results['results'].items():
                    if 'error' in result:
                        click.echo(f"❌ {symbol}: {result['error']}")
                    else:
                        market = result['market_analysis']
                        risk = result['risk_assessment']
                        click.echo(f"✅ {symbol}: Price ${market['current_price']:.2f}, "
                                 f"Trend {market['trend_strength']}, "
                                 f"Risk {risk['risk_level']}")
            
            # Shutdown system
            await system.shutdown_system()
            system_task.cancel()
            
        except Exception as e:
            click.echo(f"Analysis failed: {str(e)}")
            await system.shutdown_system()
    
    asyncio.run(run_analysis())


@cli.command()
@click.pass_context
def market_summary(ctx):
    """Get market summary"""
    async def get_summary():
        system = FinancialMultiAgentSystem()
        
        try:
            # Start system
            system_task = asyncio.create_task(system.start_system())
            await asyncio.sleep(2)
            
            # Get market summary
            summary = await system.get_market_summary()
            
            if 'error' in summary:
                click.echo(f"Error: {summary['error']}")
            else:
                click.echo("Market Summary:")
                for index, data in summary.get('indices', {}).items():
                    change_color = "green" if data['change'] >= 0 else "red"
                    click.echo(f"{index}: ${data['current_price']:.2f} "
                             f"({data['change']:+.2f}, {data['change_percent']:+.1f}%)")
            
            # Shutdown
            await system.shutdown_system()
            system_task.cancel()
            
        except Exception as e:
            click.echo(f"Failed to get market summary: {str(e)}")
    
    asyncio.run(get_summary())


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    async def check_health():
        system = FinancialMultiAgentSystem()
        
        try:
            # Start system
            system_task = asyncio.create_task(system.start_system())
            await asyncio.sleep(2)
            
            # Check health
            health_status = await system.get_system_health()
            
            click.echo(f"System Status: {health_status.status}")
            click.echo(f"Active Agents: {', '.join(health_status.active_agents)}")
            if health_status.failed_agents:
                click.echo(f"Failed Agents: {', '.join(health_status.failed_agents)}")
            click.echo(f"Message Queue Size: {health_status.message_queue_size}")
            
            # Performance metrics
            click.echo("\nAgent Performance:")
            for agent_name, perf in health_status.performance_metrics.items():
                click.echo(f"  {agent_name}: {perf.success_rate:.1%} success, "
                         f"{perf.average_processing_time:.2f}s avg time")
            
            # Shutdown
            await system.shutdown_system()
            system_task.cancel()
            
        except Exception as e:
            click.echo(f"Health check failed: {str(e)}")
    
    asyncio.run(check_health())


@cli.command()
@click.option('--port', '-p', default=8000, help='Server port')
@click.option('--host', '-h', default='localhost', help='Server host')
@click.pass_context
def serve(ctx, port, host):
    """Start the system as a web service"""
    
    # Import FastAPI here to avoid dependency issues
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        import uvicorn
    except ImportError:
        click.echo("FastAPI not installed. Install with: pip install fastapi uvicorn")
        return
    
    app = FastAPI(title="Financial Multi-Agent System API", version="1.0.0")
    system = None
    
    @app.on_event("startup")
    async def startup():
        global system
        system = FinancialMultiAgentSystem()
        # Start system in background
        asyncio.create_task(system.start_system())
        await asyncio.sleep(2)  # Wait for initialization
    
    @app.on_event("shutdown")
    async def shutdown():
        if system:
            await system.shutdown_system()
    
    @app.get("/health")
    async def get_health():
        if not system:
            raise HTTPException(status_code=503, detail="System not initialized")
        health_status = await system.get_system_health()
        return health_status
    
    @app.get("/market-summary")
    async def get_market_summary():
        if not system:
            raise HTTPException(status_code=503, detail="System not initialized")
        summary = await system.get_market_summary()
        return summary
    
    @app.post("/analyze")
    async def analyze_symbols(symbols: List[str]):
        if not system:
            raise HTTPException(status_code=503, detail="System not initialized")
        
        if not symbols:
            raise HTTPException(status_code=400, detail="No symbols provided")
        
        try:
            results = await system.analyze_symbols(symbols)
            return results
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/agents")
    async def get_agents():
        if not system:
            raise HTTPException(status_code=503, detail="System not initialized")
        return system.get_agent_info()
    
    @app.get("/workflows")
    async def get_workflows():
        if not system:
            raise HTTPException(status_code=503, detail="System not initialized")
        return await system.get_workflow_history()
    
    click.echo(f"Starting Financial Multi-Agent System API on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.pass_context
def demo(ctx):
    """Run a demonstration of the system"""
    async def run_demo():
        click.echo("🚀 Financial Multi-Agent System Demo")
        click.echo("=" * 50)
        
        system = FinancialMultiAgentSystem()
        
        try:
            # Start system
            click.echo("Starting system...")
            system_task = asyncio.create_task(system.start_system())
            await asyncio.sleep(3)
            
            # Demo symbols
            demo_symbols = ["AAPL", "MSFT", "GOOGL"]
            click.echo(f"Analyzing demo symbols: {', '.join(demo_symbols)}")
            
            # Run analysis
            results = await system.analyze_symbols(demo_symbols)
            
            # Display results
            click.echo("\n📊 Analysis Results:")
            click.echo("-" * 30)
            
            for symbol, result in results['results'].items():
                if 'error' in result:
                    click.echo(f"❌ {symbol}: Analysis failed - {result['error']}")
                else:
                    market = result['market_analysis']
                    risk = result['risk_assessment']
                    
                    click.echo(f"\n📈 {symbol}:")
                    click.echo(f"  Price: ${market['current_price']:.2f}")
                    click.echo(f"  Trend: {market['trend_strength']}")
                    click.echo(f"  RSI: {market['rsi']:.1f}")
                    click.echo(f"  Risk Level: {risk['risk_level']}")
                    click.echo(f"  Volatility: {risk['volatility']:.1%}")
                    click.echo(f"  Sharpe Ratio: {risk['sharpe_ratio']:.2f}")
                    
                    if risk['risk_factors']:
                        click.echo(f"  Risk Factors: {len(risk['risk_factors'])} identified")
            
            # System health
            click.echo("\n🏥 System Health:")
            health = await system.get_system_health()
            click.echo(f"  Status: {health.status}")
            click.echo(f"  Active Agents: {len(health.active_agents)}")
            
            click.echo("\n✅ Demo completed successfully!")
            
            # Shutdown
            await system.shutdown_system()
            system_task.cancel()
            
        except Exception as e:
            click.echo(f"❌ Demo failed: {str(e)}")
            await system.shutdown_system()
    
    asyncio.run(run_demo())


if __name__ == "__main__":
    cli()
