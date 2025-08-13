"""
Enhanced MetaTrader 5 Interface
==============================

This module provides a comprehensive interface to MetaTrader 5 with improved
error handling, connection management, and integration with specialized modules.
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    # Mock MT5 for development/testing environments
    class MockMT5:
        @staticmethod
        def initialize(*args, **kwargs):
            return False
        @staticmethod
        def shutdown():
            pass
        @staticmethod
        def last_error():
            return (0, "Mock MT5 - MetaTrader5 not installed")
        @staticmethod
        def terminal_info():
            return None
        @staticmethod
        def account_info():
            return None
    mt5 = MockMT5()
import logging
import pandas as pd
import datetime
import time
from contextlib import contextmanager
from decimal import Decimal, ROUND_DOWN

from .base import OrderPosition, TradePosition
from .constants import (
    TRADE_ACTION, ORDER_TYPE, ORDER_FILLING, ORDER_TIME,
    POSITION_TYPE, TIMEFRAME, get_error_description, create_trade_request, parse_timeframe
)
from .models import (
    AccountInfo, SymbolInfo, TerminalInfo, Position, Order, Deal, PortfolioSummary,
    TradeRequest, TradeResult, OrderCheckResult,
    create_account_info, create_symbol_info, create_terminal_info, create_trade_result, create_order_check_result
)
from .market_data import MarketDataProvider
from .account import AccountMonitor
from typing import Union, Optional, Dict, List, Tuple, Any
from .constants import MT5_ERROR_CODES
from datetime import timedelta

from log.logger import setup_logger
from .exceptions import (
    MT5ConnectionError, 
    MT5AuthenticationError, 
    MT5TradingError, 
    MT5SymbolError,
    MetaApiError
)

logger = setup_logger()


class MT5_Interface():
    """
    Enhanced MetaTrader 5 Interface with modular architecture.
    
    This class provides a comprehensive interface to MT5 operations including
    connection management, trading, market data, and account monitoring.
    """
    
    def __init__(self, login=True, account_id: Optional[Union[str, int]] = None, password: Optional[str] = None, 
                 server: Optional[str] = None, path: Optional[str] = "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                 max_retries: int = 3, retry_delay: float = 1.0, default_magic: int = 12345,
                 default_filling: Optional[ORDER_FILLING] = None):
        """
        Initialize a connection to the MetaTrader 5 terminal using the given credentials.

        Args:
            login (bool): Whether to login with credentials or just initialize.
            account_id (Union[str, int]): MT5 login account ID.
            password (str): MT5 account password.
            server (str): MT5 broker server name.
            path (str): Path to MT5 terminal executable.
            max_retries (int): Maximum number of connection retries.
            retry_delay (float): Delay between retries in seconds.
            default_magic (int): Default magic number for trades.
            default_filling (ORDER_FILLING | None): Preferred default filling for orders. If None, a sensible
                default is used and may be overridden per-symbol when building requests.
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.default_magic = default_magic
        self.is_connected = False
        self.account_info = None
        self.connection_params = {
            'account_id': account_id, 'password': password, 'server': server,
            'path': path
        }
        
        # Initialize specialized modules
        self.market_data = MarketDataProvider()
        self.account = AccountMonitor()
        
        # Trading parameters (integrated from TradingManager)
        self.default_deviation = 5
        self.default_filling = default_filling if default_filling is not None else ORDER_FILLING.IOC
        
        # Connection status tracking
        self._last_connection_check = 0
        self._connection_check_interval = 30  # seconds
        
        if login:
            self._initialize_with_login(account_id, password, server, path)
        else:
            self._initialize_without_login(path)
    
    def _initialize_with_login(self, account_id: Union[str, int], password: str, server: str, path: str):
        """Initialize MT5 with login credentials."""
        if not all([account_id, password, server]):
            raise MT5AuthenticationError("Account ID, password, and server are required for login")
        
        for attempt in range(self.max_retries):
            try:
                if mt5.initialize(login=int(account_id), password=password, server=server, path=path):
                    self.is_connected = True
                    self.account_info = mt5.account_info()
                    logger.info(f"MT5 initialized successfully for account {account_id} on server '{server}'")
                    return
                else:
                    error = self.get_last_error()
                    if attempt == self.max_retries - 1:
                        raise MT5AuthenticationError(
                            f"Authentication failed after {self.max_retries} attempts: {error['description']}",
                            code=error['code']
                        )
                    logger.warning(f"Authentication attempt {attempt + 1} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise MT5ConnectionError(f"Connection failed after {self.max_retries} attempts: {str(e)}")
                time.sleep(self.retry_delay)
    
    def _initialize_without_login(self, path: str):
        """Initialize MT5 without login credentials."""
        for attempt in range(self.max_retries):
            try:
                if mt5.initialize(path=path):
                    self.is_connected = True
                    logger.info("MT5 initialized successfully without login")
                    return
                else:
                    error = self.get_last_error()
                    if attempt == self.max_retries - 1:
                        raise MT5ConnectionError(
                            f"Initialization failed after {self.max_retries} attempts: {error['description']}",
                            code=error['code']
                        )
                    logger.warning(f"Initialization attempt {attempt + 1} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise MT5ConnectionError(f"Connection failed after {self.max_retries} attempts: {str(e)}")
                time.sleep(self.retry_delay)
    
    @contextmanager
    def ensure_connection(self):
        """Context manager to ensure MT5 connection is active."""
        if not self.is_connected or not mt5.terminal_info():
            raise MT5ConnectionError("MT5 terminal is not connected")
        try:
            yield
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown()
    
    def shutdown(self):
        """Safely shutdown MT5 connection."""
        try:
            if self.is_connected:
                mt5.shutdown()
                self.is_connected = False
                logger.info("MT5 connection shutdown successfully")
        except Exception as e:
            logger.warning(f"Error during MT5 shutdown: {e}")
            


    @contextmanager
    def ensure_symbol(self, symbol: str):
        """Ensure a symbol is visible/enabled during the operation, restoring state after."""
        with self.ensure_connection():
            info = mt5.symbol_info(symbol)
            if info is None:
                raise MT5SymbolError(f"Symbol {symbol} not found")
            was_visible = info.visible
            if not was_visible:
                if not mt5.symbol_select(symbol, True):
                    raise MT5SymbolError(f"Failed to enable symbol {symbol}")
            try:
                yield
            finally:
                if not was_visible:
                    mt5.symbol_select(symbol, False)

    def ensure_symbols(self, symbols: List[str]) -> bool:
        """Batch-enable multiple symbols idempotently."""
        with self.ensure_connection():
            for symbol in symbols:
                info = mt5.symbol_info(symbol)
                if info is None:
                    raise MT5SymbolError(f"Symbol {symbol} not found")
                if not info.visible:
                    if not mt5.symbol_select(symbol, True):
                        raise MT5SymbolError(f"Failed to enable symbol {symbol}")
        return True

    @staticmethod
    def normalize_price(symbol: str, price: float) -> float:
        info = mt5.symbol_info(symbol)
        if info is None:
            return price
        point = Decimal(str(info.point))
        if point == 0:
            return price
        # Snap price to the nearest point grid
        scaled = Decimal(str(price)) / point
        normalized = (scaled.to_integral_value(rounding=ROUND_DOWN)) * point
        return float(normalized)

    @staticmethod
    def normalize_volume(symbol: str, volume: float) -> float:
        info = mt5.symbol_info(symbol)
        if info is None:
            return volume
        step = Decimal(str(info.volume_step or 0.01))
        min_vol = Decimal(str(info.volume_min or 0.01))
        max_vol = Decimal(str(info.volume_max or 100.0))
        v = Decimal(str(volume))
        if step > 0:
            v = (v / step).to_integral_value(rounding=ROUND_DOWN) * step
        if v < min_vol:
            v = min_vol
        if v > max_vol:
            v = max_vol
        return float(v)

    @staticmethod
    def default_filling_and_deviation(symbol: str) -> tuple[ORDER_FILLING, int]:
        info = mt5.symbol_info(symbol)
        if info is None:
            return ORDER_FILLING.IOC, 5
        # Heuristic based on execution mode
        if info.trade_execution == 0:  # REQUEST
            return ORDER_FILLING.FOK, 10
        if info.trade_execution == 1:  # INSTANT
            return ORDER_FILLING.FOK, 20
        if info.trade_execution == 2:  # MARKET
            return ORDER_FILLING.IOC, 5
        return ORDER_FILLING.RETURN, 10

    def _send_order(self, request: Dict | TradeRequest) -> TradeResult:
        """Send the order to the broker using typed models and return TradeResult."""
        with self.ensure_connection():
            # Normalize to TradeRequest model
            trade_request: TradeRequest = request if isinstance(request, TradeRequest) else TradeRequest.from_dict(request)
            request_dict = trade_request.to_dict()

            # Validate request before sending
            check_result = self.check_order(request_dict)
            if not check_result or (hasattr(check_result, 'success') and not check_result.success):
                error_info = self.get_last_error()
                raise MT5TradingError(
                    f"Order validation failed for {trade_request.symbol or 'unknown'}: {getattr(check_result, 'retcode_description', error_info.get('description'))}",
                    code=getattr(check_result, 'retcode', error_info.get('code'))
                )

            try:
                mt5_result = mt5.order_send(request_dict)

                if mt5_result is None:
                    error_info = self.get_last_error()
                    logger.error(f"Order send returned None: {error_info}")
                    raise MT5TradingError(f"Order send failed: {error_info.get('description')}", code=error_info.get('code'))

                trade_result: TradeResult = create_trade_result(mt5_result)

                if not trade_result.success:
                    logger.error(
                        f"Order failed for {trade_request.symbol}: {trade_result.comment} (code: {trade_result.retcode})"
                    )
                else:
                    logger.info(
                        f"Order successful for {trade_request.symbol}: {trade_result.comment}"
                    )
                return trade_result

            except Exception as e:
                logger.error(f"Unexpected error sending order: {e}")
                raise MT5TradingError(f"Failed to send order: {str(e)}")
    
    def check_order(self, request: Dict) -> bool:
        """Check order before sending it to the broker."""
        try:
            with self.ensure_connection():
                check = mt5.order_check(request)
                if check is None:
                    logger.warning("Order check returned None")
                    return False
                
                if check.retcode != 0:
                    logger.warning(f"Invalid order for {request.get('symbol', 'unknown')}: {check.comment} (code: {check.retcode})")
                    return False
                
                return True
        except Exception as e:
            logger.error(f"Error checking order: {e}")
            return False

    
    def fetch_data(self, symbol: str="EURUSD", timeframe: str='5m', count: int=200) -> Optional[pd.DataFrame]:
        tf_value = parse_timeframe(timeframe) if isinstance(timeframe, str) else timeframe
        rates = mt5.copy_rates_from_pos(symbol, tf_value, 0, count)
        if rates is None:
            logger.error(f" - Failed to fetch rates for the symbol {symbol}, at the {timeframe} Timeframes")
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    @staticmethod
    def initialize_symbols_list(symbol_array: list[str]) -> bool | Exception:
        all_symbols = mt5.symbols_get()
        if all_symbols is None:
            logger.error("Failed to retrieve symbols from MT5.")
            raise RuntimeError("MT5 connection issue or no symbols returned.")

        available_symbol_names = {symbol.name for symbol in all_symbols}

        for symbol in symbol_array:
            if symbol not in available_symbol_names:
                logger.error(f"Symbol not found: {symbol}")
                raise LookupError(f"Symbol '{symbol}' not available in MT5.")

            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to enable symbol: {symbol}")
                raise ValueError(f"Could not enable symbol '{symbol}'.")
            
        return True

    
    def place_limit_stop_order(self, order_type: str, symbol: str, volume: float, 
                               price: float, stop_loss: float, take_profit: float, 
                               comment: str = "Nothing") -> bool:
        symbol_info = mt5.symbol_info(symbol)
        
        # Check if symbol is available
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return False
        
        # Refresh the symbol data
        if not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        # Determine the order type using internal constants
        order_type_map = {
            "SELL_STOP": ORDER_TYPE.SELL_STOP,
            "BUY_STOP": ORDER_TYPE.BUY_STOP,
            "BUY_LIMIT": ORDER_TYPE.BUY_LIMIT,
            "SELL_LIMIT": ORDER_TYPE.SELL_LIMIT,
        }
        if order_type not in order_type_map:
            raise ValueError("Invalid Order Type")
        order_type_internal = order_type_map[order_type]

        # Create the request using internal models/constants
        filling, deviation_default = self.default_filling_and_deviation(symbol)
        if self.default_filling is not None:
            filling = self.default_filling
        order_params = create_trade_request(
            action=TRADE_ACTION.PENDING,
            symbol=symbol,
            volume=self.normalize_volume(symbol, volume),
            type=order_type_internal,
            price=self.normalize_price(symbol, price),
            sl=stop_loss,
            tp=take_profit,
            type_filling=filling,
            type_time=ORDER_TIME.GTC,
            comment=comment,
        )

        # Send the order to MT5
        try:
            result = self._send_order(order_params)
            
            if result.success:
                logger.info(f"{order_type} order for {symbol} placed successfully")
                return True
            else:
                logger.error(f"Error placing {order_type} order: {result.comment}")
                return False
                
        except (MT5TradingError, MT5ConnectionError) as e:
            logger.error(f"Failed to place {order_type} order for {symbol}: {e}")
            return False

    
    @staticmethod
    def get_orders_position(symbol,only_id=True) -> list[OrderPosition]:
        positions = mt5.positions_get(symbol=symbol)
        all_positions_dict : list = []
        if positions is None or len(positions) == 0:
            return []
        for position in positions:
            position_dict = position._asdict()
            all_positions_dict.append(OrderPosition(position_dict))

        return all_positions_dict
    
    @staticmethod
    def get_history_position(position_id) -> list[TradePosition]:
        positions = mt5.history_deals_get(position=position_id)
        all_positions_dict : list = []
    
        if positions is None or len(positions) == 0:
            return []
        for position in positions:
            position_dict = position._asdict()
            all_positions_dict.append(TradePosition(position_dict))

        return all_positions_dict
    
    def cancel_all_open_orders(self) -> List[Dict]:
        """Cancel all open pending orders."""
        with self.ensure_connection():
            all_cancelled_orders = []
            failed_cancellations = []
            
            orders = mt5.orders_get()
            if not orders:
                logger.info("No open orders to cancel")
                return all_cancelled_orders
                
            for order in orders:
                try:
                    cancel_params = create_trade_request(
                        action=TRADE_ACTION.REMOVE,
                        order=order.ticket,
                        comment="Order cancelled by MetaApi",
                    )
                    
                    result = self._send_order(cancel_params)
                    
                    if result.success:
                        logger.info(f"Successfully cancelled order {order.ticket}")
                        all_cancelled_orders.append({
                            "ticket": order.ticket,
                            "symbol": order.symbol,
                            "type": order.type,
                            "volume": order.volume_initial
                        })
                    else:
                        logger.error(f"Failed to cancel order {order.ticket}: {result.comment}")
                        failed_cancellations.append({
                            "ticket": order.ticket,
                            "error": result.comment
                        })
                        
                except Exception as e:
                    logger.error(f"Error cancelling order {order.ticket}: {e}")
                    failed_cancellations.append({
                        "ticket": order.ticket,
                        "error": str(e)
                    })
            
            if failed_cancellations:
                logger.warning(f"Failed to cancel {len(failed_cancellations)} orders")
            
            return all_cancelled_orders

      
    

    def create_market_order_mt5(self, symbol: str, stoploss: Optional[float] = None, takeprofit: Optional[float] = None,
                                direction: str = "long", stake_amount: float = None, lot_size: float = None, 
                                deviation: int = 5, magic: int = 23400) -> Dict[str, Any]:
        """
        Create a market order with enhanced error handling and validation.
        
        Args:
            symbol: Trading symbol
            stoploss: Stop loss price
            takeprofit: Take profit price
            direction: Order direction ('long', 'short', 'buy', 'sell')
            stake_amount: USD risk amount to be converted to lot size
            lot_size: Direct lot size (if provided, overrides stake_amount)
            deviation: Maximum price deviation
            magic: Magic number for the order
            
        Returns:
            Dictionary containing order result information
        """
        # Ensure symbol is available and selected
        try:
            self.select_symbols(symbol)
        except Exception as e:
            raise MT5SymbolError(f"Failed to select symbol {symbol}: {str(e)}")
        
        # Normalize direction
        direction = direction.lower()
        if direction in ['long', 'buy']:
            order_type = ORDER_TYPE.BUY
            direction_str = "BUY"
        elif direction in ['short', 'sell']:
            order_type = ORDER_TYPE.SELL
            direction_str = "SELL"
        else:
            raise MT5TradingError(f"Invalid direction: {direction}. Must be 'long', 'short', 'buy', or 'sell'")
        
        # Calculate lot size from stake amount or use provided lot size
        if lot_size is None:
            if stake_amount is None:
                raise MT5TradingError("Either stake_amount (USD risk) or lot_size must be provided")
            
            # Calculate lot size from USD stake amount
            try:
                calculated_lot_size = self.calculate_lot_size(symbol, stake_amount)
                logger.info(f"Calculated lot size {calculated_lot_size} from stake amount ${stake_amount}")
                lot_size = calculated_lot_size
            except Exception as e:
                logger.error(f"Failed to calculate lot size from stake amount: {e}")
                raise MT5TradingError(f"Failed to calculate lot size from stake amount ${stake_amount}: {e}")
        else:
            logger.info(f"Using provided lot size: {lot_size}")
        
        # Validate lot size
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise MT5SymbolError(f"Could not get symbol info for {symbol}")
        
        min_lot = symbol_info.volume_min
        max_lot = symbol_info.volume_max
        
        if lot_size < min_lot or lot_size > max_lot:
            raise MT5TradingError(f"Calculated lot size {lot_size} is outside allowed range [{min_lot}, {max_lot}]")
        
        # Normalize lot size to step
        lot_size = self.normalize_volume(symbol, lot_size)
        
        # Build order request
        filling, default_dev = self.default_filling_and_deviation(symbol)
        if self.default_filling is not None:
            filling = self.default_filling
        if deviation is None:
            deviation = default_dev
        order_params = create_trade_request(
            action=TRADE_ACTION.DEAL,
            symbol=symbol,
            volume=lot_size,
            type=order_type,
            deviation=deviation,
            magic=magic,
            type_time=ORDER_TIME.GTC,
            type_filling=filling,
            comment=f"MetaApi {direction_str} order",
        )
        
        # Add stop loss and take profit if provided, normalized and respecting minimum distance
        try:
            tick = mt5.symbol_info_tick(symbol)
            info = mt5.symbol_info(symbol)
            if tick is None or info is None:
                raise MT5SymbolError(f"Could not retrieve symbol data for {symbol}")

            current_price = tick.ask if order_type == ORDER_TYPE.BUY else tick.bid
            point = info.point or 0.0
            spread = (info.spread or 0) * point
            stop_level = (info.trade_stops_level or 0) * point
            min_distance = max(spread, stop_level)

            if stoploss is not None:
                sl = self.normalize_price(symbol, float(stoploss))
                # Enforce minimum distance and correct side of price
                if order_type == ORDER_TYPE.BUY:
                    # SL must be below current price by at least min_distance
                    required_sl = current_price - min_distance
                    if sl >= required_sl:
                        sl = self.normalize_price(symbol, required_sl)
                else:
                    # SL must be above current price by at least min_distance
                    required_sl = current_price + min_distance
                    if sl <= required_sl:
                        sl = self.normalize_price(symbol, required_sl)
                order_params["sl"] = sl

            if takeprofit is not None:
                tp = self.normalize_price(symbol, float(takeprofit))
                # Enforce minimum distance and correct side of price
                if order_type == ORDER_TYPE.BUY:
                    # TP must be above current price by at least min_distance
                    required_tp = current_price + min_distance
                    if tp <= required_tp:
                        tp = self.normalize_price(symbol, required_tp)
                else:
                    # TP must be below current price by at least min_distance
                    required_tp = current_price - min_distance
                    if tp >= required_tp:
                        tp = self.normalize_price(symbol, required_tp)
                order_params["tp"] = tp
        except Exception as e:
            logger.warning(f"Failed to normalize or enforce SL/TP for {symbol}: {e}")
            if stoploss is not None:
                order_params["sl"] = float(stoploss)
            if takeprofit is not None:
                order_params["tp"] = float(takeprofit)
        
        try:
            # Send the order
            result = self._send_order(order_params)
            
            if not result.success:
                error_msg = f"Failed to create market order for {symbol}: {result.comment}"
                raise MT5TradingError(error_msg, details=result.to_dict())
            
            logger.info(f"Market order placed successfully: {direction_str} {lot_size} lots of {symbol}")
            
            return {
                "success": True,
                "symbol": symbol,
                "direction": direction_str,
                "volume": lot_size,
                "comment": result.comment,
                "details": result.to_dict()
            }
            
        except MT5TradingError:
            raise
        except Exception as e:
            raise MT5TradingError(f"Unexpected error creating market order: {str(e)}")
    
    def close_all_open_positions(self, symbol: str = "") -> Tuple[List, List]:
        """
        Close all open positions for a specific symbol or all positions.

        Args:
            symbol (str): Trading symbol (e.g., 'EURUSD'). If empty, closes all positions.

        Returns:
            Tuple[List, List]: (closed_positions, unclosed_positions)
            
        Raises:
            MT5TradingError: If no positions found or closing fails
        """
        with self.ensure_connection():
            try:
                if symbol:
                    positions = mt5.positions_get(symbol=symbol)
                else:
                    positions = mt5.positions_get()

                if not positions:
                    raise MT5TradingError(f"No open positions found{' for symbol ' + symbol if symbol else ''}")

                all_closed_positions: List = []
                unclosed_positions: List[Dict] = []
                
                for position in positions:
                    try:
                        # Determine opposite order type to close position
                        close_type = ORDER_TYPE.SELL if position.type == POSITION_TYPE.BUY else ORDER_TYPE.BUY
                        position_type_str = 'BUY' if position.type == POSITION_TYPE.BUY else 'SELL'
                        
                        # Build close request
                        close_request = create_trade_request(
                            action=TRADE_ACTION.DEAL,
                            symbol=position.symbol,
                            volume=position.volume,
                            type=close_type,
                            position=position.ticket,
                            type_time=ORDER_TIME.GTC,
                            type_filling=ORDER_FILLING.FOK,
                            comment=f"Close {position_type_str} position {position.ticket}",
                        )

                        result = self._send_order(close_request)
                        
                        if result.success:
                            logger.info(f"Successfully closed position {position.ticket} ({position_type_str} {position.volume} {position.symbol})")
                            all_closed_positions.append(position)
                        else:
                            logger.warning(f"Failed to close position {position.ticket}: {result.comment}")
                            unclosed_positions.append({
                                "ticket": position.ticket,
                                "symbol": position.symbol,
                                "error": result.comment,
                                "details": result.to_dict()
                            })
                            
                    except Exception as e:
                        logger.error(f"Error closing position {position.ticket}: {e}")
                        unclosed_positions.append({
                            "ticket": position.ticket,
                            "symbol": position.symbol,
                            "error": str(e)
                        })

                return all_closed_positions, unclosed_positions
                
            except Exception as e:
                raise MT5TradingError(f"Failed to close positions: {str(e)}")

    def modify_order_sltp_percent(self, position, symbol: str, tp_dist: float, sl_dist: float) -> bool:
        entry_price = position.price_open
        position_type_str = 'long' if position.type == POSITION_TYPE.BUY else 'short'
        sl,tp = 0.0,0.0
        
        if position_type_str =='long':
            sl,tp = entry_price - (entry_price * sl_dist),entry_price + (entry_price * tp_dist)
        else:
            sl,tp = entry_price + (entry_price * sl_dist),entry_price - (entry_price * tp_dist)

        request = create_trade_request(
            action=TRADE_ACTION.SLTP,
            position=position.ticket,
            symbol=symbol,
            sl=self.normalize_price(symbol, sl),
            tp=self.normalize_price(symbol, tp),
        )
        
        logger.info(f"Sending modification request: {request}")
        result = self._send_order(request=request)
        if not result.success:
            logger.error("Error modifying TP & SL for position: %s", result.to_dict())
            logger.error("Failed position details: %s", position)
        else:
            logger.info(f"Take Profit & Stop Loss set for position #{position.ticket} ({position_type_str}, volume={position.volume}) at TP: {tp}, SL: {sl}")
            logger.info("Position details: %s",position)
        return result.success

    def modify_order_sltp(self, position, tp_price: float, sl_price: float) -> bool:
        entry_price = position.price_open
        symbol = position.symbol
        position_type_str = 'long' if position.type == POSITION_TYPE.BUY else 'short'
        
        request = create_trade_request(
            action=TRADE_ACTION.SLTP,
            position=position.ticket,
            symbol=symbol,
            sl=self.normalize_price(symbol, sl_price) if sl_price else 0.0,
            tp=self.normalize_price(symbol, tp_price) if tp_price else 0.0,
        )
        
        logger.info(f"Sending modification request: {request}")
        result = self._send_order(request=request)
        if not result.success:
            logger.error("Error modifying TP & SL for position: %s", result.to_dict())
            logger.error("Failed position details: %s", position)
        else:
            logger.info(f"Take Profit & Stop Loss set for position #{position.ticket} ({position_type_str}, volume={position.volume}) at TP: {tp_price}, SL: {sl_price}")
            logger.info("Position details: %s",position)
        return result.success
    
    @staticmethod
    def calculate_lot_size(symbol, risk_stake) -> float:
        """
        Calculate the lot size based on a fraction of the available account balance.

        :param symbol: Symbol to trade.
        :param fraction_of_balance: Fraction of balance to risk on trade.
        :return: Calculated lot size.
        """
        account_info = mt5.account_info()
        if account_info is None:
            logger.info("Failed to fetch account information.")
            return 0.01  # Return a default lot size
        
        balance = account_info.equity
        fraction_of_balance = risk_stake / balance
        lot_size_for_trade = (balance * fraction_of_balance) / mt5.symbol_info(symbol).ask

        # Depending on your broker's settings, you might need to adjust the lot size.
        # E.g., if your broker's minimum lot size increment is 0.01, round the lot size to the nearest 0.01.
        lot_size_for_trade = round(lot_size_for_trade, 2)
        return max(lot_size_for_trade, 0.01)

    
    @staticmethod
    def calculate_lot_size_contract(symbol: str,risk_stake: float,exit_price: float,entry_price: float = 0) -> float: #Position size in lot 
        """
            Calculate position size based on risk parameters.

            Args:
                - symbol (str): Trading symbol (e.g., 'EURUSD').
                - stop-loss (float): Stop-loss value.
                - per_to_risk (float): risk per trade in usd.

            Returns:
                float: Calculated position size.
        """
        symbol_info_tick = mt5.symbol_info_tick(symbol)
        symbol_info = mt5.symbol_info(symbol)

        current_price = (symbol_info_tick.bid + symbol_info_tick.ask) / 2 if not entry_price else entry_price
        tick_size = symbol_info.trade_tick_size

        risk_per_trade = risk_stake
        ticks_at_risk = abs(current_price - exit_price) / tick_size
        tick_value = symbol_info.trade_tick_value


        position_size = round(
            (risk_per_trade) / (ticks_at_risk * tick_value), 2
        )

        return position_size
    
    # This method is already implemented above with better error handling
    
    @staticmethod
    def compute_minimum_points(order_type : str, sl : float,symbol : str) -> float :
        symbol_info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)

        # Extract symbol details
        spread = symbol_info.spread * symbol_info.point
        stop_level = symbol_info.trade_stops_level * symbol_info.point
        minimum_price = max(spread, stop_level)

        return max(sl, minimum_price)

    def select_symbols(self, symbol: str):
        """Select and enable a symbol for trading."""
        with self.ensure_connection():
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise MT5SymbolError(f"Symbol {symbol} not found")
            
            if not symbol_info.visible:
                logger.info(f"Symbol {symbol} is not visible, attempting to enable")
                if not mt5.symbol_select(symbol, True):
                    raise MT5SymbolError(f"Failed to enable symbol {symbol}")
                logger.info(f"Successfully enabled symbol {symbol}")
            
            return True

    
    def get_terminal_info(self) -> Optional[TerminalInfo]:
        """Get MetaTrader 5 terminal information."""
        with self.ensure_connection():
            try:
                terminal_info = mt5.terminal_info()
                if terminal_info is None:
                    return None
                
                return create_terminal_info(terminal_info)
            except Exception as e:
                logger.error(f"Error getting terminal info: {e}")
                return None
    
    def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information using the account monitor."""
        with self.ensure_connection():
            return self.account.get_account_info()
    
    def get_positions(self, symbol: str = None) -> List[Position]:
        """Get open positions using the account monitor."""
        with self.ensure_connection():
            return self.account.get_positions(symbol)
    
    def get_orders(self, symbol: str = None) -> List[Order]:
        """Get pending orders using the account monitor."""
        with self.ensure_connection():
            return self.account.get_orders(symbol)
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get comprehensive portfolio summary."""
        with self.ensure_connection():
            return self.account.get_portfolio_summary()
    
    def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get symbol information using market data provider."""
        with self.ensure_connection():
            return self.market_data.get_symbol_info(symbol)
    
    def get_symbol_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current tick for symbol."""
        with self.ensure_connection():
            return self.market_data.get_symbol_tick(symbol)
    
    def get_rates(self, symbol: str, timeframe: Union[str, int], count: int = 500) -> Optional[pd.DataFrame]:
        """Get historical rates data."""
        with self.ensure_connection():
            return self.market_data.get_rates(symbol, timeframe, count)
    
    def get_ticks(self, symbol: str, count: int = 1000) -> Optional[pd.DataFrame]:
        """Get tick data."""
        with self.ensure_connection():
            return self.market_data.get_ticks(symbol, count)
    

    def check_connection(self) -> bool:
        """
        Check if MT5 connection is still active.
        Uses caching to avoid frequent checks.
        """
        current_time = time.time()
        
        # Use cached result if recent
        if current_time - self._last_connection_check < self._connection_check_interval:
            return self.is_connected
        
        # Check actual connection
        try:
            terminal_info = mt5.terminal_info()
            account_info = mt5.account_info()
            
            self.is_connected = (
                terminal_info is not None and 
                account_info is not None and 
                terminal_info.connected
            )
            
            self._last_connection_check = current_time
            
            if not self.is_connected:
                logger.warning("MT5 connection check failed")
            
            return self.is_connected
            
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            self.is_connected = False
            return False
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to MT5 if connection is lost."""
        try:
            logger.info("Attempting to reconnect to MT5...")
            
            # Shutdown current connection
            self.shutdown()
            
            # Re-initialize
            params = self.connection_params
            if all([params['account_id'], params['password'], params['server']]):
                self._initialize_with_login(
                    params['account_id'], 
                    params['password'], 
                    params['server'], 
                    params['path']
                )
            else:
                self._initialize_without_login(params['path'])
            
            if self.is_connected:
                logger.info("Successfully reconnected to MT5")
                return True
            else:
                logger.error("Failed to reconnect to MT5")
                return False
                
        except Exception as e:
            logger.error(f"Error during reconnection: {e}")
            return False
    
                
    
    # _parse_order_result is deprecated; unified via TradeResult in _send_order
    

    def close_position(
        self,
        ticket: int,
        volume: float = None,
        deviation: int = None,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Close a position by ticket.
        
        Args:
            ticket: Position ticket
            volume: Volume to close (None for full position)
            deviation: Maximum price deviation
            comment: Close comment
            
        Returns:
            Dictionary with close result information
        """
        with self.ensure_connection():
            try:
                # Get position info
                position = mt5.positions_get(ticket=ticket)
                if not position:
                    raise MT5TradingError(f"Position {ticket} not found")
                
                pos = position[0]
                
                # Set defaults
                if volume is None:
                    volume = pos.volume
                if deviation is None:
                    deviation = self.default_deviation
                
                # Determine close order type
                close_type = ORDER_TYPE.SELL if pos.type == POSITION_TYPE.BUY else ORDER_TYPE.BUY
                
                # Create close request
                request = create_trade_request(
                    action=TRADE_ACTION.DEAL,
                    symbol=pos.symbol,
                    volume=volume,
                    type=close_type,
                    position=ticket,
                    deviation=deviation,
                    magic=pos.magic,
                    comment=comment
                )
                
                # Send close order using unified path
                result = self._send_order(request)
                if not result.success:
                    raise MT5TradingError(f"Position close failed: {result.comment}")
                return result.to_dict()
                
            except Exception as e:
                logger.error(f"Error closing position {ticket}: {e}")
                raise MT5TradingError(f"Position close failed: {e}")
    
    
    def cancel_pending_order(self, ticket: int) -> Dict[str, Any]:
        """
        Cancel a pending order.
        
        Args:
            ticket: Order ticket
            
        Returns:
            Dictionary with cancellation result
        """
        with self.ensure_connection():
            try:
                # Get order info
                order = mt5.orders_get(ticket=ticket)
                if not order:
                    raise MT5TradingError(f"Order {ticket} not found")
                
                ord = order[0]
                
                # Create cancel request
                request = create_trade_request(
                    action=TRADE_ACTION.REMOVE,
                    order=ticket,
                    magic=ord.magic
                )
                
                # Send cancel request using unified path
                result = self._send_order(request)
                if not result.success:
                    raise MT5TradingError(f"Order cancellation failed: {result.comment}")
                return result.to_dict()
                
            except Exception as e:
                logger.error(f"Error cancelling order {ticket}: {e}")
                raise MT5TradingError(f"Order cancellation failed: {e}")
    
    
    
    @staticmethod
    def get_last_error(verbose: bool = True) -> dict:
        """
        Retrieve the last MT5 error with optional human-readable description.

        Args:
            verbose (bool): Whether to return description alongside the error code and message.

        Returns:
            dict: Dictionary containing 'code', 'message', and optionally 'description'.
        """
        code, message = mt5.last_error()
        error_info = {
            "code": code,
            "message": message
        }

        if verbose:
            description = MT5_ERROR_CODES.get(code, "Unknown error code")
            error_info["description"] = description

        return error_info