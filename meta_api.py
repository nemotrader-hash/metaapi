import MetaTrader5 as mt5
from flask import Flask, request, jsonify
from functools import wraps

from mt5_lib import MT5_Interface
import logging 
import json 
import atexit

import time
from datetime import datetime, timezone
import telebot

from typing import Union, Optional, Dict 

from log.logger import setup_logger

logger = setup_logger()

app = Flask(__name__)

# Load config with error handling
try:
    with open("config.json", "r") as f:
        config = json.load(f)
        SECRET_KEY = config.get("secret_key")
        # Load Telegram config
        TELEGRAM_BOT_TOKEN = config.get("telegram_bot_token")
        TELEGRAM_CHAT_ID = int(config.get("telegram_chat_id"))  # Can be overridden in the request

        telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode="HTML")
        if not SECRET_KEY:
            raise KeyError("SECRET_KEY not found in config.")
        
except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
    logging.error(f"Failed to load SECRET_KEY: {e}")
    raise SystemExit("Unable to start server due to missing or invalid config.")


@app.route('/', methods=['GET'])
def welcome():
    return jsonify({'message': 'Hello! Welcome to the MT5 Flask API 🚀'}), 200

def authenticate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != SECRET_KEY:
                raise ValueError("Invalid token format or token mismatch.")
        except ValueError as e:
            logging.warning(f"Unauthorized access attempt: {e}")
            return jsonify({"error": "Invalid authorization token"}), 401

        return func(*args, **kwargs)

    return wrapper

@app.route('/initialize_mt5_connection', methods=['POST'])
@authenticate
def initialize_mt5_connection():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

    account_id = data.get('account_id')
    password = data.get('password')
    server_name = data.get('server')

    if not all((account_id, password, server_name)):
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        path = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
        mt5_interface = MT5_Interface(account_id=account_id, password=password, server=server_name, path=path)
        logger.info(f"Connected to MT5 account: {account_id}")
        return jsonify({'message': 'MT5 connection initialized successfully'}), 200
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return jsonify({'error': f"Failed to connect to MetaTrader: {e}", "message": "NOTOK"}), 400
    except Exception as e:
        logger.exception("Unexpected error initializing MT5 connection")
        return jsonify({'error': f"Internal Server Error: {e}", "message": "NOTOK"}), 500

@app.route('/create_mt5_orders', methods=['POST'])
@authenticate
def create_mt5_orders():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

    symbol = data.get('symbol')
    stake_amount: Optional[float] = round(float(data.get('stake_amount')), 2)
    direction: Optional[str] = data.get('side')

    if not all((symbol, stake_amount, direction)):
        return jsonify({'error': 'Missing parameters (symbol, direction, stake_amount)', "message": "NOTOK"}), 400

    mt5_interface = MT5_Interface(login=False)

    try:
        try:
            mt5_interface.select_symbols(symbol=symbol)
        except Exception as e:
            logger.warning(f"Failed to select symbols due to error: {e}")

        result = mt5_interface.create_market_order_mt5(symbol=symbol, direction=direction.lower()
                                                       ,lot_size=stake_amount)
    except (ConnectionError, ConnectionRefusedError, ValueError) as e:
        logger.error(f"Trade execution error for {symbol}: {e}")
        return jsonify({'error': str(e), "message": "NOTOK"}), 400
    except Exception as e:
        logger.exception(f"Unexpected error while placing MT5 order for symbol {symbol}")
        return jsonify({'error': f"Internal server error: {e}", "message": "NOTOK"}), 500

    return jsonify({'message': f"Successfully created positions for {symbol}"}), 200

@app.route('/close_mt5_orders', methods=['POST'])
@authenticate
def webhook_close_mt5_orders():
    data = request.json
    if not data:
        return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400
    
    symbol: str = data.get('symbol')
    if not all((symbol)):
        return jsonify({'error': 'Missing required parameters (symbol) in the JSON payload', "message":"NOTOK"}), 400
    
    try:
        mt5_interface = MT5_Interface(login=False)
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

    except ConnectionError as e:
        logger.warning(f"MT5 Connection error: {str(e)}")
        return jsonify({'error': f'Failed to initialize MetaTrader 5: {str(e)}', 'message': 'NOTOK'}), 400
    
    except NameError as e:
        logger.warning(f"Error Position Not Found for symbol {symbol}: {str(e)}")
        return jsonify({'message': f'No open positions found for symbol: {symbol}'}), 200

    except ConnectionRefusedError as e:
        logger.warning(f"Order closing error for symbol {symbol}: {str(e)}")
        return jsonify({'error': f'Failed to close position for symbol {symbol}: {str(e)}', 'message': 'NOTOK'}), 401

    except Exception as e:
        logger.exception(f"Unexpected error while closing MT5 orders for symbol {symbol}")
        return jsonify({'error': f'Internal server error: {str(e)}', 'message': 'NOTOK'}), 500

@app.route('/send_telegram_alert', methods=['POST'])
@authenticate
def send_telegram_alert():
    start_time = time.time()
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing JSON payload', "message": "NOTOK"}), 400

    alert_message = data.get("message", "🚨 Alert from MT5 Server")
    server_pin = data.get("ping", "Unknown")
    chat_id = data.get("chat_id", TELEGRAM_CHAT_ID)  # Optional override
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
    

def shutdown_mt5():
    try:
        logger.info("MT5 shutdown successfully.")
    except Exception as e:
        logger.warning(f"Failed to shutdown MT5: {e}")

atexit.register(shutdown_mt5)
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0",port=8087)
