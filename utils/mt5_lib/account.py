"""
MetaTrader 5 Account Monitoring Module
=====================================

This module provides comprehensive account monitoring, position tracking,
and portfolio analysis functions.
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union, Tuple, Any
import logging
import time

from .constants import POSITION_TYPE, DEAL_TYPE, DEAL_ENTRY
from .models import (
    AccountInfo, Position, Order, Deal, PortfolioSummary,
    create_account_info, create_position, create_order, create_deal
)
from log.logger import setup_logger
from .exceptions import MT5ConnectionError, MT5TradingError

logger = setup_logger()


class AccountMonitor:
    """Enhanced account monitoring and analysis"""
    
    def __init__(self):
        self._last_account_update = 0
        self._account_cache = {}
        self._cache_ttl = 30  # 30 seconds cache for account info
    
    def get_account_info(self, use_cache: bool = True) -> Optional[AccountInfo]:
        """
        Get detailed account information.
        
        Args:
            use_cache: Whether to use cached data
            
        Returns:
            AccountInfo model or None if error
        """
        try:
            # Check cache first
            if use_cache and self._account_cache:
                if time.time() - self._last_account_update < self._cache_ttl:
                    return self._account_cache
            
            account_info = mt5.account_info()
            if account_info is None:
                logger.warning("Could not get account information")
                return None
            
            # Create AccountInfo model (includes automatic calculations)
            account_model = create_account_info(account_info)
            
            # Cache the result
            if use_cache:
                self._account_cache = account_model
                self._last_account_update = time.time()
            
            return account_model
            
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            raise MT5ConnectionError(f"Failed to get account info: {e}")
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """
        Get all open positions with detailed information.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of Position models
        """
        try:
            positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
            
            if positions is None:
                positions = []
            
            position_list = []
            for pos in positions:
                position_model = create_position(pos)
                if position_model:
                    position_list.append(position_model)
            
            logger.info(f"Retrieved {len(position_list)} positions")
            return position_list
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise MT5ConnectionError(f"Failed to get positions: {e}")
    
    def get_orders(self, symbol: str = None) -> List[Order]:
        """
        Get all pending orders with detailed information.
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of Order models
        """
        try:
            orders = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
            
            if orders is None:
                orders = []
            
            order_list = []
            for order in orders:
                order_model = create_order(order)
                if order_model:
                    order_list.append(order_model)
            
            logger.info(f"Retrieved {len(order_list)} orders")
            return order_list
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            raise MT5ConnectionError(f"Failed to get orders: {e}")
    
    def get_deals_history(
        self,
        date_from: datetime = None,
        date_to: datetime = None,
        symbol: str = None,
        position_ticket: int = None
    ) -> List[Deal]:
        """
        Get trade history (deals) with detailed information.
        
        Args:
            date_from: Start date (default: last 30 days)
            date_to: End date (default: now)
            symbol: Filter by symbol (optional)
            position_ticket: Filter by position ticket (optional)
            
        Returns:
            List of Deal models
        """
        try:
            # Set default dates
            if date_to is None:
                date_to = datetime.now()
            if date_from is None:
                date_from = date_to - timedelta(days=30)
            
            # Get deals based on parameters
            if position_ticket:
                deals = mt5.history_deals_get(position=position_ticket)
            elif symbol:
                deals = mt5.history_deals_get(date_from, date_to, group=symbol)
            else:
                deals = mt5.history_deals_get(date_from, date_to)
            
            if deals is None:
                deals = []
            
            deal_list = []
            for deal in deals:
                deal_model = create_deal(deal)
                if deal_model:
                    deal_list.append(deal_model)
            
            logger.info(f"Retrieved {len(deal_list)} deals")
            return deal_list
            
        except Exception as e:
            logger.error(f"Error getting deals history: {e}")
            raise MT5ConnectionError(f"Failed to get deals history: {e}")
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """
        Get comprehensive portfolio summary and statistics.
        
        Returns:
            PortfolioSummary model with portfolio analysis
        """
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()
            orders = self.get_orders()
            
            if not account_info:
                raise MT5ConnectionError("Could not get account information")
            
            # Calculate position statistics
            total_positions = len(positions)
            long_positions = sum(1 for pos in positions if pos.type_string == 'BUY')
            short_positions = sum(1 for pos in positions if pos.type_string == 'SELL')
            total_volume = sum(pos.volume for pos in positions)
            total_profit = sum(pos.profit for pos in positions)
            
            # Calculate symbol distribution
            symbol_distribution = {}
            for pos in positions:
                symbol = pos.symbol
                if symbol not in symbol_distribution:
                    symbol_distribution[symbol] = {
                        'positions': 0,
                        'volume': 0,
                        'profit': 0
                    }
                symbol_distribution[symbol]['positions'] += 1
                symbol_distribution[symbol]['volume'] += pos.volume
                symbol_distribution[symbol]['profit'] += pos.profit
            
            # Count order types
            order_types = {}
            for order in orders:
                order_type = order.type_string
                order_types[order_type] = order_types.get(order_type, 0) + 1
            
            # Create PortfolioSummary model
            portfolio_summary = PortfolioSummary(
                account_info=account_info.to_dict(),
                positions_summary={
                    'total_positions': total_positions,
                    'long_positions': long_positions,
                    'short_positions': short_positions,
                    'total_volume': total_volume,
                    'total_profit': total_profit,
                    'avg_profit_per_position': total_profit / total_positions if total_positions > 0 else 0,
                },
                orders_summary={
                    'total_orders': len(orders),
                    'order_types': order_types,
                },
                risk_metrics={
                    'margin_used_percent': account_info.margin_used_percent,
                    'drawdown_percent': account_info.drawdown_percent,
                    'profit_percent': (total_profit / account_info.balance * 100) if account_info.balance > 0 else 0,
                    'leverage_utilization': (account_info.margin / account_info.equity * account_info.leverage) if account_info.equity > 0 else 0,
                },
                symbol_distribution=symbol_distribution,
                timestamp=datetime.now()
            )
            
            return portfolio_summary
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            raise MT5ConnectionError(f"Failed to get portfolio summary: {e}")
    
    
    def clear_cache(self):
        """Clear the account cache"""
        self._account_cache.clear()
        self._last_account_update = 0
        logger.info("Account cache cleared")


# Global account monitor instance
account_monitor = AccountMonitor()
