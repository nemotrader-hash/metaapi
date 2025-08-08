# MetaApi - Enhanced Professional Trading API

A clean, organized, and production-ready Flask API for MetaTrader 5 trading operations with **100% backward compatibility** and **full enhanced features activated**:

## 🚀 **Enhanced Features Now Active**
- ✅ **Rate Limiting** - Prevents API abuse (configurable limits)
- ✅ **Request Logging** - Detailed request/response tracking with unique IDs
- ✅ **Metrics Collection** - Performance monitoring and usage analytics  
- ✅ **Input Validation** - Enhanced security with sanitization
- ✅ **Error Handling** - Better error tracking while maintaining original format
- ✅ **Health Monitoring** - New `/health` and `/metrics` endpoints
- ✅ **Middleware** - Professional request/response processing
- ✅ **Type Safety** - Full type validation throughout

## 🏗️ Clean Architecture

```
MetaApi/
├── 📁 api/                    # API Layer
│   ├── __init__.py
│   ├── auth.py               # Authentication decorators
│   └── routes.py             # All API endpoints
├── 📁 config/                 # Configuration
│   ├── __init__.py
│   ├── config_manager.py     # Config loading (JSON + ENV)
│   └── env.example           # Environment template
├── 📁 core/                   # Business Logic
│   ├── __init__.py
│   ├── exceptions.py         # Custom exceptions
│   ├── models.py             # Data models
│   └── validators.py         # Input validation
├── 📁 utils/                  # External Services
│   ├── __init__.py
│   ├── middleware.py         # Request/response middleware
│   ├── mt5_compat.py         # Backward compatibility
│   └── mt5_lib/              # Enhanced MT5 interface
├── 📁 docs/                   # Documentation
├── 📁 log/                    # Logging
│   └── logger.py
├── app.py                    # 🚀 Main application (NEW)
├── meta_api.py               # ✅ Original API (preserved)
├── config.json               # ✅ Original config
├── requirements.txt          # Dependencies
└── test_compatibility.py     # Compatibility tests
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
Update `config.json` or use environment variables:
```bash
export SECRET_KEY="your-secret-key"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### 3. Run Application

**New Organized Version (Recommended):**
```bash
python3 app.py
```

**Original Version (Still Available):**
```bash
python3 meta_api.py
```

## 🔄 100% Backward Compatibility

All existing client code works unchanged:

```python
import requests

headers = {"Authorization": "Bearer your-secret-key"}

# Initialize MT5 - SAME REQUEST FORMAT
data = {
    "account_id": "12345678",
    "password": "your-password",
    "server": "YourBroker-Demo"
}
response = requests.post("http://localhost:8087/initialize_mt5_connection", 
                        headers=headers, json=data)

# Create Orders - SAME REQUEST FORMAT
data = {
    "symbol": "EURUSD",
    "stake_amount": 0.01,
    "side": "long"
}
response = requests.post("http://localhost:8087/create_mt5_orders", 
                        headers=headers, json=data)

# Close Orders - SAME REQUEST FORMAT
data = {"symbol": "EURUSD"}
response = requests.post("http://localhost:8087/close_mt5_orders", 
                        headers=headers, json=data)

# Telegram Alerts - SAME REQUEST FORMAT
data = {
    "message": "Alert message",
    "ping": "SERVER-001",
    "include_timestamp": True
}
response = requests.post("http://localhost:8087/send_telegram_alert", 
                        headers=headers, json=data)
```

## 📚 API Endpoints

### 🔄 Original Endpoints (Enhanced)
| Endpoint | Method | Description | Enhanced Features |
|----------|--------|-------------|-------------------|
| `/` | GET | Welcome message | ✅ Metrics collection |
| `/initialize_mt5_connection` | POST | Connect to MT5 | ✅ Rate limiting, validation, logging |
| `/create_mt5_orders` | POST | Create market orders | ✅ Rate limiting, validation, metrics |
| `/close_mt5_orders` | POST | Close positions | ✅ Rate limiting, validation, logging |
| `/send_telegram_alert` | POST | Send alerts | ✅ Rate limiting, validation, metrics |

### 🆕 New Enhanced Endpoints
| Endpoint | Method | Description | Features |
|----------|--------|-------------|----------|
| `/health` | GET | Service health check | Real-time status, feature flags |
| `/metrics` | GET | API performance metrics | Request counts, response times, errors |

**All original endpoints maintain exact same request/response format while gaining enhanced features!**

## 🛡️ Features

- **✅ Backward Compatible**: All existing requests work unchanged
- **🏗️ Clean Architecture**: Organized, maintainable code structure
- **🔧 Enhanced Error Handling**: Custom exceptions and detailed errors
- **📝 Input Validation**: Comprehensive request validation
- **🔐 Secure**: Bearer token authentication
- **📊 Logging**: Structured logging with request tracking
- **🌐 Environment Support**: JSON config + environment variables
- **📖 Type Safe**: Full type hints throughout

## 🧪 Testing

**Test backward compatibility:**
```bash
python3 test_compatibility.py
```

**Demo all enhanced features:**
```bash
python3 demo_enhanced_features.py
```

This will show:
- ✅ All original requests work exactly the same
- ✅ Enhanced features active: rate limiting, validation, logging
- ✅ New endpoints: `/health`, `/metrics`
- ✅ Enhanced headers: Request-ID, Response-Time
- ✅ Middleware working in background

## 📁 Key Files

- **`app.py`** - Main application (new organized version)
- **`meta_api.py`** - Original API (preserved for compatibility)
- **`config.json`** - Configuration file
- **`requirements.txt`** - Python dependencies
- **`test_compatibility.py`** - Backward compatibility tests

## 🔧 Enhanced Configuration

**Option 1: JSON File (`config.json`)**
```json
{
    "$schema": "2.0",
    "secret_key": "your-secret-key",
    "telegram_bot_token": "your-bot-token",
    "telegram_chat_id": "your-chat-id",
    "debug": false,
    "host": "0.0.0.0",
    "port": 8087,
    "rate_limit_per_minute": 300,
    "request_timeout": 30,
    "log_level": "INFO",
    "features": {
        "rate_limiting": true,
        "request_logging": true,
        "metrics_collection": true,
        "input_validation": true,
        "middleware": true
    }
}
```

**Option 2: Environment Variables**
```bash
export SECRET_KEY="your-secret-key"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
export RATE_LIMIT_PER_MINUTE=300
export RATE_LIMITING=true
export REQUEST_LOGGING=true
export METRICS_COLLECTION=true
```

**Option 3: Copy Example Files**
```bash
# For JSON config
cp config/config.example.json config.json

# For environment config  
cp config/env.example .env
```

## 🎯 Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Structure** | Single file | Organized modules |
| **Maintainability** | Difficult | Easy |
| **Documentation** | None | Comprehensive |
| **Error Handling** | Basic | Advanced |
| **Type Safety** | None | Full coverage |
| **Client Impact** | N/A | **Zero changes required** |

## 📞 Support

- All existing integrations continue working without modification
- Enhanced error messages for better debugging
- Structured logging for easier troubleshooting
- Clean architecture for easier maintenance and extension

---

**Perfect backward compatibility + Professional architecture = Zero deprecation errors!** 🎉
