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

### 1. Setup Configuration

```bash
# Copy template and edit with your details
cp config.template.json config.json
# Edit config.json with your actual values (see SETUP.md for details)
```

**🔐 Important**: Your `config.json` with real secrets is automatically ignored by git!

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
Update `config.json` or use environment variables:
```bash
export SECRET_KEY="your-secret-key"
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### 4. Run Application

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
    "stake_amount": 100.0,  # USD risk amount (automatically converted to lot size)
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
| `/mt5/info` | GET | MT5 terminal & account info | Terminal status, account details, connection status |
| `/mt5/symbols` | GET | Available trading symbols | All symbols with metadata, trade modes |
| `/mt5/positions` | GET | Current open positions | Real-time position data with P&L |
| `/mt5/orders` | GET | Pending orders | All pending orders with details |

**All original endpoints maintain exact same request/response format while gaining enhanced features!**

## 🛡️ Features

- **✅ Backward Compatible**: All existing requests work unchanged
- **🏗️ Clean Architecture**: Organized, maintainable code structure
- **🔧 Enhanced Error Handling**: Custom exceptions and detailed errors
- **📝 Input Validation**: Comprehensive request validation
- **💰 Smart Position Sizing**: Automatic USD risk to lot size conversion
- **🔐 Secure**: Bearer token authentication
- **📊 Logging**: Structured logging with request tracking
- **🌐 Environment Support**: JSON config + environment variables
- **📖 Type Safe**: Full type hints throughout

## 💰 **Smart Position Sizing**

The API now intelligently converts USD risk amounts to appropriate lot sizes:

```python
# Specify risk in USD, not lot size
data = {
    "symbol": "EURUSD",
    "stake_amount": 100.0,  # Risk $100 on this trade
    "side": "long"
}

# The API will:
# 1. Get your account balance
# 2. Calculate appropriate lot size for $100 risk
# 3. Validate against broker min/max limits
# 4. Execute the trade with proper position sizing
```

**Benefits:**
- ✅ **Consistent Risk**: Same dollar risk regardless of account size
- ✅ **Automatic Calculation**: No manual lot size calculations needed
- ✅ **Account-Aware**: Considers your actual account balance
- ✅ **Broker-Safe**: Validates against broker lot size limits

## 🚀 **Multi-Instance Support**

Run multiple MetaApi instances simultaneously with different configurations:

### Quick Start - Multiple Instances

```bash
# Install psutil for process management
pip install psutil

# Start multiple instances (must provide MT5 path)
python3 launcher.py start --instance demo1 --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8087
python3 launcher.py start --instance demo2 --mt5-path "/path/to/mt5/terminal64.exe" --port 8088
python3 launcher.py start --instance live1 --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8089

# Check all instances
python3 launcher.py list
```

### Launcher Commands

```bash
# Create and start instance (MT5 path required)
python3 launcher.py start -i <instance_name> -m <mt5_path> [-p <port>] [-c <config_file>]

# List all instances
python3 launcher.py list

# Stop specific instance  
python3 launcher.py stop -i <instance_name>

# Stop all instances
python3 launcher.py stop --all

# Remove instance
python3 launcher.py remove -i <instance_name>

# Check status
python3 launcher.py status
```

### Instance Features

- ✅ **Automatic Port Assignment**: No port conflicts
- ✅ **User-Provided MT5 Paths**: You specify your own MT5 installation  
- ✅ **Individual Configurations**: Per-instance settings
- ✅ **Process Management**: Start/stop/monitor instances
- ✅ **Automatic Cleanup**: Proper resource management

### Use Cases

```bash
# Different trading accounts
python3 launcher.py start -i demo_account --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8087
python3 launcher.py start -i live_account --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8088

# Multiple strategies
python3 launcher.py start -i scalping_bot --mt5-path "/path/to/mt5/terminal64.exe" --port 8089  
python3 launcher.py start -i swing_bot --mt5-path "/path/to/mt5/terminal64.exe" --port 8090

# Testing environments
python3 launcher.py start -i test_env --mt5-path "C:\\Program Files\\MetaTrader 5\\terminal64.exe" --port 8091
```

**Each instance runs independently with its own:**
- 🔧 Configuration file (`instances/<name>_config.json`)
- 📁 User-provided MT5 installation path (no auto-creation)
- 📝 Log file (`instances/<name>.log`)
- 🔢 Process ID tracking (`instances/<name>.pid`)

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
- **`launcher.py`** - Multi-instance launcher
- **`requirements.txt`** - Python dependencies
- **`SETUP.md`** - Detailed setup guide

### 🔧 Configuration Files

- **`config.template.json`** - ✅ **Safe template** (copy this to create your config)
- **`config.test.json`** - ✅ **Test config** with dummy values (safe for testing)
- **`config.json`** - 🔐 **Your actual config** (automatically ignored by git)
- **`config/config.example.json`** - ✅ **Another example** in config directory

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
