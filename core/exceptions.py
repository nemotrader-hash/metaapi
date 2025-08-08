"""
Custom exception classes for MetaApi application.
Provides specific error types for better error handling and debugging.
"""

class MetaApiError(Exception):
    """Base exception class for MetaApi application."""
    
    def __init__(self, message: str, code: int = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details
        }


class MT5ConnectionError(MetaApiError):
    """Raised when MT5 connection fails."""
    pass


class MT5AuthenticationError(MetaApiError):
    """Raised when MT5 authentication fails."""
    pass


class MT5TradingError(MetaApiError):
    """Raised when MT5 trading operations fail."""
    pass


class MT5SymbolError(MetaApiError):
    """Raised when symbol-related operations fail."""
    pass


class ValidationError(MetaApiError):
    """Raised when input validation fails."""
    pass


class ConfigurationError(MetaApiError):
    """Raised when configuration is invalid or missing."""
    pass


class TelegramError(MetaApiError):
    """Raised when Telegram operations fail."""
    pass


class RateLimitError(MetaApiError):
    """Raised when rate limits are exceeded."""
    pass
