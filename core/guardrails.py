import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from .models import Recommendation, RiskAssessment, FinancialData
from .enums import RiskLevel, ValidationStatus, GuardrailType, ErrorSeverity

logger = logging.getLogger(__name__)


class GuardrailViolation(Exception):
    """Exception raised when a guardrail is violated"""
    def __init__(self, message: str, severity: ErrorSeverity, guardrail_type: GuardrailType):
        self.message = message
        self.severity = severity
        self.guardrail_type = guardrail_type
        super().__init__(self.message)


class FinancialGuardrails:
    """Comprehensive safety guardrails for financial analysis and recommendations"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize guardrails with configuration"""
        self.config = config or self._default_config()
        self.violation_history: List[GuardrailViolation] = []
        
    def _default_config(self) -> Dict[str, Any]:
        """Default guardrail configuration"""
        return {
            "max_position_size": 0.1,  # 10% of portfolio
            "max_leverage": 2.0,
            "min_liquidity_threshold": 1000000,  # $1M daily volume
            "max_volatility": 1.0,  # 100% annual volatility
            "min_data_quality": 0.3,
            "max_recommendation_age_hours": 24,
            "min_confidence_threshold": 0.2,
            "blacklisted_symbols": ["SCAM", "PUMP", "FAKE"],
            "risk_limits": {
                RiskLevel.LOW: {"max_allocation": 0.3},
                RiskLevel.MEDIUM: {"max_allocation": 0.2},
                RiskLevel.HIGH: {"max_allocation": 0.1},
                RiskLevel.CRITICAL: {"max_allocation": 0.05}
            },
            "data_freshness_hours": 4,
            "min_historical_data_points": 50
        }
    
    def validate_symbol(self, symbol: str) -> Tuple[ValidationStatus, List[str]]:
        """Validate if symbol is safe to analyze"""
        issues = []
        
        # Check if symbol is blacklisted
        if symbol.upper() in self.config["blacklisted_symbols"]:
            issues.append(f"Symbol {symbol} is blacklisted")
            self._log_violation(
                f"Blacklisted symbol attempted: {symbol}",
                ErrorSeverity.ERROR,
                GuardrailType.REGULATORY_COMPLIANCE
            )
            return ValidationStatus.FAILED, issues
        
        # Check symbol format
        if not isinstance(symbol, str) or len(symbol) > 6 or not symbol.replace('^', '').isalnum():
            issues.append(f"Invalid symbol format: {symbol}")
            return ValidationStatus.FAILED, issues
        
        # Check for suspicious patterns
        if len(set(symbol)) == 1:  # All same character
            issues.append(f"Suspicious symbol pattern: {symbol}")
            return ValidationStatus.WARNING, issues
        
        return ValidationStatus.PASSED, issues
    
    def validate_financial_data(self, data: FinancialData) -> Tuple[ValidationStatus, List[str]]:
        """Validate financial data quality and integrity"""
        issues = []
        
        # Check data quality score
        if data.data_quality < self.config["min_data_quality"]:
            issues.append(f"Data quality {data.data_quality:.2f} below minimum {self.config['min_data_quality']}")
        
        # Check data freshness
        try:
            data_timestamp = datetime.fromisoformat(data.timestamp)
            age_hours = (datetime.now() - data_timestamp).total_seconds() / 3600
            
            if age_hours > self.config["data_freshness_hours"]:
                issues.append(f"Data is {age_hours:.1f} hours old, exceeds {self.config['data_freshness_hours']} hour limit")
        except ValueError:
            issues.append("Invalid timestamp format in financial data")
        
        # Check data completeness
        if data.data.empty:
            issues.append("Financial data is empty")
            return ValidationStatus.FAILED, issues
        
        # Check minimum data points
        if len(data.data) < self.config["min_historical_data_points"]:
            issues.append(f"Insufficient data points: {len(data.data)} < {self.config['min_historical_data_points']}")
        
        # Check for suspicious data patterns
        if 'Close' in data.data.columns:
            close_prices = data.data['Close']
            
            # Check for constant prices (possible data issue)
            if close_prices.nunique() == 1:
                issues.append("All closing prices are identical - possible data error")
            
            # Check for extreme price movements
            daily_returns = close_prices.pct_change().dropna()
            if len(daily_returns) > 0:
                extreme_returns = daily_returns[abs(daily_returns) > 0.5]  # >50% daily change
                if len(extreme_returns) > 0:
                    issues.append(f"Detected {len(extreme_returns)} extreme daily returns (>50%)")
        
        # Check volume data if available
        if 'Volume' in data.data.columns:
            volumes = data.data['Volume']
            if volumes.sum() < self.config["min_liquidity_threshold"]:
                issues.append(f"Low liquidity: total volume {volumes.sum():,.0f}")
        
        # Determine overall status
        if any("empty" in issue or "Failed" in issue for issue in issues):
            return ValidationStatus.FAILED, issues
        elif issues:
            return ValidationStatus.WARNING, issues
        else:
            return ValidationStatus.PASSED, issues
    
    def validate_risk_assessment(self, risk_assessment: RiskAssessment) -> Tuple[ValidationStatus, List[str]]:
        """Validate risk assessment results"""
        issues = []
        
        # Check confidence level
        if risk_assessment.confidence < 0.1:
            issues.append(f"Risk assessment confidence too low: {risk_assessment.confidence:.2f}")
        
        # Check for reasonable risk metrics
        metrics = risk_assessment.risk_metrics
        
        # Volatility checks
        if metrics.volatility < 0 or metrics.volatility > self.config["max_volatility"]:
            issues.append(f"Unrealistic volatility: {metrics.volatility:.2%}")
        
        # VaR checks
        if metrics.var_95 > 0:  # VaR should be negative
            issues.append(f"Invalid VaR (should be negative): {metrics.var_95:.4f}")
        
        # Sharpe ratio checks
        if abs(metrics.sharpe_ratio) > 10:  # Extremely high Sharpe ratio is suspicious
            issues.append(f"Suspicious Sharpe ratio: {metrics.sharpe_ratio:.2f}")
        
        # Max drawdown checks
        if metrics.max_drawdown > 0:  # Drawdown should be negative
            issues.append(f"Invalid max drawdown (should be negative): {metrics.max_drawdown:.2%}")
        
        # Beta checks
        if metrics.beta < -5 or metrics.beta > 5:  # Extreme beta values
            issues.append(f"Extreme beta value: {metrics.beta:.2f}")
        
        # Check risk level consistency
        calculated_risk = self._calculate_risk_level_from_metrics(metrics)
        if calculated_risk != risk_assessment.risk_level:
            issues.append(f"Risk level inconsistency: calculated {calculated_risk.value}, assigned {risk_assessment.risk_level.value}")
        
        return ValidationStatus.WARNING if issues else ValidationStatus.PASSED, issues
    
    def validate_recommendation(self, recommendation: Recommendation) -> Tuple[ValidationStatus, List[str]]:
        """Validate investment recommendation safety"""
        issues = []
        
        # Check basic recommendation structure
        if recommendation.action not in ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]:
            issues.append(f"Invalid recommendation action: {recommendation.action}")
            return ValidationStatus.FAILED, issues
        
        # Check confidence level
        if recommendation.confidence < self.config["min_confidence_threshold"]:
            issues.append(f"Recommendation confidence too low: {recommendation.confidence:.2f}")
        
        if recommendation.confidence > 1.0:
            issues.append(f"Invalid confidence level (>1.0): {recommendation.confidence:.2f}")
        
        # Check price targets
        if recommendation.target_price is not None and recommendation.target_price <= 0:
            issues.append(f"Invalid target price: ${recommendation.target_price:.2f}")
        
        if recommendation.stop_loss is not None and recommendation.stop_loss <= 0:
            issues.append(f"Invalid stop loss: ${recommendation.stop_loss:.2f}")
        
        # Check stop loss vs target price logic
        if (recommendation.target_price is not None and 
            recommendation.stop_loss is not None):
            
            if recommendation.action in ["BUY", "STRONG_BUY"]:
                if recommendation.stop_loss > recommendation.target_price:
                    issues.append("Stop loss is higher than target price for BUY recommendation")
            elif recommendation.action in ["SELL", "STRONG_SELL"]:
                if recommendation.stop_loss < recommendation.target_price:
                    issues.append("Stop loss is lower than target price for SELL recommendation")
        
        # Check recommendation age
        try:
            rec_timestamp = datetime.fromisoformat(recommendation.recommendation_timestamp)
            age_hours = (datetime.now() - rec_timestamp).total_seconds() / 3600
            
            if age_hours > self.config["max_recommendation_age_hours"]:
                issues.append(f"Recommendation is {age_hours:.1f} hours old")
        except ValueError:
            issues.append("Invalid timestamp in recommendation")
        
        # Check for required reasoning
        if not recommendation.reasoning or len(recommendation.reasoning) < 10:
            issues.append("Insufficient reasoning provided")
        
        return ValidationStatus.WARNING if issues else ValidationStatus.PASSED, issues
    
    def validate_portfolio_allocation(self, recommendations: List[Recommendation]) -> Tuple[ValidationStatus, List[str]]:
        """Validate portfolio-level allocation constraints"""
        issues = []
        
        # Calculate total allocation by risk level
        risk_allocations = {level: 0.0 for level in RiskLevel}
        total_allocation = 0.0
        
        for rec in recommendations:
            if rec.action in ["BUY", "STRONG_BUY"]:
                # Estimate allocation (simplified - in practice, would use position sizes)
                allocation = self.config["max_position_size"]  # Default position size
                total_allocation += allocation
                
                # This would require risk assessment - simplified for now
                risk_level = RiskLevel.MEDIUM  # Default assumption
                risk_allocations[risk_level] += allocation
        
        # Check total allocation
        if total_allocation > 1.0:
            issues.append(f"Total allocation exceeds 100%: {total_allocation:.1%}")
        
        # Check risk level allocations
        for risk_level, allocation in risk_allocations.items():
            max_allowed = self.config["risk_limits"][risk_level]["max_allocation"]
            if allocation > max_allowed:
                issues.append(f"{risk_level.value} risk allocation {allocation:.1%} exceeds limit {max_allowed:.1%}")
        
        return ValidationStatus.WARNING if issues else ValidationStatus.PASSED, issues
    
    def check_data_quality(self, data: pd.DataFrame) -> float:
        """Check data quality and return a score between 0 and 1"""
        try:
            if data.empty:
                return 0.0
            
            quality_score = 1.0
            
            # Check for missing values
            missing_ratio = data.isnull().sum().sum() / (len(data) * len(data.columns))
            quality_score -= missing_ratio * 0.3
            
            # Check for sufficient data points
            if len(data) < 50:
                quality_score -= 0.2
            
            # Check for data completeness
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                quality_score -= len(missing_columns) * 0.1
            
            # Check for extreme values (likely data errors)
            if 'Close' in data.columns:
                price_changes = data['Close'].pct_change().dropna()
                extreme_changes = price_changes[abs(price_changes) > 0.5]  # >50% change
                if len(extreme_changes) > 0:
                    quality_score -= len(extreme_changes) * 0.05
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error checking data quality: {str(e)}")
            return 0.5  # Default middle score if error occurs
    
    def _calculate_risk_level_from_metrics(self, metrics) -> RiskLevel:
        """Calculate risk level based on metrics"""
        risk_score = 0
        
        # Volatility factor
        if metrics.volatility > 0.4:
            risk_score += 3
        elif metrics.volatility > 0.25:
            risk_score += 2
        elif metrics.volatility > 0.15:
            risk_score += 1
        
        # VaR factor
        if abs(metrics.var_95) > 0.05:
            risk_score += 3
        elif abs(metrics.var_95) > 0.03:
            risk_score += 2
        elif abs(metrics.var_95) > 0.02:
            risk_score += 1
        
        # Max drawdown factor
        if abs(metrics.max_drawdown) > 0.3:
            risk_score += 3
        elif abs(metrics.max_drawdown) > 0.2:
            risk_score += 2
        elif abs(metrics.max_drawdown) > 0.1:
            risk_score += 1
        
        # Determine risk level
        if risk_score >= 8:
            return RiskLevel.CRITICAL
        elif risk_score >= 6:
            return RiskLevel.HIGH
        elif risk_score >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _log_violation(self, message: str, severity: ErrorSeverity, guardrail_type: GuardrailType):
        """Log a guardrail violation"""
        violation = GuardrailViolation(message, severity, guardrail_type)
        self.violation_history.append(violation)
        
        log_func = getattr(logger, severity.value.lower(), logger.info)
        log_func(f"Guardrail violation ({guardrail_type.value}): {message}")
    
    def get_violation_summary(self) -> Dict[str, Any]:
        """Get summary of recent guardrail violations"""
        recent_violations = [
            v for v in self.violation_history 
            if (datetime.now() - datetime.fromisoformat(v.message)).days <= 7
        ]
        
        summary = {
            "total_violations": len(recent_violations),
            "by_severity": {},
            "by_type": {},
            "recent_violations": [
                {
                    "message": v.message,
                    "severity": v.severity.value,
                    "type": v.guardrail_type.value
                }
                for v in recent_violations[-10:]  # Last 10 violations
            ]
        }
        
        for violation in recent_violations:
            severity = violation.severity.value
            guardrail_type = violation.guardrail_type.value
            
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            summary["by_type"][guardrail_type] = summary["by_type"].get(guardrail_type, 0) + 1
        
        return summary
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update guardrail configuration"""
        self.config.update(new_config)
        logger.info("Guardrail configuration updated")
    
    def reset_violations(self):
        """Reset violation history"""
        self.violation_history.clear()
        logger.info("Guardrail violation history reset")

