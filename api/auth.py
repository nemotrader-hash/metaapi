"""
Authentication module for MetaApi.
Maintains the exact same authentication behavior as the original API.
"""

import logging
from functools import wraps
from flask import request, jsonify

from config.config_manager import config_manager

# Load configuration
config = config_manager.get_config()


def authenticate(func):
    """
    Authentication decorator - maintains exact original behavior.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        try:
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer" or parts[1] != config.secret_key:
                raise ValueError("Invalid token format or token mismatch.")
        except ValueError as e:
            logging.warning(f"Unauthorized access attempt: {e}")
            return jsonify({"error": "Invalid authorization token"}), 401

        return func(*args, **kwargs)

    return wrapper
