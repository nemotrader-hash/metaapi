"""
MetaTrader 5 Market Data Module
==============================

This module provides comprehensive market data functions for retrieving
rates, ticks, symbol information, and other market-related data.
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union, Tuple, Any
import logging

from .constants import TIMEFRAME, TIMEFRAME_MAP, parse_timeframe, ORDER_TYPE
from .models import SymbolInfo, Tick, Rate, create_symbol_info, create_tick, create_rate
from log.logger import setup_logger
from .exceptions import MT5ConnectionError, MT5SymbolError

logger = setup_logger()


class MarketDataProvider:
    """Enhanced market data provider for MetaTrader 5"""
    
    def __init__(self):
        self._symbols_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_symbol_update = {}
    
    def get_rates(
        self, 
        symbol: str, 
        timeframe: Union[str, int], 
        count: int = 500,
        start_pos: int = 0
    ) -> Optional[pd.DataFrame]:
        """
        Get historical rates data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Chart timeframe (e.g., 'M1', 'H1', 'D1')
            count: Number of bars to retrieve
            start_pos: Start position from the last bar
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            tf = parse_timeframe(timeframe) if isinstance(timeframe, str) else timeframe
            
            rates = mt5.copy_rates_from_pos(symbol, tf, start_pos, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates data available for {symbol} {timeframe}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            logger.info(f"Retrieved {len(df)} bars for {symbol} {timeframe}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting rates for {symbol}: {e}")
            raise MT5ConnectionError(f"Failed to get rates data: {e}")
    
    def get_rates_range(
        self, 
        symbol: str, 
        timeframe: Union[str, int],
        date_from: datetime,
        date_to: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Get historical rates data for a specific date range.
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            date_from: Start date
            date_to: End date
            
        Returns:
            DataFrame with OHLCV data or None if error
        """
        try:
            tf = parse_timeframe(timeframe) if isinstance(timeframe, str) else timeframe
            
            rates = mt5.copy_rates_range(symbol, tf, date_from, date_to)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No rates data available for {symbol} {timeframe} from {date_from} to {date_to}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            logger.info(f"Retrieved {len(df)} bars for {symbol} {timeframe} range")
            return df
            
        except Exception as e:
            logger.error(f"Error getting rates range for {symbol}: {e}")
            raise MT5ConnectionError(f"Failed to get rates range: {e}")
    
    def get_ticks(
        self, 
        symbol: str, 
        count: int = 1000,
        from_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Get tick data for a symbol.
        
        Args:
            symbol: Trading symbol
            count: Number of ticks to retrieve
            from_date: Start date for ticks (optional)
            
        Returns:
            DataFrame with tick data or None if error
        """
        try:
            if from_date:
                ticks = mt5.copy_ticks_from(symbol, from_date, count, mt5.COPY_TICKS_ALL)
            else:
                ticks = mt5.copy_ticks_from_pos(symbol, 0, count, mt5.COPY_TICKS_ALL)
            
            if ticks is None or len(ticks) == 0:
                logger.warning(f"No tick data available for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ticks)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            logger.info(f"Retrieved {len(df)} ticks for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting ticks for {symbol}: {e}")
            raise MT5ConnectionError(f"Failed to get tick data: {e}")
    
    def get_symbol_info(self, symbol: str, use_cache: bool = True) -> Optional[SymbolInfo]:
        """
        Get detailed symbol information.
        
        Args:
            symbol: Trading symbol
            use_cache: Whether to use cached data
            
        Returns:
            SymbolInfo model or None if error
        """
        try:
            # Check cache first
            if use_cache and symbol in self._symbols_cache:
                cache_time = self._last_symbol_update.get(symbol, 0)
                if datetime.now().timestamp() - cache_time < self._cache_ttl:
                    return self._symbols_cache[symbol]
            
            symbol_info = mt5.symbol_info(symbol)
            
            if symbol_info is None:
                logger.warning(f"Symbol {symbol} not found")
                return None
            
            # Create SymbolInfo model
            symbol_model = create_symbol_info(symbol_info)
            
            # Cache the result
            if use_cache:
                self._symbols_cache[symbol] = symbol_model
                self._last_symbol_update[symbol] = datetime.now().timestamp()
            
            return symbol_model
            
        except Exception as e:
            logger.error(f"Error getting symbol info for {symbol}: {e}")
            raise MT5SymbolError(f"Failed to get symbol info: {e}")
    
    def get_symbol_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current tick information for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with current tick data or None if error
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            
            if tick is None:
                logger.warning(f"No tick data available for {symbol}")
                return None
            
            return {
                'symbol': symbol,
                'time': datetime.fromtimestamp(tick.time),
                'bid': tick.bid,
                'ask': tick.ask,
                'last': tick.last,
                'volume': tick.volume,
                'spread': tick.ask - tick.bid,
                'flags': tick.flags,
                'volume_real': tick.volume_real,
            }
            
        except Exception as e:
            logger.error(f"Error getting tick for {symbol}: {e}")
            return None
    
    def get_symbols_list(self, group: str = "*") -> List[str]:
        """
        Get list of available symbols.
        
        Args:
            group: Symbol group filter (e.g., "*", "Forex*", "*.US")
            
        Returns:
            List of symbol names
        """
        try:
            symbols = mt5.symbols_get(group)
            
            if symbols is None:
                logger.warning("No symbols available")
                return []
            
            return [symbol.name for symbol in symbols]
            
        except Exception as e:
            logger.error(f"Error getting symbols list: {e}")
            return []
    
    def calculate_margin(
        self, 
        symbol: str, 
        volume: float, 
        order_type: ORDER_TYPE,
        price: float = 0.0
    ) -> Optional[float]:
        """
        Calculate required margin for an order.
        
        Args:
            symbol: Trading symbol
            volume: Order volume
            order_type: Order type (`ORDER_TYPE.BUY` or `ORDER_TYPE.SELL`)
            price: Order price (current price if 0.0)
            
        Returns:
            Required margin amount or None if error
        """
        try:
            if price == 0.0:
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    return None
                price = tick.bid if order_type == ORDER_TYPE.SELL else tick.ask
            
            margin = mt5.order_calc_margin(int(order_type), symbol, volume, price)
            
            if margin is None:
                logger.warning(f"Could not calculate margin for {symbol}")
                return None
            
            return margin
            
        except Exception as e:
            logger.error(f"Error calculating margin for {symbol}: {e}")
            return None
    
    def calculate_profit(
        self, 
        symbol: str, 
        volume: float, 
        order_type: ORDER_TYPE,
        price_open: float,
        price_close: float
    ) -> Optional[float]:
        """
        Calculate profit for a trade.
        
        Args:
            symbol: Trading symbol
            volume: Trade volume
            order_type: Order type
            price_open: Opening price
            price_close: Closing price
            
        Returns:
            Profit amount or None if error
        """
        try:
            profit = mt5.order_calc_profit(int(order_type), symbol, volume, price_open, price_close)
            
            if profit is None:
                logger.warning(f"Could not calculate profit for {symbol}")
                return None
            
            return profit
            
        except Exception as e:
            logger.error(f"Error calculating profit for {symbol}: {e}")
            return None
    
    def get_market_book(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get market depth (order book) for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            DataFrame with market depth data or None if error
        """
        try:
            book = mt5.market_book_get(symbol)
            
            if book is None or len(book) == 0:
                logger.warning(f"No market book data available for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(book)
            df['symbol'] = symbol
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market book for {symbol}: {e}")
            return None
    
    def clear_cache(self):
        """Clear the symbols cache"""
        self._symbols_cache.clear()
        self._last_symbol_update.clear()
        logger.info("Symbol cache cleared")


# Global market data provider instance
market_data = MarketDataProvider()
