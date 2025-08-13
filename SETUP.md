# 🚀 MetaApi Setup Guide

## 📋 Prerequisites

- Python 3.7+
- MetaTrader 5 installed
- Telegram Bot (optional, for alerts)

## ⚙️ Configuration Setup

### Step 1: Create Your Configuration File

```bash
# Copy the template to create your config
cp config.template.json config.json
```

### Step 2: Fill in Your Details

Edit `config.json` with your actual values:

```json
{
    "$schema": "2.0",
    "secret_key": "your-actual-secret-key",           // 🔑 Your API authentication key
    "telegram_bot_token": "your-bot-token",           // 🤖 From @BotFather
    "telegram_chat_id": "your-chat-id",               // 👤 Your Telegram chat ID
    "debug": false,                                   // 🐛 Set to true for development
    "host": "0.0.0.0",                               // 🌐 Server host (0.0.0.0 for all interfaces)
    "port": 8087,                                    // 🔌 Server port
    "mt5_path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe", // 📁 Your MT5 path
    "rate_limit_per_minute": 300,                    // 🛡️ Rate limiting (requests per minute)
    "request_timeout": 30,                           // ⏱️ Request timeout in seconds
    "log_level": "INFO",                             // 📝 Logging level (DEBUG, INFO, WARNING, ERROR)
    "features": {                                    // ⚡ Feature toggles
        "rate_limiting": true,
        "request_logging": true,
        "metrics_collection": true,
        "input_validation": true,
        "middleware": true
    }
}
```

### Step 3: How to Get Required Values

#### 🔑 Secret Key
- Choose a strong, unique string for API authentication
- Example: `"MySecureApiKey2024!"`

#### 🤖 Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the token (format: `123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ`)

#### 👤 Telegram Chat ID
1. Message your bot first
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response
4. Use that number as your chat ID

#### 📁 MT5 Path
- **Windows**: Usually `"C:\\Program Files\\MetaTrader 5\\terminal64.exe"`
- **Windows (32-bit)**: `"C:\\Program Files\\MetaTrader 5\\terminal.exe"`
- **Custom Installation**: Find where you installed MT5

## 🛡️ Security Best Practices

### ✅ Do's
- ✅ Use a strong, unique secret key
- ✅ Keep your `config.json` private
- ✅ Use environment variables for production
- ✅ Regularly rotate your API keys

### ❌ Don'ts
- ❌ Never commit `config.json` to version control
- ❌ Don't share your bot token publicly
- ❌ Don't use weak secret keys like "password123"
- ❌ Don't leave debug mode on in production

## 🧪 Testing Your Setup

### Test Configuration
```bash
# Use the test config for development
python3 app.py --config config.test.json
```

### Verify Setup
```bash
# Test the API
curl http://localhost:8087/

# Test with authentication
curl -H "Authorization: Bearer your-secret-key" http://localhost:8087/health
```

## 🚀 Production Deployment

### Environment Variables (Recommended)
Instead of `config.json`, use environment variables:

```bash
export METAAPI_SECRET_KEY="your-secret-key"
export METAAPI_TELEGRAM_BOT_TOKEN="your-bot-token"
export METAAPI_TELEGRAM_CHAT_ID="your-chat-id"
export METAAPI_DEBUG="false"
export METAAPI_LOG_LEVEL="INFO"

# Start the application
python3 app.py
```

### Multiple Instances
```bash
# Instance 1 - Demo trading
python3 launcher.py start -i demo -m "C:\Program Files\MetaTrader 5\terminal64.exe" -p 8087

# Instance 2 - Live trading  
python3 launcher.py start -i live -m "C:\Program Files\MetaTrader 5\terminal64.exe" -p 8088
```

## 📁 Available Configuration Files

- **`config.template.json`** - Template to copy from
- **`config.test.json`** - Safe test configuration with dummy values
- **`config.example.json`** - Example in the config/ directory
- **`config.json`** - Your actual configuration (create this)

## 🆘 Troubleshooting

### Configuration Not Found
```bash
# Make sure config.json exists
ls -la config.json

# Or specify a different config
python3 app.py --config config.test.json
```

### Invalid Telegram Setup
```bash
# Test your bot token
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

### MT5 Path Issues
```bash
# Verify MT5 path exists
ls -la "C:\Program Files\MetaTrader 5\terminal64.exe"  # Windows
```

## 🔄 Configuration Validation

The application automatically validates your configuration on startup and will show clear error messages if something is wrong.

---

**🎉 You're all set! Your MetaApi is ready to use securely.**
