import asyncio
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from ..core.base_agent import BaseFinancialAgent
from ..core.models import FinancialData
from ..core.enums import MessageType, Priority, DataSource, ValidationStatus

logger = logging.getLogger(__name__)


class DataCollectionAgent(BaseFinancialAgent):
    """Agent responsible for collecting and validating financial data"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("DataCollectionAgent", config)
        self.cache = {}
        self.data_sources = {
            DataSource.YAHOO_FINANCE: self._fetch_yahoo_data,
            # Can add more data sources here
        }
        self.cache_ttl_hours = self.config.get("cache_ttl_hours", 1)
        
    async def collect_stock_data(self, symbol: str, period: str = "1y", 
                                source: DataSource = DataSource.YAHOO_FINANCE) -> FinancialData:
        """Collect stock data with validation and caching"""
        try:
            await self.log_activity(f"Starting data collection for {symbol}")
            
            # Validate symbol first
            validation_status, issues = self.guardrails.validate_symbol(symbol)
            if validation_status == ValidationStatus.FAILED:
                raise ValueError(f"Symbol validation failed: {', '.join(issues)}")
            
            # Check cache first
            cache_key = f"{symbol}_{period}_{source.value}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                await self.log_activity(f"Using cached data for {symbol}")
                return cached_data
            
            # Fetch from data source
            if source not in self.data_sources:
                raise ValueError(f"Unsupported data source: {source}")
            
            financial_data = await self.data_sources[source](symbol, period)
            
            # Validate the collected data
            validation_status, issues = self.guardrails.validate_financial_data(financial_data)
            if validation_status == ValidationStatus.FAILED:
                raise ValueError(f"Data validation failed: {', '.join(issues)}")
            
            if issues:  # Log warnings
                await self.log_activity(f"Data validation warnings for {symbol}: {', '.join(issues)}", "warning")
            
            # Cache the data
            self._cache_data(cache_key, financial_data)
            
            await self.log_activity(
                f"Successfully collected data for {symbol}",
                data={
                    "records": len(financial_data.data),
                    "quality": financial_data.data_quality,
                    "source": financial_data.source
                }
            )
            
            return financial_data
            
        except Exception as e:
            await self.log_activity(f"Failed to collect data for {symbol}: {str(e)}", "error")
            raise
    
    async def _fetch_yahoo_data(self, symbol: str, period: str) -> FinancialData:
        """Fetch data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            hist_data = ticker.history(period=period)
            if hist_data.empty:
                raise ValueError(f"No historical data available for {symbol}")
            
            # Fetch company info
            try:
                info = ticker.info
            except Exception as e:
                logger.warning(f"Could not fetch info for {symbol}: {str(e)}")
                info = {"symbol": symbol, "error": "Info not available"}
            
            # Calculate data quality
            data_quality = self.guardrails.check_data_quality(hist_data)
            
            financial_data = FinancialData(
                symbol=symbol,
                data=hist_data,
                info=info,
                timestamp=datetime.now().isoformat(),
                data_quality=data_quality,
                source="yahoo_finance",
                metadata={
                    "period": period,
                    "records_count": len(hist_data),
                    "date_range": {
                        "start": str(hist_data.index[0].date()),
                        "end": str(hist_data.index[-1].date())
                    }
                }
            )
            
            return financial_data
            
        except Exception as e:
            logger.error(f"Yahoo Finance fetch error for {symbol}: {str(e)}")
            raise
    
    def _get_cached_data(self, cache_key: str) -> Optional[FinancialData]:
        """Get data from cache if still valid"""
        if cache_key not in self.cache:
            return None
        
        cached_item = self.cache[cache_key]
        cache_timestamp = datetime.fromisoformat(cached_item["timestamp"])
        
        # Check if cache is still valid
        if (datetime.now() - cache_timestamp).total_seconds() / 3600 < self.cache_ttl_hours:
            return cached_item["data"]
        else:
            # Remove expired cache
            del self.cache[cache_key]
            return None
    
    def _cache_data(self, cache_key: str, data: FinancialData):
        """Cache financial data"""
        self.cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Limit cache size
        max_cache_size = self.config.get("max_cache_size", 100)
        if len(self.cache) > max_cache_size:
            # Remove oldest entries
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
    
    async def collect_multiple_symbols(self, symbols: List[str], 
                                     period: str = "1y") -> List[FinancialData]:
        """Collect data for multiple symbols concurrently"""
        await self.log_activity(f"Starting batch collection for {len(symbols)} symbols")
        
        # Create tasks for concurrent execution
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(
                self._collect_single_with_retry(symbol, period)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Separate successful results from errors
        successful_data = []
        failed_symbols = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_symbols.append(symbols[i])
                logger.error(f"Failed to collect data for {symbols[i]}: {str(result)}")
            else:
                successful_data.append(result)
        
        await self.log_activity(
            f"Batch collection completed",
            data={
                "requested": len(symbols),
                "successful": len(successful_data),
                "failed": len(failed_symbols),
                "failed_symbols": failed_symbols
            }
        )
        
        return successful_data
    
    async def _collect_single_with_retry(self, symbol: str, period: str, 
                                       max_retries: int = 3) -> FinancialData:
        """Collect data for a single symbol with retry logic"""
        for attempt in range(max_retries):
            try:
                return await self.collect_stock_data(symbol, period)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                
                wait_time = 2 ** attempt  # Exponential backoff
                await self.log_activity(
                    f"Retry {attempt + 1} for {symbol} in {wait_time}s: {str(e)}", 
                    "warning"
                )
                await asyncio.sleep(wait_time)
    
    async def get_market_summary(self, indices: List[str] = None) -> Dict[str, Any]:
        """Get market summary for major indices"""
        if indices is None:
            indices = ["^GSPC", "^DJI", "^IXIC", "^RUT"]  # S&P500, Dow, Nasdaq, Russell 2000
        
        try:
            market_data = await self.collect_multiple_symbols(indices, period="5d")
            
            summary = {
                "timestamp": datetime.now().isoformat(),
                "indices": {}
            }
            
            for data in market_data:
                if not data.data.empty:
                    latest = data.data.iloc[-1]
                    previous = data.data.iloc[-2] if len(data.data) > 1 else latest
                    
                    change = latest['Close'] - previous['Close']
                    change_pct = (change / previous['Close']) * 100
                    
                    summary["indices"][data.symbol] = {
                        "current_price": float(latest['Close']),
                        "change": float(change),
                        "change_percent": float(change_pct),
                        "volume": int(latest['Volume']),
                        "high": float(latest['High']),
                        "low": float(latest['Low'])
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting market summary: {str(e)}")
            raise
    
    async def process(self, input_data: Dict[str, Any]) -> List[FinancialData]:
        """Main processing method for the agent"""
        try:
            symbols = input_data.get('symbols', [])
            period = input_data.get('period', '1y')
            
            if not symbols:
                raise ValueError("No symbols provided for data collection")
            
            # Collect data for all symbols
            collected_data = await self.collect_multiple_symbols(symbols, period)
            
            # Send data to next agent(s) in the pipeline
            for data in collected_data:
                await self.send_mcp_message(
                    target_agent="BusinessIntelligenceAgent",
                    message_type=MessageType.DATA_COLLECTED,
                    data={'financial_data': self._serialize_financial_data(data)},
                    priority=Priority.MEDIUM
                )
            
            return collected_data
            
        except Exception as e:
            await self.log_activity(f"Processing failed: {str(e)}", "error")
            raise
    
    def _serialize_financial_data(self, data: FinancialData) -> Dict[str, Any]:
        """Serialize FinancialData for MCP message transmission"""
        return {
            'symbol': data.symbol,
            'data': data.data.to_dict('index'),  # Convert DataFrame to dict
            'info': data.info,
            'timestamp': data.timestamp,
            'data_quality': data.data_quality,
            'source': data.source,
            'metadata': data.metadata
        }
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "stock_data_collection",
            "market_data_validation",
            "multi_source_aggregation",
            "real_time_data_caching",
            "batch_symbol_processing",
            "market_summary_generation",
            "data_quality_assessment"
        ]
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_items = len(self.cache)
        total_size = sum(len(str(item)) for item in self.cache.values())
        
        # Calculate age distribution
        now = datetime.now()
        age_distribution = {"0-1h": 0, "1-6h": 0, "6h+": 0}
        
        for item in self.cache.values():
            age_hours = (now - datetime.fromisoformat(item["timestamp"])).total_seconds() / 3600
            if age_hours < 1:
                age_distribution["0-1h"] += 1
            elif age_hours < 6:
                age_distribution["1-6h"] += 1
            else:
                age_distribution["6h+"] += 1
        
        return {
            "total_items": total_items,
            "estimated_size_bytes": total_size,
            "ttl_hours": self.cache_ttl_hours,
            "age_distribution": age_distribution,
            "hit_rate": getattr(self, '_cache_hit_rate', 0.0)
        }
    
    async def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for specific symbol or all data"""
        if symbol:
            # Clear cache for specific symbol
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(symbol)]
            for key in keys_to_remove:
                del self.cache[key]
            await self.log_activity(f"Cleared cache for symbol: {symbol}")
        else:
            # Clear all cache
            self.cache.clear()
            await self.log_activity("Cleared all cache data")
    
    async def validate_data_sources(self) -> Dict[str, bool]:
        """Validate connectivity to all configured data sources"""
        results = {}
        
        for source in self.data_sources:
            try:
                # Test with a known symbol
                test_data = await self.data_sources[source]("AAPL", "5d")
                results[source.value] = test_data is not None and not test_data.data.empty
            except Exception as e:
                logger.error(f"Data source validation failed for {source.value}: {str(e)}")
                results[source.value] = False
        
        return results
