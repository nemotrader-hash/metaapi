"""
MetaTrader 5 Data Models
========================

Comprehensive data models for all MT5 operations based on the official
MetaTrader 5 Python API documentation.
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    # Mock MT5 constants for development/testing
    class MockMT5:
        TRADE_RETCODE_DONE = 10009
        TRADE_RETCODE_REQUOTE = 10004
        TRADE_RETCODE_REJECT = 10006
        # Add other constants as needed
    mt5 = MockMT5()
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Union, List, Dict, Tuple, Any
from enum import Enum

from .constants import ORDER_TYPE, POSITION_TYPE, DEAL_TYPE, TRADE_ACTION, get_error_description


@dataclass
class BaseModel:
    """Base model with common functionality for all MT5 models."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create model instance from dictionary."""
        if data is None:
            return None
        # Filter out keys that don't match the dataclass fields
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        return cls(**filtered_data)
    
    @classmethod
    def from_mt5_struct(cls, mt5_struct):
        """Create model instance from MT5 named tuple."""
        if mt5_struct is None:
            return None
        return cls.from_dict(mt5_struct._asdict())


@dataclass
class AccountInfo(BaseModel):
    """Account information model based on mt5.account_info()."""
    login: Optional[int] = None
    trade_mode: Optional[int] = None
    leverage: Optional[int] = None
    limit_orders: Optional[int] = None
    margin_so_mode: Optional[int] = None
    trade_allowed: Optional[bool] = None
    trade_expert: Optional[bool] = None
    margin_mode: Optional[int] = None
    currency_digits: Optional[int] = None
    fifo_close: Optional[bool] = None
    
    # Financial information
    balance: Optional[float] = None
    credit: Optional[float] = None
    profit: Optional[float] = None
    equity: Optional[float] = None
    margin: Optional[float] = None
    margin_free: Optional[float] = None
    margin_level: Optional[float] = None
    margin_so_call: Optional[float] = None
    margin_so_so: Optional[float] = None
    margin_initial: Optional[float] = None
    margin_maintenance: Optional[float] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    commission_blocked: Optional[float] = None
    
    # Account details
    name: Optional[str] = None
    server: Optional[str] = None
    currency: Optional[str] = None
    company: Optional[str] = None
    
    # Calculated fields
    drawdown_absolute: Optional[float] = field(init=False, default=None)
    drawdown_percent: Optional[float] = field(init=False, default=None)
    margin_used_percent: Optional[float] = field(init=False, default=None)
    account_value: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.balance is not None and self.equity is not None:
            self.drawdown_absolute = self.balance - self.equity
            self.drawdown_percent = (self.drawdown_absolute / self.balance * 100) if self.balance > 0 else 0
        
        if self.margin is not None and self.equity is not None and self.equity > 0:
            self.margin_used_percent = (self.margin / self.equity * 100)
        
        if self.balance is not None and self.credit is not None:
            self.account_value = self.balance + self.credit


@dataclass
class SymbolInfo(BaseModel):
    """Symbol information model based on mt5.symbol_info()."""
    # Basic symbol information
    name: Optional[str] = None
    description: Optional[str] = None
    path: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    
    # Currency information
    currency_base: Optional[str] = None
    currency_profit: Optional[str] = None
    currency_margin: Optional[str] = None
    
    # Price information
    digits: Optional[int] = None
    point: Optional[float] = None
    spread: Optional[int] = None
    spread_float: Optional[bool] = None
    
    # Volume information
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None
    volume_step: Optional[float] = None
    volume_limit: Optional[float] = None
    
    # Margin information
    margin_initial: Optional[float] = None
    margin_maintenance: Optional[float] = None
    
    # Trade information
    trade_tick_value: Optional[float] = None
    trade_tick_value_profit: Optional[float] = None
    trade_tick_value_loss: Optional[float] = None
    trade_tick_size: Optional[float] = None
    trade_contract_size: Optional[float] = None
    trade_mode: Optional[int] = None
    trade_execution: Optional[int] = None
    
    # Swap information
    swap_long: Optional[float] = None
    swap_short: Optional[float] = None
    swap_sunday: Optional[float] = None
    swap_monday: Optional[float] = None
    swap_tuesday: Optional[float] = None
    swap_wednesday: Optional[float] = None
    swap_thursday: Optional[float] = None
    swap_friday: Optional[float] = None
    swap_saturday: Optional[float] = None
    
    # Status
    visible: Optional[bool] = None
    select: Optional[bool] = None
    
    # Session information
    session_deals: Optional[int] = None
    session_buy_orders: Optional[int] = None
    session_sell_orders: Optional[int] = None
    session_turnover: Optional[float] = None
    session_interest: Optional[float] = None
    session_buy_orders_volume: Optional[float] = None
    session_sell_orders_volume: Optional[float] = None
    session_open: Optional[float] = None
    session_close: Optional[float] = None
    session_aw: Optional[float] = None
    session_price_settlement: Optional[float] = None
    session_price_limit_min: Optional[float] = None
    session_price_limit_max: Optional[float] = None


@dataclass
class TerminalInfo(BaseModel):
    """Terminal information model based on mt5.terminal_info()."""
    # Connection status
    community_account: Optional[bool] = None
    community_connection: Optional[bool] = None
    connected: Optional[bool] = None
    
    # Permissions
    dlls_allowed: Optional[bool] = None
    trade_allowed: Optional[bool] = None
    tradeapi_disabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    ftp_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    
    # Technical information
    mqid: Optional[bool] = None
    build: Optional[int] = None
    maxbars: Optional[int] = None
    codepage: Optional[int] = None
    ping_last: Optional[int] = None
    community_balance: Optional[float] = None
    retransmission: Optional[float] = None
    
    # Terminal details
    company: Optional[str] = None
    name: Optional[str] = None
    language: Optional[int] = None
    path: Optional[str] = None
    data_path: Optional[str] = None
    commondata_path: Optional[str] = None


@dataclass
class TradeRequest(BaseModel):
    """Trade request model for order operations."""
    action: Optional[int] = None
    magic: Optional[int] = None
    order: Optional[int] = None
    symbol: Optional[str] = None
    volume: Optional[float] = None
    price: Optional[float] = None
    stoplimit: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: Optional[int] = None
    type: Optional[int] = None
    type_filling: Optional[int] = None
    type_time: Optional[int] = None
    expiration: Optional[int] = None
    comment: Optional[str] = None
    position: Optional[int] = None
    position_by: Optional[int] = None


@dataclass
class TradeResult(BaseModel):
    """Trade result model from order operations."""
    retcode: Optional[int] = None
    deal: Optional[int] = None
    order: Optional[int] = None
    volume: Optional[float] = None
    price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    comment: Optional[str] = None
    request_id: Optional[int] = None
    retcode_external: Optional[int] = None
    
    # Additional computed fields
    success: Optional[bool] = field(init=False, default=None)
    retcode_description: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.retcode is not None:
            self.success = self.retcode == mt5.TRADE_RETCODE_DONE
            self.retcode_description = self._get_retcode_description(self.retcode)
    
    def _get_retcode_description(self, retcode: int) -> str:
        """Get human-readable description for trade return codes."""
        descriptions = {
            mt5.TRADE_RETCODE_REQUOTE: "Requote",
            mt5.TRADE_RETCODE_REJECT: "Request rejected",
            mt5.TRADE_RETCODE_CANCEL: "Request canceled by trader",
            mt5.TRADE_RETCODE_PLACED: "Order placed",
            mt5.TRADE_RETCODE_DONE: "Request completed",
            mt5.TRADE_RETCODE_DONE_PARTIAL: "Request partially completed",
            mt5.TRADE_RETCODE_ERROR: "Request processing error",
            mt5.TRADE_RETCODE_TIMEOUT: "Request canceled by timeout",
            mt5.TRADE_RETCODE_INVALID: "Invalid request",
            mt5.TRADE_RETCODE_INVALID_VOLUME: "Invalid volume in the request",
            mt5.TRADE_RETCODE_INVALID_PRICE: "Invalid price in the request",
            mt5.TRADE_RETCODE_INVALID_STOPS: "Invalid stops in the request",
            mt5.TRADE_RETCODE_TRADE_DISABLED: "Trade is disabled",
            mt5.TRADE_RETCODE_MARKET_CLOSED: "Market is closed",
            mt5.TRADE_RETCODE_NO_MONEY: "There is not enough money to complete the request",
            mt5.TRADE_RETCODE_PRICE_CHANGED: "Prices changed",
            mt5.TRADE_RETCODE_PRICE_OFF: "There are no quotes to process the request",
            mt5.TRADE_RETCODE_INVALID_EXPIRATION: "Invalid order expiration date",
            mt5.TRADE_RETCODE_ORDER_CHANGED: "Order state changed",
            mt5.TRADE_RETCODE_TOO_MANY_REQUESTS: "Too frequent requests",
            mt5.TRADE_RETCODE_NO_CHANGES: "No changes in request",
            mt5.TRADE_RETCODE_SERVER_DISABLES_AT: "Autotrading disabled by server",
            mt5.TRADE_RETCODE_CLIENT_DISABLES_AT: "Autotrading disabled by client terminal",
            mt5.TRADE_RETCODE_LOCKED: "Request locked for processing",
            mt5.TRADE_RETCODE_FROZEN: "Order or position frozen",
            mt5.TRADE_RETCODE_INVALID_FILL: "Invalid order filling type",
            mt5.TRADE_RETCODE_CONNECTION: "No connection with the trade server",
            mt5.TRADE_RETCODE_ONLY_REAL: "Operation is allowed only for live accounts",
            mt5.TRADE_RETCODE_LIMIT_ORDERS: "The number of pending orders has reached the limit",
            mt5.TRADE_RETCODE_LIMIT_VOLUME: "The volume of orders and positions for the symbol has reached the limit",
            mt5.TRADE_RETCODE_INVALID_ORDER: "Incorrect or prohibited order type",
            mt5.TRADE_RETCODE_POSITION_CLOSED: "Position with the specified identifier has already been closed",
        }
        return descriptions.get(retcode, f"Unknown return code: {retcode}")


@dataclass
class OrderCheckResult(BaseModel):
    """Wrapper for mt5.order_check result with convenience fields."""
    retcode: Optional[int] = None
    comment: Optional[str] = None
    request_id: Optional[int] = None
    margin_free: Optional[float] = None
    margin: Optional[float] = None
    price: Optional[float] = None
    volume: Optional[float] = None
    # Computed
    success: Optional[bool] = field(init=False, default=None)
    retcode_description: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        if self.retcode is not None:
            self.success = self.retcode == 0
            self.retcode_description = get_error_description(self.retcode)


@dataclass
class Position(BaseModel):
    """Position model based on mt5.positions_get()."""
    ticket: Optional[int] = None
    time: Optional[int] = None
    time_msc: Optional[int] = None
    time_update: Optional[int] = None
    time_update_msc: Optional[int] = None
    type: Optional[int] = None
    magic: Optional[int] = None
    identifier: Optional[int] = None
    reason: Optional[int] = None
    volume: Optional[float] = None
    price_open: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    price_current: Optional[float] = None
    swap: Optional[float] = None
    profit: Optional[float] = None
    symbol: Optional[str] = None
    comment: Optional[str] = None
    external_id: Optional[str] = None
    
    # Calculated fields
    time_datetime: Optional[datetime] = field(init=False, default=None)
    time_update_datetime: Optional[datetime] = field(init=False, default=None)
    type_string: Optional[str] = field(init=False, default=None)
    duration_seconds: Optional[float] = field(init=False, default=None)
    duration_hours: Optional[float] = field(init=False, default=None)
    duration_days: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.time is not None:
            self.time_datetime = datetime.fromtimestamp(self.time)
            self.duration_seconds = datetime.now().timestamp() - self.time
            self.duration_hours = self.duration_seconds / 3600
            self.duration_days = self.duration_seconds / 86400
        
        if self.time_update is not None:
            self.time_update_datetime = datetime.fromtimestamp(self.time_update)
        
        if self.type is not None:
            self.type_string = "BUY" if self.type == POSITION_TYPE.BUY else "SELL"


@dataclass
class Order(BaseModel):
    """Order model based on mt5.orders_get()."""
    ticket: Optional[int] = None
    time_setup: Optional[int] = None
    time_setup_msc: Optional[int] = None
    time_done: Optional[int] = None
    time_done_msc: Optional[int] = None
    time_expiration: Optional[int] = None
    type: Optional[int] = None
    state: Optional[int] = None
    type_filling: Optional[int] = None
    type_time: Optional[int] = None
    magic: Optional[int] = None
    reason: Optional[int] = None
    position_id: Optional[int] = None
    position_by_id: Optional[int] = None
    volume_initial: Optional[float] = None
    volume_current: Optional[float] = None
    price_open: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    price_current: Optional[float] = None
    price_stoplimit: Optional[float] = None
    symbol: Optional[str] = None
    comment: Optional[str] = None
    external_id: Optional[str] = None
    
    # Calculated fields
    time_setup_datetime: Optional[datetime] = field(init=False, default=None)
    time_done_datetime: Optional[datetime] = field(init=False, default=None)
    time_expiration_datetime: Optional[datetime] = field(init=False, default=None)
    type_string: Optional[str] = field(init=False, default=None)
    state_string: Optional[str] = field(init=False, default=None)
    age_seconds: Optional[float] = field(init=False, default=None)
    age_hours: Optional[float] = field(init=False, default=None)
    age_days: Optional[float] = field(init=False, default=None)
    is_expired: Optional[bool] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.time_setup is not None:
            self.time_setup_datetime = datetime.fromtimestamp(self.time_setup)
            self.age_seconds = datetime.now().timestamp() - self.time_setup
            self.age_hours = self.age_seconds / 3600
            self.age_days = self.age_seconds / 86400
        
        if self.time_done is not None:
            self.time_done_datetime = datetime.fromtimestamp(self.time_done)
        
        if self.time_expiration is not None:
            self.time_expiration_datetime = datetime.fromtimestamp(self.time_expiration)
            self.is_expired = datetime.now().timestamp() > self.time_expiration
        
        if self.type is not None:
            self.type_string = self._get_order_type_string(self.type)
        
        if self.state is not None:
            self.state_string = self._get_order_state_string(self.state)
    
    def _get_order_type_string(self, order_type: int) -> str:
        """Convert order type to human-readable string."""
        type_map = {
            0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT",
            4: "BUY_STOP", 5: "SELL_STOP", 6: "BUY_STOP_LIMIT",
            7: "SELL_STOP_LIMIT", 8: "CLOSE_BY"
        }
        return type_map.get(order_type, f"UNKNOWN_{order_type}")
    
    def _get_order_state_string(self, state: int) -> str:
        """Convert order state to human-readable string."""
        state_map = {
            0: "STARTED", 1: "PLACED", 2: "CANCELED", 3: "PARTIAL",
            4: "FILLED", 5: "REJECTED", 6: "EXPIRED", 7: "REQUEST_ADD",
            8: "REQUEST_MODIFY", 9: "REQUEST_CANCEL"
        }
        return state_map.get(state, f"UNKNOWN_{state}")


@dataclass
class Deal(BaseModel):
    """Deal model based on mt5.history_deals_get()."""
    ticket: Optional[int] = None
    order: Optional[int] = None
    time: Optional[int] = None
    time_msc: Optional[int] = None
    type: Optional[int] = None
    entry: Optional[int] = None
    magic: Optional[int] = None
    reason: Optional[int] = None
    position_id: Optional[int] = None
    volume: Optional[float] = None
    price: Optional[float] = None
    commission: Optional[float] = None
    swap: Optional[float] = None
    profit: Optional[float] = None
    fee: Optional[float] = None
    symbol: Optional[str] = None
    comment: Optional[str] = None
    external_id: Optional[str] = None
    
    # Calculated fields
    time_datetime: Optional[datetime] = field(init=False, default=None)
    type_string: Optional[str] = field(init=False, default=None)
    entry_string: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.time is not None:
            self.time_datetime = datetime.fromtimestamp(self.time)
        
        if self.type is not None:
            self.type_string = self._get_deal_type_string(self.type)
        
        if self.entry is not None:
            self.entry_string = self._get_deal_entry_string(self.entry)
    
    def _get_deal_type_string(self, deal_type: int) -> str:
        """Convert deal type to human-readable string."""
        type_map = {
            0: "BUY", 1: "SELL", 2: "BALANCE", 3: "CREDIT", 4: "CHARGE",
            5: "CORRECTION", 6: "BONUS", 7: "COMMISSION", 8: "COMMISSION_DAILY",
            9: "COMMISSION_MONTHLY", 10: "COMMISSION_AGENT_DAILY",
            11: "COMMISSION_AGENT_MONTHLY", 12: "INTEREST", 13: "BUY_CANCELED",
            14: "SELL_CANCELED", 15: "DIVIDEND", 16: "DIVIDEND_FRANKED", 17: "TAX"
        }
        return type_map.get(deal_type, f"UNKNOWN_{deal_type}")
    
    def _get_deal_entry_string(self, entry: int) -> str:
        """Convert deal entry to human-readable string."""
        entry_map = {0: "IN", 1: "OUT", 2: "INOUT", 3: "OUT_BY"}
        return entry_map.get(entry, f"UNKNOWN_{entry}")


@dataclass
class Tick(BaseModel):
    """Tick model based on mt5.symbol_info_tick()."""
    time: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    volume: Optional[int] = None
    time_msc: Optional[int] = None
    flags: Optional[int] = None
    volume_real: Optional[float] = None
    
    # Calculated fields
    time_datetime: Optional[datetime] = field(init=False, default=None)
    spread: Optional[float] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.time is not None:
            self.time_datetime = datetime.fromtimestamp(self.time)
        
        if self.bid is not None and self.ask is not None:
            self.spread = self.ask - self.bid


@dataclass
class Rate(BaseModel):
    """Rate model for OHLCV data from mt5.copy_rates_*()."""
    time: Optional[int] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    tick_volume: Optional[int] = None
    spread: Optional[int] = None
    real_volume: Optional[int] = None
    
    # Calculated fields
    time_datetime: Optional[datetime] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.time is not None:
            self.time_datetime = datetime.fromtimestamp(self.time)


@dataclass
class BookInfo(BaseModel):
    """Market depth (order book) model based on mt5.market_book_get()."""
    type: Optional[int] = None
    price: Optional[float] = None
    volume: Optional[int] = None
    volume_real: Optional[float] = None
    
    # Calculated fields
    type_string: Optional[str] = field(init=False, default=None)
    
    def __post_init__(self):
        """Calculate derived fields."""
        if self.type is not None:
            self.type_string = "BUY" if self.type == 1 else "SELL" if self.type == 2 else f"UNKNOWN_{self.type}"


@dataclass
class PortfolioSummary(BaseModel):
    """Portfolio summary model with comprehensive analysis."""
    account_info: Optional[Dict[str, Any]] = None
    positions_summary: Optional[Dict[str, Any]] = None
    orders_summary: Optional[Dict[str, Any]] = None
    risk_metrics: Optional[Dict[str, Any]] = None
    symbol_distribution: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


# Factory functions for creating models from MT5 data
def create_account_info(mt5_account_info) -> Optional[AccountInfo]:
    """Create AccountInfo model from MT5 account_info."""
    return AccountInfo.from_mt5_struct(mt5_account_info)


def create_symbol_info(mt5_symbol_info) -> Optional[SymbolInfo]:
    """Create SymbolInfo model from MT5 symbol_info."""
    return SymbolInfo.from_mt5_struct(mt5_symbol_info)


def create_terminal_info(mt5_terminal_info) -> Optional[TerminalInfo]:
    """Create TerminalInfo model from MT5 terminal_info."""
    return TerminalInfo.from_mt5_struct(mt5_terminal_info)


def create_position(mt5_position) -> Optional[Position]:
    """Create Position model from MT5 position."""
    return Position.from_mt5_struct(mt5_position)


def create_order(mt5_order) -> Optional[Order]:
    """Create Order model from MT5 order."""
    return Order.from_mt5_struct(mt5_order)


def create_deal(mt5_deal) -> Optional[Deal]:
    """Create Deal model from MT5 deal."""
    return Deal.from_mt5_struct(mt5_deal)


def create_tick(mt5_tick) -> Optional[Tick]:
    """Create Tick model from MT5 tick."""
    return Tick.from_mt5_struct(mt5_tick)


def create_rate(mt5_rate) -> Optional[Rate]:
    """Create Rate model from MT5 rate."""
    return Rate.from_mt5_struct(mt5_rate)


def create_trade_result(mt5_result) -> Optional[TradeResult]:
    """Create TradeResult model from MT5 trade result."""
    return TradeResult.from_mt5_struct(mt5_result)


def create_order_check_result(mt5_check) -> Optional[OrderCheckResult]:
    """Create OrderCheckResult model from mt5.order_check result."""
    return OrderCheckResult.from_mt5_struct(mt5_check)


# Legacy models for backward compatibility
@dataclass
class OrderPosition(Position):
    """Legacy OrderPosition model - now inherits from Position."""
    identifier_class: str = field(init=False, default="OrderPosition")


@dataclass
class TradePosition(BaseModel):
    """Legacy TradePosition model for backward compatibility."""
    identifier_class: str = field(init=False, default="TradePosition")
    
    def __init__(self, data: dict):
        """Initialize with dictionary data (legacy behavior)."""
        self.identifier_class = "TradePosition"
        for key, value in data.items():
            setattr(self, key, value)
    
    def update_from_dict(self, data: dict):
        """Update from dictionary (legacy behavior)."""
        for key, value in data.items():
            setattr(self, key, value)
