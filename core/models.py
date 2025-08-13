"""
Request models for MetaApi application.
Provides minimal structured data validation inputs used by validators.
"""

from typing import Optional, Union
from dataclasses import dataclass


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
