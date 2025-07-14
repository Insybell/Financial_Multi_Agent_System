# core/models.py
"""
Data models for the Financial Multi-Agent System
Author: Zhang Weiling (Insybell)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
from .enums import RiskLevel, Priority, MessageType


@dataclass
class FinancialData:
    """Financial data structure for stock information"""
    symbol: str
    data: pd.DataFrame
    info: Dict[str, Any]
    timestamp: str
    data_quality: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechnicalIndicators:
    """Technical analysis indicators"""
    sma_20: float
    sma_50: float
    sma_200: float
    rsi: float
    macd: float
    macd_signal: float
    bb_upper: float
    bb_lower: float
    bb_middle: float
    volume_ratio: float


@dataclass
class MarketAnalysis:
    """Market analysis results"""
    symbol: str
    current_price: float
    trend_strength: str
    technical_indicators: TechnicalIndicators
    volume_analysis: Dict[str, float]
    support_resistance: Dict[str, float]
    data_quality: float
    analysis_timestamp: str


@dataclass
class RiskMetrics:
    """Risk calculation metrics"""
    var_95: float
    var_99: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    beta: float
    information_ratio: float
    sortino_ratio: float


@dataclass
class RiskAssessment:
    """Comprehensive risk assessment"""
    symbol: str
    risk_metrics: RiskMetrics
    risk_level: RiskLevel
    confidence: float
    risk_factors: List[str]
    assessment_timestamp: str
    methodology: str = "quantitative"


@dataclass
class Recommendation:
    """Investment recommendation"""
    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    reasoning: str
    target_price: Optional[float]
    stop_loss: Optional[float]
    time_horizon: str
    risk_factors: List[str]
    expected_return: Optional[float]
    recommendation_timestamp: str


@dataclass
class MCPMessage:
    """MCP protocol message structure"""
    message_type: MessageType
    source_agent: str
    target_agent: str
    data: Dict[str, Any]
    timestamp: str
    message_id: str
    priority: Priority
    correlation_id: Optional[str] = None


@dataclass
class AgentPerformance:
    """Agent performance metrics"""
    agent_name: str
    success_rate: float
    average_processing_time: float
    error_count: int
    last_execution: str
    total_executions: int


@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str  # healthy, degraded, critical
    active_agents: List[str]
    failed_agents: List[str]
    message_queue_size: int
    last_health_check: str
    performance_metrics: Dict[str, AgentPerformance]


@dataclass
class PortfolioAnalysis:
    """Portfolio-level analysis"""
    symbols: List[str]
    total_value: float
    diversification_score: float
    overall_risk_level: RiskLevel
    correlation_matrix: Dict[str, Dict[str, float]]
    recommended_actions: List[Recommendation]
    analysis_timestamp: str


@dataclass
class TriageResult:
    """Triage prioritization result"""
    symbol: str
    priority_score: float
    urgency_level: Priority
    reasoning: str
    recommended_agents: List[str]
    estimated_processing_time: int
    triage_timestamp: str


@dataclass
class ReportSection:
    """Individual report section"""
    title: str
    content: str
    charts: List[Dict[str, Any]]
    priority: Priority
    section_type: str  # executive_summary, analysis, recommendations, risks


@dataclass
class FinancialReport:
    """Comprehensive financial report"""
    report_id: str
    symbols: List[str]
    executive_summary: ReportSection
    market_analysis: ReportSection
    risk_assessment: ReportSection
    recommendations: ReportSection
    appendices: List[ReportSection]
    generation_timestamp: str
    report_type: str  # individual, portfolio, market_overview
    confidence_score: float
