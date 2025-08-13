import MetaTrader5 as mt5
import logging
import pandas as pd
import datetime
import time
from contextlib import contextmanager

from .base import OrderPosition, TradePosition
from typing import Union, Optional, Dict, List, Tuple, Any
from .utils import ERROR_CODES
from datetime import timedelta

from log.logger import setup_logger
from core.exceptions import (
    MT5ConnectionError, 
    MT5AuthenticationError, 
    MT5TradingError, 
    MT5SymbolError,
    MetaApiError
)

logger = setup_logger()


class MT5_Interface():
    def __init__(self, login=True, account_id: Optional[Union[str, int]] = None, password: Optional[str] = None, 
                 server: Optional[str] = None, path: Optional[str] = "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
                 max_retries: int = 3, retry_delay: float = 1.0):
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
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_connected = False
        self.account_info = None
        
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


    def _send_order(self, request: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Send the order to the broker with enhanced error handling."""
        with self.ensure_connection():
            # Validate request before sending
            if not self.check_order(request):
                error_info = self.get_last_error()
                raise MT5TradingError(
                    f"Order validation failed for {request.get('symbol', 'unknown')}: {error_info['description']}",
                    code=error_info['code']
                )
            
            try:
                result = mt5.order_send(request)
                
                if result is None:
                    error_info = self.get_last_error()
                    logger.error(f"Order send returned None: {error_info}")
                    return False, None, error_info
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    logger.error(f"Order failed for {request.get('symbol')}: {result.comment} (code: {result.retcode})")
                    return False, result.comment, {
                        "retcode": result.retcode,
                        "deal": result.deal,
                        "order": result.order,
                        "volume": result.volume,
                        "price": result.price,
                        "bid": result.bid,
                        "ask": result.ask,
                        "comment": result.comment,
                        "request_id": result.request_id
                    }
                
                logger.info(f"Order successful for {request.get('symbol')}: {result.comment}")
                return True, result.comment, {
                    "deal": result.deal,
                    "order": result.order,
                    "volume": result.volume,
                    "price": result.price
                }
                
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
        timeframes = {
            #Scalping Timeframes        #Intraday Timeframes          #Swing Timeframes
            '1m' : mt5.TIMEFRAME_M1,    "15m" : mt5.TIMEFRAME_M15,  '3h' : mt5.TIMEFRAME_H3,
            '3m' : mt5.TIMEFRAME_M3,    "30m" : mt5.TIMEFRAME_M30,  '4h' : mt5.TIMEFRAME_H4,
            '5m' : mt5.TIMEFRAME_M5,    '1h' : mt5.TIMEFRAME_H1,    '1d' : mt5.TIMEFRAME_D1,
        }
        rates = mt5.copy_rates_from_pos(symbol, timeframes.get(timeframe,"5m"), 0, count)
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

        # Determine the order type
        if order_type == "SELL_STOP":
            order_type_mt5 = mt5.ORDER_TYPE_SELL_STOP
        elif order_type == "BUY_STOP":
            order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP
        elif order_type == "BUY_LIMIT":
            order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
        elif order_type == "SELL_LIMIT":
            order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
        else:
            raise ValueError("Invalid Order Type")

        # Create the request
        order_params = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": order_type_mt5,
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "type_filling": mt5.ORDER_FILLING_RETURN,
            "type_time": mt5.ORDER_TIME_GTC,
            "comment": comment
        }

        # Send the order to MT5
        try:
            success, comment, details = self._send_order(order_params)
            
            if success:
                logger.info(f"{order_type} order for {symbol} placed successfully")
                return True
            else:
                logger.error(f"Error placing {order_type} order: {comment}")
                return False
                
        except (MT5TradingError, MT5ConnectionError) as e:
            logger.error(f"Failed to place {order_type} order for {symbol}: {e}")
            return False

    
    @staticmethod
    def get_orders_position(symbol,only_id=True) -> list:
        positions = mt5.positions_get(symbol=symbol)
        all_positions_dict : list = []
        if positions is None or len(positions) == 0:
            return []
        for position in positions:
            position_dict = position._asdict()
            all_positions_dict.append(OrderPosition(position_dict))

        return all_positions_dict
    
    @staticmethod
    def get_history_position(position_id) -> list:
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
                    cancel_params = {
                        "action": mt5.TRADE_ACTION_REMOVE,
                        "order": order.ticket,
                        "comment": "Order cancelled by MetaApi"
                    }
                    
                    success, comment, details = self._send_order(cancel_params)
                    
                    if success:
                        logger.info(f"Successfully cancelled order {order.ticket}")
                        all_cancelled_orders.append({
                            "ticket": order.ticket,
                            "symbol": order.symbol,
                            "type": order.type,
                            "volume": order.volume_initial
                        })
                    else:
                        logger.error(f"Failed to cancel order {order.ticket}: {comment}")
                        failed_cancellations.append({
                            "ticket": order.ticket,
                            "error": comment
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
            order_type = mt5.ORDER_TYPE_BUY
            direction_str = "BUY"
        elif direction in ['short', 'sell']:
            order_type = mt5.ORDER_TYPE_SELL
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
        lot_step = symbol_info.volume_step
        
        if lot_size < min_lot or lot_size > max_lot:
            raise MT5TradingError(f"Calculated lot size {lot_size} is outside allowed range [{min_lot}, {max_lot}]")
        
        # Round lot size to step
        lot_size = round(lot_size / lot_step) * lot_step
        
        # Build order request
        order_params = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "deviation": deviation,
            "magic": magic,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
            "comment": f"MetaApi {direction_str} order"
        }
        
        # Add stop loss and take profit if provided
        if stoploss is not None:
            order_params["sl"] = stoploss
        if takeprofit is not None:
            order_params["tp"] = takeprofit
        
        try:
            # Send the order
            success, comment, details = self._send_order(order_params)
            
            if not success:
                error_msg = f"Failed to create market order for {symbol}: {comment}"
                raise MT5TradingError(error_msg, details=details)
            
            logger.info(f"Market order placed successfully: {direction_str} {lot_size} lots of {symbol}")
            
            return {
                "success": True,
                "symbol": symbol,
                "direction": direction_str,
                "volume": lot_size,
                "comment": comment,
                "details": details
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
                        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
                        position_type_str = 'BUY' if position.type == mt5.POSITION_TYPE_BUY else 'SELL'
                        
                        # Build close request
                        close_request = {
                            "action": mt5.TRADE_ACTION_DEAL,
                            "symbol": position.symbol,
                            "volume": position.volume,
                            "type": close_type,
                            "position": position.ticket,
                            "type_time": mt5.ORDER_TIME_GTC,
                            "type_filling": mt5.ORDER_FILLING_FOK,
                            "comment": f"Close {position_type_str} position {position.ticket}"
                        }

                        success, comment, details = self._send_order(close_request)
                        
                        if success:
                            logger.info(f"Successfully closed position {position.ticket} ({position_type_str} {position.volume} {position.symbol})")
                            all_closed_positions.append(position)
                        else:
                            logger.warning(f"Failed to close position {position.ticket}: {comment}")
                            unclosed_positions.append({
                                "ticket": position.ticket,
                                "symbol": position.symbol,
                                "error": comment,
                                "details": details
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
        position_type_str = 'long' if position.type == mt5.POSITION_TYPE_BUY else 'short'
        sl,tp = 0.0,0.0
        
        if position_type_str =='long':
            sl,tp = entry_price - (entry_price * sl_dist),entry_price + (entry_price * tp_dist)
        else:
            sl,tp = entry_price + (entry_price * sl_dist),entry_price - (entry_price * tp_dist)

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": symbol,
            "sl": sl,
            "tp": tp,
        }
        
        logger.info(f"Sending modification request: {request}")
        order_bool, order_result = self._send_order(request=request)
        if not order_bool:
            logger.error("Error modifying TP & SL for position: %s", self.get_last_error() if not order_result else order_result)
            logger.error("Failed position details: %s", position)
        else:
            logger.info(f"Take Profit & Stop Loss set for position #{position.ticket} ({position_type_str}, volume={position.volume}) at TP: {tp}, SL: {sl}")
            logger.info("Position details: %s",position)
        return order_bool

    def modify_order_sltp(self, position, tp_price: float, sl_price: float) -> bool:
        entry_price = position.price_open
        symbol = position.symbol
        position_type_str = 'long' if position.type == mt5.POSITION_TYPE_BUY else 'short'
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": symbol,
            **({"sl": sl_price} if sl_price else {}),
            **({"tp": tp_price} if tp_price else {})
            }
        
        logger.info(f"Sending modification request: {request}")
        order_bool, order_result = self._send_order(request=request)
        if not order_bool :
            logger.error("Error modifying TP & SL for position: %s", self.get_last_error() if not order_result else order_result)
            logger.error("Failed position details: %s", position)
        else:
            logger.info(f"Take Profit & Stop Loss set for position #{position.ticket} ({position_type_str}, volume={position.volume}) at TP: {tp_price}, SL: {sl_price}")
            logger.info("Position details: %s",position)
        return order_bool
    
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
            description = ERROR_CODES.get(code, "Unknown error code")
            error_info["description"] = description

        return error_info