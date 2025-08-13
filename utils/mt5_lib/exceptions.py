"""
Custom MT5 exceptions for the mt5_lib package.

These exceptions decouple the library from external exception modules and
provide a consistent error interface with optional error codes and details.
"""

from typing import Optional, Dict, Any


class MetaApiError(Exception):
    """Base error for MetaApi/MT5 related failures."""

    def __init__(
        self,
        message: str,
        *,
        code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details
        self.original_exception = original_exception

    def __str__(self) -> str:  # pragma: no cover - simple convenience
        base = self.message
        if self.code is not None:
            base = f"[code={self.code}] {base}"
        return base


class MT5Error(MetaApiError):
    """Base class for MT5-specific errors."""


class MT5ConnectionError(MT5Error):
    """Errors related to MT5 connection/terminal availability."""


class MT5AuthenticationError(MT5Error):
    """Authentication or authorization failures when logging into MT5."""


class MT5TradingError(MT5Error):
    """Trading-related errors (validation, order send/close, etc.)."""


class MT5SymbolError(MT5Error):
    """Symbol lookup/selection/visibility errors."""


__all__ = [
    "MetaApiError",
    "MT5Error",
    "MT5ConnectionError",
    "MT5AuthenticationError",
    "MT5TradingError",
    "MT5SymbolError",
]


