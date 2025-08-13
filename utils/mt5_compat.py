"""
MT5 compatibility wrapper to maintain original API behavior.
This ensures that the old request/response format is preserved.
"""

from typing import Union, Optional, Dict, List, Tuple
from .mt5_lib.modules import MT5_Interface as EnhancedMT5Interface
from core.exceptions import MT5TradingError


class MT5_Interface_Compat(EnhancedMT5Interface):
    """
    Compatibility wrapper for MT5_Interface that maintains original behavior.
    """
    
    def create_market_order_mt5(self, symbol: str, stoploss: Optional[float] = None, 
                                takeprofit: Optional[float] = None, direction: str = "long", 
                                stake_amount: float = None, lot_size: float = None, deviation: int = 5,
                                magic: int = 23400) -> bool:
        """
        Override to return boolean like original API instead of dict.
        This maintains backward compatibility with existing code.
        Now properly handles stake_amount (USD risk) to lot size conversion.
        """
        try:
            # Call the enhanced version with proper parameter handling
            result = super().create_market_order_mt5(
                symbol=symbol,
                stoploss=stoploss,
                takeprofit=takeprofit,
                direction=direction,
                stake_amount=stake_amount,
                lot_size=lot_size,
                deviation=deviation,
                magic=magic
            )
            
            # Return boolean for compatibility (original behavior)
            return result.get('success', True) if isinstance(result, dict) else True
            
        except MT5TradingError:
            # Re-raise as ConnectionRefusedError for original compatibility
            raise ConnectionRefusedError(f"Error creating market order for {symbol}")
    
    def close_all_open_positions(self, symbol: str = "") -> Tuple[List, List]:
        """
        Override to maintain original behavior for position closing.
        """
        try:
            return super().close_all_open_positions(symbol)
        except MT5TradingError as e:
            if "No open positions found" in str(e):
                # Re-raise as NameError for original compatibility  
                raise NameError(f"No positions found for symbol {symbol}")
            else:
                # Re-raise as ConnectionRefusedError for original compatibility
                raise ConnectionRefusedError(str(e))


# Create an alias to maintain the original import name
MT5_Interface = MT5_Interface_Compat
