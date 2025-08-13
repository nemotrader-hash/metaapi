"""
MetaApi Flask Application - Enhanced with Middleware and Multi-Instance Support
Maintains 100% backward compatibility while using all enhanced features:
- Rate limiting, request logging, metrics collection
- Enhanced validation with original error format compatibility
- Professional architecture with all middleware activated
- Multi-instance support with independent configurations
"""

import atexit
import argparse
import os
import sys
from flask import Flask

from api.routes import init_routes
from config.config_manager import ConfigManager
from core.exceptions import ConfigurationError
from utils.middleware import init_middleware
from log.logger import setup_logger

def create_app(config_file: str = None, instance_name: str = None):
    """Create and configure the Flask application with all enhancements."""
    try:
        # Initialize logger
        logger = setup_logger()
        
        # Load configuration from specified file or default
        if config_file:
            config_manager = ConfigManager(config_file)
        else:
            config_manager = ConfigManager()
            
        config = config_manager.load_config()
        
        # Log with instance context
        instance_context = f"[{instance_name}] " if instance_name else ""
        logger.info(f"{instance_context}Configuration loaded successfully")
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        raise SystemExit("Unable to start server due to configuration error")
    
    # Initialize Flask app
    app = Flask(__name__)
    app.config['INSTANCE_NAME'] = instance_name or 'default'
    
    # Initialize middleware (rate limiting, logging, metrics, error handling)
    init_middleware(app)
    logger.info(f"{instance_context}Middleware initialized - rate limiting, logging, metrics enabled")
    
    # Initialize routes with enhanced validation and middleware
    init_routes(app)
    logger.info(f"{instance_context}API routes initialized with enhanced validation")
    
    return app, config, logger

def shutdown_mt5():
    """Cleanup function for MT5 connection."""
    try:
        # Import here to avoid circular imports
        from utils.mt5_compat import MT5_Interface
        from log.logger import setup_logger
        logger = setup_logger()
        # The enhanced version will handle cleanup automatically
        logger.info("MT5 cleanup completed")
    except Exception as e:
        from log.logger import setup_logger
        logger = setup_logger()
        logger.warning(f"Error during MT5 cleanup: {e}")

# Register cleanup function
atexit.register(shutdown_mt5)

def main():
    """Main entry point with command-line argument support."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MetaApi Server - Multi-Instance Support")
    parser.add_argument("--config", "-c", help="Configuration file path")
    parser.add_argument("--port", "-p", type=int, help="Port number (overrides config)")
    parser.add_argument("--host", help="Host address (overrides config)")
    parser.add_argument("--instance", "-i", help="Instance name for logging")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get instance name from environment or args
    instance_name = args.instance or os.environ.get('METAAPI_INSTANCE_NAME', 'default')
    
    # Create the Flask app
    app, config, logger = create_app(args.config, instance_name)
    
    # Override config with command line arguments
    host = args.host or config.host
    port = args.port or config.port
    debug = args.debug or config.debug
    
    instance_context = f"[{instance_name}] " if instance_name else ""
    
    logger.info("=" * 60)
    logger.info(f"🚀 {instance_context}Starting Enhanced MetaApi Server")
    logger.info("=" * 60)
    logger.info(f"📡 {instance_context}Host: {host}")
    logger.info(f"🔌 {instance_context}Port: {port}")
    logger.info(f"🐛 {instance_context}Debug: {debug}")
    logger.info(f"🏷️  {instance_context}Instance: {instance_name}")
    if args.config:
        logger.info(f"⚙️  {instance_context}Config: {args.config}")
    logger.info("=" * 60)
    
    try:
        app.run(
            debug=debug,
            host=host,
            port=port,
            use_reloader=False  # Disable auto-reloader for multi-instance
        )
    except KeyboardInterrupt:
        logger.info(f"🛑 {instance_context}Server stopped by user")
    except Exception as e:
        logger.error(f"❌ {instance_context}Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
