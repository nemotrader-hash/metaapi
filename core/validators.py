"""
Input validation utilities for MetaApi application.
Provides validation functions for API requests and data sanitization.
"""

import re
from typing import Any, Dict, List, Union
from functools import wraps
from flask import request, jsonify
from core.exceptions import ValidationError
from core.models import (
    MT5ConnectionRequest, 
    MarketOrderRequest, 
    CloseOrderRequest, 
    TelegramAlertRequest
)


def validate_symbol(symbol: str) -> bool:
    """Validate trading symbol format."""
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Basic symbol validation (alphanumeric, dots, underscores)
    pattern = r'^[A-Za-z0-9._]{1,20}$'
    return bool(re.match(pattern, symbol.strip()))


def validate_lot_size(lot_size: Union[float, int]) -> bool:
    """Validate lot size."""
    try:
        lot = float(lot_size)
        return 0.01 <= lot <= 100.0  # Reasonable range
    except (ValueError, TypeError):
        return False


def validate_usd_risk_amount(risk_amount: Union[float, int]) -> bool:
    """Validate USD risk amount for position sizing."""
    try:
        risk = float(risk_amount)
        # Allow risk amounts from $1 to $1,000,000 USD
        return 1.0 <= risk <= 1000000.0
    except (ValueError, TypeError):
        return False


def validate_price(price: Union[float, int]) -> bool:
    """Validate price value."""
    try:
        p = float(price)
        return p > 0
    except (ValueError, TypeError):
        return False


def validate_account_id(account_id: Union[str, int]) -> bool:
    """Validate MT5 account ID."""
    try:
        # Convert to string and check if it's numeric
        account_str = str(account_id).strip()
        return account_str.isdigit() and len(account_str) >= 6
    except (ValueError, TypeError):
        return False


def validate_server_name(server: str) -> bool:
    """Validate MT5 server name."""
    if not server or not isinstance(server, str):
        return False
    
    # Basic server name validation
    pattern = r'^[A-Za-z0-9.-]{1,50}$'
    return bool(re.match(pattern, server.strip()))


def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input."""
    if not isinstance(value, str):
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', value)
    return sanitized.strip()[:max_length]


def validate_json_request(required_fields: List[str] = None, model_class=None):
    """Deprecated middleware-style validator (kept for compatibility, unused)."""
    def decorator(func):
        return func
    return decorator


def validate_mt5_connection_data(data: Dict[str, Any]) -> MT5ConnectionRequest:
    """Validate MT5 connection request data."""
    try:
        account_id = data.get('account_id')
        password = data.get('password')
        server = data.get('server')
        
        if not validate_account_id(account_id):
            raise ValidationError("Invalid account ID format")
        
        if not password or len(str(password)) < 4:
            raise ValidationError("Password must be at least 4 characters")
        
        if not validate_server_name(server):
            raise ValidationError("Invalid server name format")
        
        return MT5ConnectionRequest(
            account_id=account_id,
            password=str(password),
            server=sanitize_string(server)
        )
    
    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}")


def validate_market_order_data(data: Dict[str, Any]) -> MarketOrderRequest:
    """
    Validate market order request data.
    
    Args:
        data: Dictionary containing order data with stake_amount as USD risk amount
        
    Returns:
        MarketOrderRequest: Validated order request object
        
    Raises:
        ValidationError: If validation fails
        
    Note:
        stake_amount is expected to be a USD risk amount ($1-$100,000)
        that will be automatically converted to appropriate lot size.
    """
    try:
        symbol = data.get('symbol')
        stake_amount = data.get('stake_amount')
        side = data.get('side')
        
        if not validate_symbol(symbol):
            raise ValidationError("Invalid symbol format")
        
        if not validate_usd_risk_amount(stake_amount):
            raise ValidationError("Invalid stake amount - must be between $1 and $100,000 USD")
        
        if side.lower() not in ['long', 'short', 'buy', 'sell']:
            raise ValidationError("Invalid order side")
        
        # Optional fields
        stoploss = data.get('stoploss')
        takeprofit = data.get('takeprofit')
        
        if stoploss is not None and not validate_price(stoploss):
            raise ValidationError("Invalid stop loss value")
        
        if takeprofit is not None and not validate_price(takeprofit):
            raise ValidationError("Invalid take profit value")
        
        return MarketOrderRequest(
            symbol=sanitize_string(symbol),
            stake_amount=round(float(stake_amount), 2),
            side=side.lower(),
            stoploss=float(stoploss) if stoploss is not None else None,
            takeprofit=float(takeprofit) if takeprofit is not None else None,
            deviation=data.get('deviation', 5),
            magic=data.get('magic', 23400)
        )
    
    except (KeyError, ValueError) as e:
        raise ValidationError(f"Invalid market order data: {e}")


def validate_close_order_data(data: Dict[str, Any]) -> CloseOrderRequest:
    """Validate close order request data."""
    try:
        symbol = data.get('symbol')
        
        if not validate_symbol(symbol):
            raise ValidationError("Invalid symbol format")
        
        return CloseOrderRequest(symbol=sanitize_string(symbol))
    
    except KeyError as e:
        raise ValidationError(f"Missing required field: {e}")


def validate_telegram_alert_data(data: Dict[str, Any]) -> TelegramAlertRequest:
    """Validate Telegram alert request data."""
    try:
        message = data.get('message', '🚨 Alert from MT5 Server')
        ping = data.get('ping', 'Unknown')
        chat_id = data.get('chat_id')
        include_timestamp = data.get('include_timestamp', True)
        
        return TelegramAlertRequest(
            message=sanitize_string(message, 4000),  # Telegram message limit
            ping=sanitize_string(ping, 100),
            chat_id=int(chat_id) if chat_id is not None else None,
            include_timestamp=bool(include_timestamp)
        )
    
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid telegram alert data: {e}")
