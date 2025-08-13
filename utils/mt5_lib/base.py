"""
Base classes and legacy models for MetaTrader 5 integration.
This module maintains backward compatibility while providing enhanced functionality.
"""

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # Will be handled gracefully in the code
import logging 

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Union, List, Dict, Tuple, Any

# Import enhanced models
from .models import Position

# Get the root logger configured by `log/logger.py`
logger = logging.getLogger(__name__)


# Legacy models for backward compatibility
@dataclass  
class OrderPosition(Position):
    """
    Legacy OrderPosition model - now inherits from enhanced Position model.
    
    This class provides backward compatibility while leveraging the enhanced
    Position model with calculated fields and better functionality.
    """
    identifier_class: str = field(init=False, default="OrderPosition")
    
    def update_from_dict(self, data: dict):
        """Legacy method for updating from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self):
        """Legacy method for converting to dictionary."""
        result = asdict(self)
        result["__type__"] = self.identifier_class
        return result

    @classmethod
    def from_dict(cls, data: dict):
        """Legacy method for creating from dictionary."""
        if data.get("__type__") == "OrderPosition":
            data = {k: v for k, v in data.items() if k != "__type__"}
            return cls(**data)
        return data


class TradePosition:
    """
    Legacy TradePosition model for backward compatibility.
    
    This class maintains the original dictionary-based interface
    for existing code that depends on it.
    """
    identifier_class = "TradePosition"

    def __init__(self, data: dict):
        """
        Initialize with dictionary data (legacy behavior).
        Set each dictionary key as an attribute of the class.
        """
        self.identifier_class = "TradePosition"
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        """Custom string representation to display all attributes and values."""
        return f"TradePosition({', '.join([f'{key}={value}' for key, value in self.__dict__.items()])})"

    def __eq__(self, other):
        """Check equality with another TradePosition."""
        if isinstance(other, TradePosition):
            return self.__dict__ == other.__dict__
        return False
    
    def update_from_dict(self, data: dict):
        """Update from dictionary (legacy behavior)."""
        for key, value in data.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert to dictionary with identifier (legacy behavior)."""
        result = self.__dict__.copy()
        result['__type__'] = self.identifier_class
        return result

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (legacy behavior)."""
        if '__type__' in data and data['__type__'] == cls.identifier_class:
            data.pop('__type__')
            return cls(data)
        return data


# Export legacy models for backward compatibility
__all__ = [
    'OrderPosition',
    'TradePosition'
]