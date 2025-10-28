import logging
from typing import Dict
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

def place_market_order(client, symbol: str, side: str, quantity: float) -> Dict:
    """
    Place a market order

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        side: 'BUY' or 'SELL'
        quantity: Order quantity

    Returns:
        Order response dictionary
    """
    params = {
        'symbol': symbol.upper(),
        'side': side.upper(),
        'type': 'MARKET',
        'quantity': quantity
    }

    try:
        # self._log_request("MARKET_ORDER", params) # Corrected line
        order = client.futures_create_order(
            symbol=params['symbol'],
            side=params['side'],
            type=params['type'],
            quantity=params['quantity']
        )
        # self._log_response("MARKET_ORDER", order)
        logger.info(f"[OK] Market {side} order placed: {symbol} @ {quantity}")
        return order
    except BinanceAPIException as e:
        # self._log_error("MARKET_ORDER", e) # Corrected line
        raise