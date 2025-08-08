"""
MetaApi Flask Application - Enhanced with Middleware
Maintains 100% backward compatibility while using all enhanced features:
- Rate limiting, request logging, metrics collection
- Enhanced validation with original error format compatibility
- Professional architecture with all middleware activated
"""

import atexit
from flask import Flask

from api.routes import init_routes
from config.config_manager import config_manager
from core.exceptions import ConfigurationError
from utils.middleware import init_middleware
from log.logger import setup_logger

# Initialize logger
logger = setup_logger()

# Initialize Flask app
app = Flask(__name__)

def create_app():
    """Create and configure the Flask application with all enhancements."""
    try:
        # Load configuration
        config = config_manager.load_config()
        logger.info("Configuration loaded successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise SystemExit("Unable to start server due to configuration error")
    
    # Initialize middleware (rate limiting, logging, metrics, error handling)
    init_middleware(app)
    logger.info("Middleware initialized - rate limiting, logging, metrics enabled")
    
    # Initialize routes with enhanced validation and middleware
    init_routes(app)
    logger.info("API routes initialized with enhanced validation")
    
    return app, config

def shutdown_mt5():
    """Cleanup function for MT5 connection."""
    try:
        # Import here to avoid circular imports
        from utils.mt5_compat import MT5_Interface
        # The enhanced version will handle cleanup automatically
        logger.info("MT5 cleanup completed")
    except Exception as e:
        logger.warning(f"Error during MT5 cleanup: {e}")

# Register cleanup function
atexit.register(shutdown_mt5)

if __name__ == '__main__':
    app, config = create_app()
    
    logger.info("Starting MetaApi server (backward compatible)...")
    logger.info(f"Server will run on {config.host}:{config.port}")
    
    app.run(
        debug=config.debug,
        host=config.host,
        port=config.port
    )
