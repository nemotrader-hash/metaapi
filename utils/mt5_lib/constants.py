"""
MetaTrader 5 Constants and Enumerations
======================================

This module provides all the constants and enumerations used in MT5 operations,
based on the official MetaTrader5 Python documentation.
"""

from enum import IntEnum, Enum
from typing import Dict, Any


class TRADE_ACTION(IntEnum):
    """Trade operation types"""
    DEAL = 1        # Place a trading order for an immediate execution with the specified parameters (market order)
    PENDING = 5     # Place a trade order for the execution under specified conditions (pending order)
    SLTP = 6        # Modify Stop Loss and Take Profit values of an opened position
    MODIFY = 7      # Modify the parameters of the order placed previously
    REMOVE = 8      # Delete the pending order placed previously
    CLOSE_BY = 10   # Close a position by an opposite one


class ORDER_TYPE(IntEnum):
    """Order types"""
    BUY = 0           # Market Buy order
    SELL = 1          # Market Sell order
    BUY_LIMIT = 2     # Buy Limit pending order
    SELL_LIMIT = 3    # Sell Limit pending order
    BUY_STOP = 4      # Buy Stop pending order
    SELL_STOP = 5     # Sell Stop pending order
    BUY_STOP_LIMIT = 6   # Buy Stop Limit pending order
    SELL_STOP_LIMIT = 7  # Sell Stop Limit pending order
    CLOSE_BY = 8      # Order to close a position by an opposite one


class ORDER_STATE(IntEnum):
    """Order states"""
    STARTED = 0       # Order checked, but not yet accepted by broker
    PLACED = 1        # Order accepted
    CANCELED = 2      # Order canceled by client
    PARTIAL = 3       # Order partially executed
    FILLED = 4        # Order fully executed
    REJECTED = 5      # Order rejected
    EXPIRED = 6       # Order expired
    REQUEST_ADD = 7   # Order is being registered (placing to the trading system)
    REQUEST_MODIFY = 8   # Order is being modified (changing its parameters)
    REQUEST_CANCEL = 9   # Order is being deleted (deleting from the trading system)


class ORDER_FILLING(IntEnum):
    """Order filling types"""
    FOK = 0          # Fill or Kill - the order must be filled completely or not at all
    IOC = 1          # Immediate or Cancel - the order is filled to the maximum possible volume
    RETURN = 2       # Return - normal filling


class ORDER_TIME(IntEnum):
    """Order lifetime"""
    GTC = 0          # Good till cancel order
    DAY = 1          # Good till current trade day order
    SPECIFIED = 2    # Good till specified time order
    SPECIFIED_DAY = 3  # Good till specified day order


class POSITION_TYPE(IntEnum):
    """Position types"""
    BUY = 0          # Buy position
    SELL = 1         # Sell position


class POSITION_REASON(IntEnum):
    """Position reasons"""
    CLIENT = 0       # The position was opened as a result of activation of an order placed from a desktop terminal
    MOBILE = 1       # The position was opened as a result of activation of an order placed from a mobile application
    WEB = 2          # The position was opened as a result of activation of an order placed from the web platform
    EXPERT = 3       # The position was opened as a result of activation of an order placed from an MQL5-program (Expert Advisor or script)


class DEAL_TYPE(IntEnum):
    """Deal types"""
    BUY = 0          # Buy deal
    SELL = 1         # Sell deal
    BALANCE = 2      # Balance operation
    CREDIT = 3       # Credit operation
    CHARGE = 4       # Additional charge
    CORRECTION = 5   # Correction
    BONUS = 6        # Bonus
    COMMISSION = 7   # Commission
    COMMISSION_DAILY = 8     # Daily commission
    COMMISSION_MONTHLY = 9   # Monthly commission
    COMMISSION_AGENT_DAILY = 10     # Daily agent commission
    COMMISSION_AGENT_MONTHLY = 11   # Monthly agent commission
    INTEREST = 12    # Interest rate
    BUY_CANCELED = 13    # Canceled buy deal
    SELL_CANCELED = 14   # Canceled sell deal
    DIVIDEND = 15    # Dividend operations
    DIVIDEND_FRANKED = 16    # Franked (non-taxable) dividend operations
    TAX = 17         # Tax charges


class DEAL_ENTRY(IntEnum):
    """Deal entry types"""
    IN = 0           # Entry into the market
    OUT = 1          # Exit from the market
    INOUT = 2        # Reverse
    OUT_BY = 3       # Close a position by an opposite one


class DEAL_REASON(IntEnum):
    """Deal reasons"""
    CLIENT = 0       # The deal was executed as a result of activation of an order placed from a desktop terminal
    MOBILE = 1       # The deal was executed as a result of activation of an order placed from a mobile application
    WEB = 2          # The deal was executed as a result of activation of an order placed from the web platform
    EXPERT = 3       # The deal was executed as a result of activation of an order placed from an MQL5-program


class SYMBOL_TRADE_MODE(IntEnum):
    """Symbol trading modes"""
    DISABLED = 0     # Trade is disabled for the symbol
    LONGONLY = 1     # Only long positions are allowed
    SHORTONLY = 2    # Only short positions are allowed
    CLOSEONLY = 3    # Only position close operations are allowed
    FULL = 4         # No trade restrictions


class SYMBOL_TRADE_EXECUTION(IntEnum):
    """Symbol execution modes"""
    REQUEST = 0      # Execution by request
    INSTANT = 1      # Instant execution
    MARKET = 2       # Market execution
    EXCHANGE = 3     # Exchange execution


class SYMBOL_CALC_MODE(IntEnum):
    """Symbol calculation modes"""
    UNKNOWN = 0      # Unknown calculation mode
    FOREX = 1        # Forex
    FUTURES = 2      # Futures
    CFD = 3          # CFD
    CFDINDEX = 4     # CFD on indices
    CFDLEVERAGE = 5  # CFD with leverage
    EXCH_STOCKS = 32     # Exchange stocks
    EXCH_FUTURES = 33    # Exchange futures
    EXCH_FUTURES_FORTS = 34  # FORTS futures
    EXCH_BONDS = 35      # Exchange bonds
    EXCH_STOCKS_MOEX = 36    # Exchange stocks MOEX
    EXCH_BONDS_MOEX = 37     # Exchange bonds MOEX
    SERV_COLLATERAL = 64     # Collateral


class TIMEFRAME(IntEnum):
    """Chart timeframes"""
    M1 = 1           # 1 minute
    M2 = 2           # 2 minutes
    M3 = 3           # 3 minutes
    M4 = 4           # 4 minutes
    M5 = 5           # 5 minutes
    M6 = 6           # 6 minutes
    M10 = 10         # 10 minutes
    M12 = 12         # 12 minutes
    M15 = 15         # 15 minutes
    M20 = 20         # 20 minutes
    M30 = 30         # 30 minutes
    H1 = 16385       # 1 hour
    H2 = 16386       # 2 hours
    H3 = 16387       # 3 hours
    H4 = 16388       # 4 hours
    H6 = 16390       # 6 hours
    H8 = 16392       # 8 hours
    H12 = 16396      # 12 hours
    D1 = 16408       # 1 day
    W1 = 32769       # 1 week
    MN1 = 49153      # 1 month


# Timeframe string mapping
TIMEFRAME_MAP = {
    "M1": TIMEFRAME.M1, "1m": TIMEFRAME.M1,
    "M2": TIMEFRAME.M2, "2m": TIMEFRAME.M2,
    "M3": TIMEFRAME.M3, "3m": TIMEFRAME.M3,
    "M4": TIMEFRAME.M4, "4m": TIMEFRAME.M4,
    "M5": TIMEFRAME.M5, "5m": TIMEFRAME.M5,
    "M6": TIMEFRAME.M6, "6m": TIMEFRAME.M6,
    "M10": TIMEFRAME.M10, "10m": TIMEFRAME.M10,
    "M12": TIMEFRAME.M12, "12m": TIMEFRAME.M12,
    "M15": TIMEFRAME.M15, "15m": TIMEFRAME.M15,
    "M20": TIMEFRAME.M20, "20m": TIMEFRAME.M20,
    "M30": TIMEFRAME.M30, "30m": TIMEFRAME.M30,
    "H1": TIMEFRAME.H1, "1h": TIMEFRAME.H1,
    "H2": TIMEFRAME.H2, "2h": TIMEFRAME.H2,
    "H3": TIMEFRAME.H3, "3h": TIMEFRAME.H3,
    "H4": TIMEFRAME.H4, "4h": TIMEFRAME.H4,
    "H6": TIMEFRAME.H6, "6h": TIMEFRAME.H6,
    "H8": TIMEFRAME.H8, "8h": TIMEFRAME.H8,
    "H12": TIMEFRAME.H12, "12h": TIMEFRAME.H12,
    "D1": TIMEFRAME.D1, "1d": TIMEFRAME.D1,
    "W1": TIMEFRAME.W1, "1w": TIMEFRAME.W1,
    "MN1": TIMEFRAME.MN1, "1M": TIMEFRAME.MN1,
}


# Error codes with descriptions
MT5_ERROR_CODES = {
    1: "RES_S_OK: Generic success",
    -1: "RES_E_FAIL: Generic fail",
    -2: "RES_E_INVALID_PARAMS: Invalid arguments/parameters",
    -3: "RES_E_NO_MEMORY: No memory condition",
    -4: "RES_E_NOT_FOUND: No history",
    -5: "RES_E_INVALID_VERSION: Invalid version",
    -6: "RES_E_AUTH_FAILED: Authorization failed",
    -7: "RES_E_UNSUPPORTED: Unsupported method",
    -8: "RES_E_AUTO_TRADING_DISABLED: Auto-trading disabled",
    -10000: "RES_E_INTERNAL_FAIL: Internal IPC general error",
    -10001: "RES_E_INTERNAL_FAIL_SEND: Internal IPC send failed",
    -10002: "RES_E_INTERNAL_FAIL_RECEIVE: Internal IPC receive failed",
    -10003: "RES_E_INTERNAL_FAIL_INIT: Internal IPC init failed",
    -10004: "RES_E_INTERNAL_FAIL_CONNECT: Internal IPC connect failed",
    -10005: "RES_E_INTERNAL_FAIL_TIMEOUT: Internal timeout",
}


# Trade request structure template
def create_trade_request(
    action: TRADE_ACTION,
    symbol: str,
    volume: float,
    type: ORDER_TYPE,
    price: float = 0.0,
    stoplimit: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    deviation: int = 5,
    magic: int = 0,
    comment: str = "",
    type_time: ORDER_TIME = ORDER_TIME.GTC,
    expiration: int = 0,
    type_filling: ORDER_FILLING = ORDER_FILLING.FOK,
    position: int = 0,
    position_by: int = 0
) -> Dict[str, Any]:
    """Create a properly formatted trade request dictionary"""
    request = {
        "action": action,
        "symbol": symbol,
        "volume": volume,
        "type": type,
        "price": price,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": type_time,
        "type_filling": type_filling,
    }
    
    # Add optional parameters if they are not default
    if stoplimit != 0.0:
        request["stoplimit"] = stoplimit
    if sl != 0.0:
        request["sl"] = sl
    if tp != 0.0:
        request["tp"] = tp
    if expiration != 0:
        request["expiration"] = expiration
    if position != 0:
        request["position"] = position
    if position_by != 0:
        request["position_by"] = position_by
    
    return request


def get_error_description(error_code: int) -> str:
    """Get human-readable error description"""
    return MT5_ERROR_CODES.get(error_code, f"Unknown error code: {error_code}")


def parse_timeframe(timeframe: str) -> int:
    """Parse timeframe string to MT5 constant"""
    if isinstance(timeframe, int):
        return timeframe
    return TIMEFRAME_MAP.get(timeframe.upper(), TIMEFRAME.M1)
