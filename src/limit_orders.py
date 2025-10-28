import logging
from typing import Dict
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

def place_limit_order(client, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = 'GTC') -> Dict:
    """
    Place a limit order

    Args:
        symbol: Trading pair
        side: 'BUY' or 'SELL'
        quantity: Order quantity
        price: Limit price
        time_in_force: GTC (Good Till Cancel), IOC, FOK

    Returns:
        Order response dictionary
    """
    params = {
        'symbol': symbol.upper(),
        'side': side.upper(),
        'type': 'LIMIT',
        'quantity': quantity,
        'price': price,
        'timeInForce': time_in_force
    }

    try:
        # self._log_request("LIMIT_ORDER", params) # Corrected line
        order = client.futures_create_order(
            symbol=params['symbol'],
            side=params['side'],
            type=params['type'],
            quantity=params['quantity'],
            price=params['price'],
            timeInForce=params['timeInForce']
        )
        # self._log_response("LIMIT_ORDER", order)
        logger.info(f"[OK] Limit {side} order placed: {symbol} @ {price}")
        return order
    except BinanceAPIException as e:
        # self._log_error("LIMIT_ORDER", e) # Corrected line
        raise