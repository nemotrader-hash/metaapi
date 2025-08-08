import MetaTrader5 as mt5
import logging 

from dataclasses import dataclass, field, asdict
from typing import Optional, Union

# Get the root logger configured by `log/logger.py`
logger = logging.getLogger()

@dataclass
class OrderPosition:
    ticket: Optional[int] = None
    time: Optional[Union[int, float]] = None
    type: Optional[int] = None
    magic: Optional[int] = None
    identifier: Optional[str] = None
    reason: Optional[int] = None
    volume: Optional[float] = None
    price_open: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    price_current: Optional[float] = None
    swap: Optional[float] = None
    profit: Optional[float] = None
    symbol: Optional[str] = None
    comment: Optional[str] = None

    # Custom class identifier
    identifier_class: str = field(init=False, default="OrderPosition")

    def __repr__(self):
        return f"OrderPosition({', '.join([f'{k}={v}' for k, v in asdict(self).items()])})"

    def __eq__(self, other):
        if isinstance(other, OrderPosition):
            return asdict(self) == asdict(other)
        return False

    def update_from_dict(self, data: dict):
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self):
        result = asdict(self)
        result["__type__"] = self.identifier_class
        return result

    @classmethod
    def from_dict(cls, data: dict):
        if data.get("__type__") == cls.__name__:
            data = {k: v for k, v in data.items() if k != "__type__"}
            return cls(**data)
        return data


class TradePosition:
    identifier_class = "TradePosition"

    def __init__(self, data: dict):

        """
        Initialize the OrderPosition class with a dictionary.
        Set each dictionary key as an attribute of the class.
        """
        self.identifier_class = "TradePosition"

        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self):
        """
        Custom string representation to display all attributes and values.
        """
        return f"TradePosition({', '.join([f'{key}={value}' for key, value in self.__dict__.items()])})"

    def __eq__(self, other):
        if isinstance(other, TradePosition):
            return self.__dict__ == other.__dict__
        return False
    
    def update_from_dict(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)
    
    def to_dict(self):
        """Convert the object's attributes back into a dictionary and include the identifier."""
        result = self.__dict__.copy()
        result['__type__'] = self.identifier_class  # Add identifier
        #print(f"Serialized as: {result}")  # Debug log to see what's happening
        return result

    @classmethod
    def from_dict(cls, data: dict):
        """Create an TradePosition instance from a dictionary."""
        #print(f"Deserializing: {data}")  # Debug log to check the data
        if '__type__' in data and data['__type__'] == cls.identifier_class:
            data.pop('__type__')  # Remove identifier
            return cls(data)
        return data

