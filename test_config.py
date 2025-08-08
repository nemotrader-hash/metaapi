"""
Simple test to verify the enhanced configuration works correctly.
"""

try:
    from config.config_manager import config_manager
    
    print("🔧 Testing Enhanced Configuration...")
    
    # Load configuration
    config = config_manager.load_config()
    
    print(f"✅ Secret Key: {config.secret_key}")
    print(f"✅ Telegram Chat ID: {config.telegram_chat_id}")
    print(f"✅ Host: {config.host}")
    print(f"✅ Port: {config.port}")
    print(f"✅ Rate Limit: {config.rate_limit_per_minute} req/min")
    print(f"✅ Log Level: {config.log_level}")
    
    print("\n🚀 Enhanced Features:")
    print(f"  - Rate Limiting: {config.features.rate_limiting}")
    print(f"  - Request Logging: {config.features.request_logging}")
    print(f"  - Metrics Collection: {config.features.metrics_collection}")
    print(f"  - Input Validation: {config.features.input_validation}")
    print(f"  - Middleware: {config.features.middleware}")
    
    print("\n🎉 Configuration loaded successfully!")
    print("✅ Enhanced config with feature flags working")
    
except Exception as e:
    print(f"❌ Configuration error: {e}")
