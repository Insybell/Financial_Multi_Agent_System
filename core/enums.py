# core/enums.py
"""
Enumerations and constants for the Financial Multi-Agent System
Author: Zhang Weiling (Insybell)
"""

from enum import Enum, IntEnum


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(IntEnum):
    """Priority levels for message processing"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class MessageType(Enum):
    """Types of messages between agents"""
    DATA_COLLECTED = "data_collected"
    ANALYSIS_COMPLETE = "analysis_complete"
    RISK_ASSESSED = "risk_assessed"
    RECOMMENDATIONS_READY = "recommendations_ready"
    REPORT_GENERATED = "report_generated"
    TRIAGE_COMPLETE = "triage_complete"
    ERROR_OCCURRED = "error_occurred"
    HEALTH_CHECK = "health_check"
    WORKFLOW_COMPLETE = "workflow_complete"


class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class DataSource(Enum):
    """Available data sources"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"
    FRED = "fred"
    QUANDL = "quandl"


class AssetClass(Enum):
    """Asset classification"""
    EQUITY = "equity"
    BOND = "bond"
    COMMODITY = "commodity"
    CURRENCY = "currency"
    CRYPTOCURRENCY = "cryptocurrency"
    DERIVATIVE = "derivative"
    REAL_ESTATE = "real_estate"


class MarketTrend(Enum):
    """Market trend directions"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"
    CONSOLIDATING = "consolidating"


class RecommendationAction(Enum):
    """Investment recommendation actions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class TimeHorizon(Enum):
    """Investment time horizons"""
    SHORT_TERM = "1-3 months"
    MEDIUM_TERM = "3-12 months"
    LONG_TERM = "1-3 years"
    VERY_LONG_TERM = "3+ years"


class AnalysisType(Enum):
    """Types of financial analysis"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    QUANTITATIVE = "quantitative"
    SENTIMENT = "sentiment"
    MACRO_ECONOMIC = "macro_economic"


class GuardrailType(Enum):
    """Types of safety guardrails"""
    DATA_VALIDATION = "data_validation"
    RISK_LIMIT = "risk_limit"
    POSITION_SIZE = "position_size"
    LEVERAGE_LIMIT = "leverage_limit"
    LIQUIDITY_CHECK = "liquidity_check"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


class ErrorSeverity(Enum):
    """Error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ReportFormat(Enum):
    """Report output formats"""
    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"


class ValidationStatus(Enum):
    """Validation status for data and recommendations"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"
    SKIPPED = "skipped"


# Constants
DEFAULT_TIMEFRAMES = {
    "1D": "1 day",
    "5D": "5 days", 
    "1M": "1 month",
    "3M": "3 months",
    "6M": "6 months",
    "1Y": "1 year",
    "2Y": "2 years",
    "5Y": "5 years",
    "10Y": "10 years",
    "MAX": "maximum available"
}

RISK_THRESHOLDS = {
    RiskLevel.LOW: {"volatility": 0.15, "var_95": 0.02, "max_drawdown": 0.1},
    RiskLevel.MEDIUM: {"volatility": 0.25, "var_95": 0.03, "max_drawdown": 0.2},
    RiskLevel.HIGH: {"volatility": 0.4, "var_95": 0.05, "max_drawdown": 0.3},
    RiskLevel.CRITICAL: {"volatility": float('inf'), "var_95": float('inf'), "max_drawdown": float('inf')}
}

TECHNICAL_INDICATORS_CONFIG = {
    "sma_periods": [20, 50, 200],
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2
}

AGENT_TIMEOUTS = {
    "data_collection": 30,  # seconds
    "business_intelligence": 60,
    "risk_assessment": 45,
    "recommendation": 30,
    "report_generation": 120,
    "triage": 15
}
