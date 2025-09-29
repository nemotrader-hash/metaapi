"""
API routes for MetaApi - maintaining backward compatibility with original format.
All request/response formats remain exactly the same as the original API.
"""

import time
from datetime import datetime, timezone
from typing import Optional

import telebot
from flask import request, jsonify

from config.config_manager import config_manager
from core.exceptions import (
    MT5ConnectionError, 
    MT5AuthenticationError,
    MT5TradingError, 
    ValidationError,
    TelegramError
)
from core.validators import (
    validate_mt5_connection_data,
    validate_market_order_data, 
    validate_close_order_data,
    validate_telegram_alert_data
)
from utils.mt5_compat import MT5_Interface
from log.logger import setup_logger
from api.auth import authenticate

# Initialize logger
logger = setup_logger()

# Load configuration
config = config_manager.load_config()

# Initialize Telegram bot
try:
    telegram_bot = telebot.TeleBot(config.telegram_bot_token, parse_mode="HTML")
    TELEGRAM_CHAT_ID = config.telegram_chat_id
    logger.info("Telegram bot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Telegram bot: {e}")
    telegram_bot = None
    TELEGRAM_CHAT_ID = None


def init_routes(app):
    """Initialize API routes (simple, no middleware)."""
    
    @app.route('/', methods=['GET'])
    def welcome():
        """Welcome endpoint."""
        return jsonify({'message': 'Hello! Welcome to the MT5 Flask API 🚀'}), 200
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        from datetime import datetime, timezone
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0",
            "features": {
                "middleware": False,
                "validation": True,
                "rate_limiting": False,
                "metrics": False,
                "backward_compatible": True,
                "advanced_trading": True
            }
        }
        
        return jsonify({'message': 'Service is healthy','data': health_data}), 200


    @app.route('/initialize_mt5_connection', methods=['POST'])
    @authenticate
    def initialize_mt5_connection():
        """Initialize MT5 connection."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

        try:
            # Use enhanced validation but catch errors to maintain original format
            connection_request = validate_mt5_connection_data(data)
            account_id = connection_request.account_id
            password = connection_request.password
            server_name = connection_request.server
            
        except ValidationError as e:
            # Convert validation errors to original format
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': 'Missing required parameters'}), 400

        try:
            path = config.mt5_path
            mt5_interface = MT5_Interface(
                login=True,
                account_id=account_id, 
                password=password, 
                server=server_name, 
                path=path
            )
            logger.info(f"Connected to MT5 account: {account_id}")
            return jsonify({'message': 'MT5 connection initialized successfully'}), 200
            
        except (MT5ConnectionError, MT5AuthenticationError) as e:
            logger.error(f"Connection error: {e}")
            return jsonify({'error': f"Failed to connect to MetaTrader: {e}", "message": "NOTOK"}), 400
        except Exception as e:
            logger.exception("Unexpected error initializing MT5 connection")
            return jsonify({'error': f"Internal Server Error: {e}", "message": "NOTOK"}), 500

    @app.route('/create_mt5_orders', methods=['POST'])
    @authenticate
    def create_mt5_orders():
        """Create MT5 orders."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

        try:
            # Use enhanced validation but catch errors to maintain original format
            order_request = validate_market_order_data(data)
            symbol = order_request.symbol
            stake_amount = order_request.stake_amount
            direction = order_request.side
            
        except ValidationError as e:
            # Convert validation errors to original format
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': 'Missing parameters (symbol, direction, stake_amount)', "message": "NOTOK"}), 400

        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            
            # Try to select symbols - log warning but continue if fails
            try:
                mt5_interface.select_symbols(symbol=symbol)
            except Exception as e:
                logger.warning(f"Failed to select symbols due to error: {e}")

            # Create the market order - stake_amount is USD risk, not lot size
            result = mt5_interface.create_market_order_mt5(
                symbol=symbol, 
                direction=direction.lower(),
                stake_amount=stake_amount  # This is USD risk amount, will be converted to lot size
            )
            
        except (MT5ConnectionError, MT5TradingError, ValueError) as e:
            logger.error(f"Trade execution error for {symbol}: {e}")
            return jsonify({'error': str(e), "message": "NOTOK"}), 400
        except Exception as e:
            logger.exception(f"Unexpected error while placing MT5 order for symbol {symbol}")
            return jsonify({'error': f"Internal server error: {e}", "message": "NOTOK"}), 500

        return jsonify({'message': f"Successfully created positions for {symbol}"}), 200

    @app.route('/close_mt5_orders', methods=['POST'])
    @authenticate
    def webhook_close_mt5_orders():
        """Close MT5 orders."""
        data = request.json
        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400
        
        try:
            # Use enhanced validation but catch errors to maintain original format
            close_request = validate_close_order_data(data)
            symbol = close_request.symbol
            
        except ValidationError as e:
            # Convert validation errors to original format
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': 'Missing required parameters (symbol) in the JSON payload', "message":"NOTOK"}), 400
        
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            closed_positions, unclosed_positions = mt5_interface.close_all_open_positions(symbol=symbol)
            
            if unclosed_positions:
                return jsonify({
                    'error': f'Some positions could not be closed for symbol: {symbol}',
                    'details': unclosed_positions,
                    'message': 'NOTOK'
                }), 400

            return jsonify({
                'message': f'Successfully closed all open positions for {symbol}',
                'details': len(closed_positions)
            }), 200

        except MT5ConnectionError as e:
            logger.warning(f"MT5 Connection error: {str(e)}")
            return jsonify({'error': f'Failed to initialize MetaTrader 5: {str(e)}', 'message': 'NOTOK'}), 400
        
        except MT5TradingError as e:
            if "no positions found" in str(e).lower():
                logger.warning(f"Error Position Not Found for symbol {symbol}: {str(e)}")
                return jsonify({'message': f'No open positions found for symbol: {symbol}'}), 200
            else:
                logger.warning(f"Order closing error for symbol {symbol}: {str(e)}")
                return jsonify({'error': f'Failed to close position for symbol {symbol}: {str(e)}', 'message': 'NOTOK'}), 401

        except Exception as e:
            logger.exception(f"Unexpected error while closing MT5 orders for symbol {symbol}")
            return jsonify({'error': f'Internal server error: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/send_telegram_alert', methods=['POST'])
    @authenticate
    def send_telegram_alert():
        """Send Telegram alert."""
        if not telegram_bot:
            return jsonify({'error': 'Telegram bot not configured', 'message': 'NOTOK'}), 500
            
        start_time = time.time()
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

        try:
            # Use enhanced validation but catch errors to maintain original format
            alert_request = validate_telegram_alert_data(data)
            alert_message = alert_request.message
            server_pin = alert_request.ping
            chat_id = alert_request.chat_id or TELEGRAM_CHAT_ID
            include_timestamp = alert_request.include_timestamp
            
        except ValidationError as e:
            # For telegram alerts, we're more lenient and use defaults
            logger.warning(f"Validation warning (using defaults): {e}")
            alert_message = data.get("message", "🚨 Alert from MT5 Server")
            server_pin = data.get("ping", "Unknown")
            chat_id = data.get("chat_id", TELEGRAM_CHAT_ID)
            include_timestamp = data.get("include_timestamp", True)

        try:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC") if include_timestamp else ""
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            full_message = (
                f"<b>🔔 ALERT</b>\n"
                f"<b>Server PIN:</b> <code>{server_pin}</code>\n"
                f"<b>Message:</b> <pre>{alert_message}</pre>\n"
                f"<b>⏱️ Response Time:</b> {elapsed_ms} ms\n"
                f"{f'<b>Update: </b> {now}' if now else ''}"
            )

            telegram_bot.send_message(chat_id, full_message)
            logger.info(f"Sent alert to Telegram for server {server_pin}")
            return jsonify({'message': 'Alert sent to Telegram successfully'}), 200

        except Exception as e:
            logger.error(f"Failed to send alert to Telegram: {e}")
            return jsonify({'error': f'Failed to send alert: {str(e)}', 'message': 'NOTOK'}), 500

    # ======= NEW MT5 ENDPOINTS =======
    
    @app.route('/place_limit_order', methods=['POST'])
    @authenticate
    def place_limit_order():
        """Place limit/stop orders."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

        # Required fields
        required_fields = ['order_type', 'symbol', 'volume', 'price']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({'error': f'Missing required parameters: {", ".join(missing_fields)}', "message": "NOTOK"}), 400

        order_type = data.get('order_type')  # BUY_LIMIT, SELL_LIMIT, BUY_STOP, SELL_STOP
        symbol = data.get('symbol')
        volume = float(data.get('volume'))
        price = float(data.get('price'))
        stop_loss = data.get('stop_loss', 0.0)
        take_profit = data.get('take_profit', 0.0)
        comment = data.get('comment', 'Limit/Stop order')

        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            
            result = mt5_interface.place_limit_stop_order(
                order_type=order_type,
                symbol=symbol,
                volume=volume,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment
            )
            
            if result:
                return jsonify({'message': f'Successfully placed {order_type} order for {symbol}'}), 200
            else:
                return jsonify({'error': f'Failed to place {order_type} order for {symbol}', "message": "NOTOK"}), 400
                
        except Exception as e:
            logger.exception(f"Error placing limit/stop order for {symbol}")
            return jsonify({'error': f'Internal server error: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/get_positions', methods=['GET'])
    @authenticate
    def get_positions():
        """Get open positions."""
        symbol = request.args.get('symbol')  # Optional filter by symbol
        
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            
            if symbol:
                positions = mt5_interface.get_orders_position(symbol)
            else:
                # Get all positions by passing empty string
                positions = mt5_interface.get_orders_position("")
            
            # Convert positions to dict format
            positions_data = []
            for pos in positions:
                if hasattr(pos, 'to_dict'):
                    positions_data.append(pos.to_dict())
                else:
                    positions_data.append(pos.__dict__)
            
            return jsonify({
                'message': 'Positions retrieved successfully',
                'positions': positions_data,
                'count': len(positions_data)
            }), 200
            
        except Exception as e:
            logger.exception("Error retrieving positions")
            return jsonify({'error': f'Failed to retrieve positions: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/get_account_info', methods=['GET'])
    @authenticate
    def get_account_info():
        """Get account information."""
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            account_info = mt5_interface.get_account_info()
            
            if account_info:
                if hasattr(account_info, 'to_dict'):
                    account_data = account_info.to_dict()
                else:
                    account_data = account_info.__dict__
                
                return jsonify({
                    'message': 'Account info retrieved successfully',
                    'account': account_data
                }), 200
            else:
                return jsonify({'error': 'Failed to retrieve account information', 'message': 'NOTOK'}), 400
                
        except Exception as e:
            logger.exception("Error retrieving account info")
            return jsonify({'error': f'Failed to retrieve account info: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/cancel_all_orders', methods=['POST'])
    @authenticate
    def cancel_all_orders():
        """Cancel all pending orders."""
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            cancelled_orders = mt5_interface.cancel_all_open_orders()
            
            return jsonify({
                'message': f'Successfully cancelled {len(cancelled_orders)} orders',
                'cancelled_orders': cancelled_orders,
                'count': len(cancelled_orders)
            }), 200
            
        except Exception as e:
            logger.exception("Error cancelling orders")
            return jsonify({'error': f'Failed to cancel orders: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/modify_position_sltp', methods=['POST'])
    @authenticate
    def modify_position_sltp():
        """Modify stop loss and take profit for a position."""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

        ticket = data.get('ticket')
        tp_price = data.get('take_profit')
        sl_price = data.get('stop_loss')
        
        if not ticket:
            return jsonify({'error': 'Missing required parameter: ticket', "message": "NOTOK"}), 400
        
        if tp_price is None and sl_price is None:
            return jsonify({'error': 'At least one of take_profit or stop_loss must be provided', "message": "NOTOK"}), 400

        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            
            # Get all positions to find the one with matching ticket
            all_positions = mt5_interface.get_orders_position("")
            position = None
            for pos in all_positions:
                if hasattr(pos, 'ticket') and pos.ticket == int(ticket):
                    position = pos
                    break
            
            if not position:
                return jsonify({'error': f'Position with ticket {ticket} not found', "message": "NOTOK"}), 404
            
            result = mt5_interface.modify_order_sltp(
                position=position,
                tp_price=tp_price,
                sl_price=sl_price
            )
            
            if result:
                return jsonify({'message': f'Successfully modified SL/TP for position {ticket}'}), 200
            else:
                return jsonify({'error': f'Failed to modify SL/TP for position {ticket}', "message": "NOTOK"}), 400
                
        except Exception as e:
            logger.exception(f"Error modifying position {ticket}")
            return jsonify({'error': f'Internal server error: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/get_symbol_info', methods=['GET'])
    @authenticate
    def get_symbol_info():
        """Get symbol information."""
        symbol = request.args.get('symbol')
        if not symbol:
            return jsonify({'error': 'Missing required parameter: symbol', "message": "NOTOK"}), 400
        
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            symbol_info = mt5_interface.get_symbol_info(symbol)
            
            if symbol_info:
                if hasattr(symbol_info, 'to_dict'):
                    symbol_data = symbol_info.to_dict()
                else:
                    symbol_data = symbol_info.__dict__
                
                return jsonify({
                    'message': f'Symbol info for {symbol} retrieved successfully',
                    'symbol_info': symbol_data
                }), 200
            else:
                return jsonify({'error': f'Symbol {symbol} not found', 'message': 'NOTOK'}), 404
                
        except Exception as e:
            logger.exception(f"Error retrieving symbol info for {symbol}")
            return jsonify({'error': f'Failed to retrieve symbol info: {str(e)}', 'message': 'NOTOK'}), 500

    @app.route('/get_terminal_info', methods=['GET'])
    @authenticate
    def get_terminal_info():
        """Get MT5 terminal information."""
        try:
            mt5_interface = MT5_Interface(login=False, path=config.mt5_path)
            terminal_info = mt5_interface.get_terminal_info()
            
            if terminal_info:
                if hasattr(terminal_info, 'to_dict'):
                    terminal_data = terminal_info.to_dict()
                else:
                    terminal_data = terminal_info.__dict__
                
                return jsonify({
                    'message': 'Terminal info retrieved successfully',
                    'terminal_info': terminal_data
                }), 200
            else:
                return jsonify({'error': 'Failed to retrieve terminal information', 'message': 'NOTOK'}), 400
                
        except Exception as e:
            logger.exception("Error retrieving terminal info")
            return jsonify({'error': f'Failed to retrieve terminal info: {str(e)}', 'message': 'NOTOK'}), 500
