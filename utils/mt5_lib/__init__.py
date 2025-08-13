from .modules import MT5_Interface
from .constants import *
from .market_data import MarketDataProvider, market_data
from .account import AccountMonitor, account_monitor
from .models import *
from .base import *
from .exceptions import (
    MetaApiError,
    MT5ConnectionError,
    MT5AuthenticationError,
    MT5TradingError,
    MT5SymbolError,
)

# Legacy imports for backward compatibility
# Legacy imports for backward compatibility (optional)
try:
    from .trading import TradingManager, trading_manager
except Exception:
    # The trading module may not be present in all builds
    TradingManager = None
    trading_manager = None

__all__ = [
    'MT5_Interface',
    'MarketDataProvider', 
    'AccountMonitor',
    'market_data',
    'account_monitor',
    # Models
    'BaseModel',
    'AccountInfo',
    'SymbolInfo',
    'TerminalInfo',
    'TradeRequest',
    'TradeResult',
    'Position',
    'Order',
    'Deal',
    'Tick',
    'Rate',
    'BookInfo',
    'PortfolioSummary',
    'OrderPosition',
    'TradePosition',
    # Factory functions
    'create_account_info',
    'create_symbol_info',
    'create_terminal_info',
    'create_position',
    'create_order',
    'create_deal',
    'create_tick',
    'create_rate',
    'create_trade_result',
    # Constants
    'TRADE_ACTION',
    'ORDER_TYPE', 
    'ORDER_FILLING',
    'ORDER_TIME',
    'POSITION_TYPE',
    'TIMEFRAME',
    'TIMEFRAME_MAP',
    'create_trade_request',
    'get_error_description',
    'parse_timeframe',
    # Exceptions
    'MetaApiError',
    'MT5ConnectionError',
    'MT5AuthenticationError',
    'MT5TradingError',
    'MT5SymbolError',
]

# Extend exports if legacy trading symbols are available
if TradingManager is not None:
    __all__.extend(['TradingManager', 'trading_manager'])