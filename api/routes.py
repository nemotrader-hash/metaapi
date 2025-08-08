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
from utils.middleware import rate_limit, log_request_response, collect_metrics
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
    """Initialize all API routes with enhanced features."""
    
    @app.route('/', methods=['GET'])
    @collect_metrics()
    def welcome():
        """Welcome endpoint - enhanced with metrics while maintaining original format."""
        return jsonify({'message': 'Hello! Welcome to the MT5 Flask API 🚀'}), 200
    
    @app.route('/health', methods=['GET'])
    @collect_metrics()
    def health_check():
        """Health check endpoint - new enhanced feature."""
        from datetime import datetime, timezone
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "2.0",
            "features": {
                "middleware": True,
                "validation": True,
                "rate_limiting": True,
                "metrics": True,
                "backward_compatible": True
            }
        }
        
        return jsonify({
            'message': 'Service is healthy',
            'data': health_data
        }), 200
    
    @app.route('/metrics', methods=['GET'])
    @authenticate
    @collect_metrics()
    def get_metrics():
        """Get API metrics - new enhanced feature."""
        from utils.middleware import request_metrics
        
        metrics_data = request_metrics.get_metrics()
        
        return jsonify({
            'message': 'API metrics retrieved successfully',
            'data': metrics_data
        }), 200

    @app.route('/initialize_mt5_connection', methods=['POST'])
    @authenticate
    @rate_limit()
    @log_request_response(include_request_data=True)
    @collect_metrics()
    def initialize_mt5_connection():
        """Initialize MT5 connection - enhanced with validation while maintaining exact original format."""
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
    @rate_limit()
    @log_request_response(include_request_data=True)
    @collect_metrics()
    def create_mt5_orders():
        """Create MT5 orders - enhanced with validation while maintaining exact original format."""
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

            # Create the market order - the method now returns dict but we ignore it for compatibility
            result = mt5_interface.create_market_order_mt5(
                symbol=symbol, 
                direction=direction.lower(),
                lot_size=stake_amount
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
    @rate_limit()
    @log_request_response(include_request_data=True)
    @collect_metrics()
    def webhook_close_mt5_orders():
        """Close MT5 orders - enhanced with validation while maintaining exact original format."""
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
            if "No open positions found" in str(e):
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
    @rate_limit()
    @log_request_response(include_request_data=True)
    @collect_metrics()
    def send_telegram_alert():
        """Send Telegram alert - enhanced with validation while maintaining exact original format."""
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
