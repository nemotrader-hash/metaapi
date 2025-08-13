"""
Request and response models for MetaApi application.
Provides structured data validation and serialization.
"""

from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum


class OrderDirection(str, Enum):
    """Order direction enumeration."""
    LONG = "long"
    SHORT = "short"
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"


@dataclass
class MT5ConnectionRequest:
    """Request model for MT5 connection initialization."""
    account_id: Union[str, int]
    password: str
    server: str
    
    def validate(self) -> None:
        """Validate the connection request."""
        if not self.account_id:
            raise ValueError("Account ID is required")
        if not self.password:
            raise ValueError("Password is required")
        if not self.server:
            raise ValueError("Server is required")


@dataclass
class MarketOrderRequest:
    """Request model for creating market orders."""
    symbol: str
    stake_amount: float  # USD risk amount (will be converted to lot size)
    side: str
    stoploss: Optional[float] = None
    takeprofit: Optional[float] = None
    deviation: int = 5
    magic: int = 23400
    
    def validate(self) -> None:
        """Validate the market order request."""
        if not self.symbol:
            raise ValueError("Symbol is required")
        if not isinstance(self.stake_amount, (int, float)) or self.stake_amount <= 0:
            raise ValueError("Stake amount (USD risk) must be a positive number")
        if not (1.0 <= self.stake_amount <= 1000000.0):
            raise ValueError("Stake amount must be between $1 and $100,000 USD")
        if self.side.lower() not in ['long', 'short', 'buy', 'sell']:
            raise ValueError("Side must be one of: long, short, buy, sell")
        if self.stoploss is not None and not isinstance(self.stoploss, (int, float)):
            raise ValueError("Stop loss must be a number")
        if self.takeprofit is not None and not isinstance(self.takeprofit, (int, float)):
            raise ValueError("Take profit must be a number")


@dataclass
class CloseOrderRequest:
    """Request model for closing orders."""
    symbol: str
    
    def validate(self) -> None:
        """Validate the close order request."""
        if not self.symbol:
            raise ValueError("Symbol is required")


@dataclass
class TelegramAlertRequest:
    """Request model for Telegram alerts."""
    message: str = "🚨 Alert from MT5 Server"
    ping: str = "Unknown"
    chat_id: Optional[int] = None
    include_timestamp: bool = True
    
    def validate(self) -> None:
        """Validate the telegram alert request."""
        if not isinstance(self.message, str):
            raise ValueError("Message must be a string")
        if self.chat_id is not None and not isinstance(self.chat_id, int):
            raise ValueError("Chat ID must be an integer")


@dataclass
class ApiResponse:
    """Standard API response model."""
    message: str
    status: str = "OK"
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            "message": self.message,
            "status": self.status
        }
        
        if self.data is not None:
            response["data"] = self.data
        
        if self.errors:
            response["errors"] = self.errors
            
        return response


@dataclass
class ErrorResponse:
    """Error response model."""
    error: str
    message: str
    status: str = "NOTOK"
    code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        response = {
            "error": self.error,
            "message": self.message,
            "status": self.status
        }
        
        if self.code is not None:
            response["code"] = self.code
            
        if self.details:
            response["details"] = self.details
            
        return response


@dataclass
class PositionInfo:
    """Position information model."""
    ticket: int
    symbol: str
    volume: float
    type: int
    price_open: float
    price_current: float
    profit: float
    swap: float
    comment: str
    magic: int
    time: int
    sl: float = 0.0
    tp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary."""
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "volume": self.volume,
            "type": "BUY" if self.type == 0 else "SELL",
            "price_open": self.price_open,
            "price_current": self.price_current,
            "profit": self.profit,
            "swap": self.swap,
            "comment": self.comment,
            "magic": self.magic,
            "time": self.time,
            "sl": self.sl,
            "tp": self.tp
        }


@dataclass
class AccountInfo:
    """Account information model."""
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_mode: int
    currency_digits: int
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    name: str
    server: str
    currency: str
    company: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert account info to dictionary."""
        return {
            "login": self.login,
            "balance": self.balance,
            "equity": self.equity,
            "margin": self.margin,
            "margin_free": self.margin_free,
            "margin_level": self.margin_level,
            "profit": self.profit,
            "currency": self.currency,
            "leverage": self.leverage,
            "name": self.name,
            "server": self.server,
            "company": self.company,
            "trade_allowed": self.trade_allowed
        }
