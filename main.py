"""
Binance Futures Testnet Trading Bot
A comprehensive trading bot with support for multiple order types
"""

import logging
import json
from typing import Optional, Dict, List
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time, os, dotenv

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BinanceFuturesBot:
    """Trading bot for Binance Futures Testnet"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        Initialize the trading bot
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            testnet: Use testnet (default: True)
        """
        self.client = Client(api_key, api_secret, testnet=testnet)
        
        if testnet:
            self.client.API_URL = 'https://testnet.binancefuture.com'
            logger.info("Connected to Binance Futures Testnet")
        else:
            logger.warning("Connected to Binance LIVE environment")
        
        self._validate_connection()
    
    def _validate_connection(self):
        """Validate API connection and permissions"""
        try:
            self.client.futures_account()
            logger.info("API connection validated successfully")
        except BinanceAPIException as e:
            logger.error(f"API connection failed: {e}")
            raise
    
    def _log_request(self, action: str, params: Dict):
        """Log API request details"""
        logger.info(f"REQUEST - {action}: {json.dumps(params, indent=2)}")
    
    def _log_response(self, action: str, response: Dict):
        """Log API response details"""
        logger.info(f"RESPONSE - {action}: {json.dumps(response, indent=2)}")
    
    def _log_error(self, action: str, error: Exception):
        """Log error details"""
        logger.error(f"ERROR - {action}: {str(error)}")
    
    def get_account_info(self) -> Dict:
        """Get futures account information"""
        try:
            self._log_request("GET_ACCOUNT", {})
            account = self.client.futures_account()
            self._log_response("GET_ACCOUNT", account)
            return account
        except BinanceAPIException as e:
            self._log_error("GET_ACCOUNT", e)
            raise
    
    def get_balance(self) -> List[Dict]:
        """Get account balance"""
        try:
            account = self.get_account_info()
            balances = [asset for asset in account['assets'] if float(asset['walletBalance']) > 0]
            logger.info(f"Account balances: {json.dumps(balances, indent=2)}")
            return balances
        except Exception as e:
            self._log_error("GET_BALANCE", e)
            raise
    
    def get_symbol_info(self, symbol: str) -> Dict:
        """Get symbol information and trading rules"""
        try:
            exchange_info = self.client.futures_exchange_info()
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    return s
            raise ValueError(f"Symbol {symbol} not found")
        except Exception as e:
            self._log_error("GET_SYMBOL_INFO", e)
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol.upper())
            price = float(ticker['price'])
            logger.info(f"{symbol} current price: {price}")
            return price
        except Exception as e:
            self._log_error("GET_CURRENT_PRICE", e)
            raise
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
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
            self._log_request("MARKET_ORDER", params)
            order = self.client.futures_create_order(
                symbol=params['symbol'],
                side=params['side'],
                type=params['type'],
                quantity=params['quantity']
            )
            self._log_response("MARKET_ORDER", order)
            logger.info(f"✓ Market {side} order placed: {symbol} @ {quantity}")
            return order
        except BinanceAPIException as e:
            self._log_error("MARKET_ORDER", e)
            raise
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, 
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
            self._log_request("LIMIT_ORDER", params)
            order = self.client.futures_create_order(
                symbol=params['symbol'],
                side=params['side'],
                type=params['type'],
                quantity=params['quantity'],
                price=params['price'],
                timeInForce=params['timeInForce']
            )
            self._log_response("LIMIT_ORDER", order)
            logger.info(f"✓ Limit {side} order placed: {symbol} @ {price}")
            return order
        except BinanceAPIException as e:
            self._log_error("LIMIT_ORDER", e)
            raise
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              stop_price: float, limit_price: float,
                              time_in_force: str = 'GTC') -> Dict:
        """
        Place a stop-limit order
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            stop_price: Stop trigger price
            limit_price: Limit price after trigger
            time_in_force: GTC, IOC, FOK
            
        Returns:
            Order response dictionary
        """
        params = {
            'symbol': symbol.upper(),
            'side': side.upper(),
            'type': 'STOP',
            'quantity': quantity,
            'price': limit_price,
            'stopPrice': stop_price,
            'timeInForce': time_in_force
        }
        
        try:
            self._log_request("STOP_LIMIT_ORDER", params)
            order = self.client.futures_create_order(
                symbol=params['symbol'],
                side=params['side'],
                type=params['type'],
                quantity=params['quantity'],
                price=params['price'],
                stopPrice=params['stopPrice'],
                timeInForce=params['timeInForce']
            )
            self._log_response("STOP_LIMIT_ORDER", order)
            logger.info(f"✓ Stop-Limit {side} order placed: {symbol} @ stop:{stop_price}, limit:{limit_price}")
            return order
        except BinanceAPIException as e:
            self._log_error("STOP_LIMIT_ORDER", e)
            raise
    
    def place_twap_order(self, symbol: str, side: str, total_quantity: float, 
                        duration_minutes: int, num_slices: int) -> List[Dict]:
        """
        Place TWAP (Time-Weighted Average Price) orders
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            total_quantity: Total quantity to trade
            duration_minutes: Total duration in minutes
            num_slices: Number of order slices
            
        Returns:
            List of order responses
        """
        orders = []
        slice_quantity = total_quantity / num_slices
        interval_seconds = (duration_minutes * 60) / num_slices
        
        logger.info(f"Starting TWAP: {total_quantity} {symbol} over {duration_minutes}m in {num_slices} slices")
        
        for i in range(num_slices):
            try:
                logger.info(f"TWAP slice {i+1}/{num_slices}")
                order = self.place_market_order(symbol, side, slice_quantity)
                orders.append(order)
                
                if i < num_slices - 1:  # Don't wait after last order
                    time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"TWAP slice {i+1} failed: {e}")
                break
        
        logger.info(f"TWAP completed: {len(orders)}/{num_slices} orders executed")
        return orders
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            
            logger.info(f"Open orders: {len(orders)}")
            return orders
        except Exception as e:
            self._log_error("GET_OPEN_ORDERS", e)
            raise
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Cancel an open order"""
        try:
            result = self.client.futures_cancel_order(
                symbol=symbol.upper(),
                orderId=order_id
            )
            logger.info(f"✓ Order {order_id} cancelled")
            return result
        except Exception as e:
            self._log_error("CANCEL_ORDER", e)
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders for a symbol"""
        try:
            result = self.client.futures_cancel_all_open_orders(symbol=symbol.upper())
            logger.info(f"✓ All orders cancelled for {symbol}")
            return result
        except Exception as e:
            self._log_error("CANCEL_ALL_ORDERS", e)
            raise
    
    def get_position_info(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get current position information"""
        try:
            positions = self.client.futures_position_information(symbol=symbol.upper() if symbol else None)
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]
            logger.info(f"Active positions: {len(active_positions)}")
            return active_positions
        except Exception as e:
            self._log_error("GET_POSITION_INFO", e)
            raise


def print_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("   BINANCE FUTURES TESTNET TRADING BOT")
    print("="*60)
    print("1.  View Account Balance")
    print("2.  Get Current Price")
    print("3.  Place Market Order")
    print("4.  Place Limit Order")
    print("5.  Place Stop-Limit Order")
    print("6.  Place TWAP Order (Advanced)")
    print("7.  View Open Orders")
    print("8.  Cancel Order")
    print("9.  Cancel All Orders")
    print("10. View Positions")
    print("0.  Exit")
    print("="*60)


def main():
    """Main CLI interface"""
    print("\n" + "="*60)
    print("   BINANCE FUTURES TRADING BOT - SETUP")
    print("="*60)
    
    # Get API credentials
    if os.getenv("BINANCE_API_KEY"):
        api_key = os.getenv("BINANCE_API_KEY")
    else:
        api_key = input("Enter your Binance API Key: ").strip()
    
    if os.getenv("BINANCE_SECRET_KEY"):
        api_secret = os.getenv("BINANCE_SECRET_KEY")
    else:
        api_secret = input("Enter your Binance API Secret: ").strip()
    
    if not api_key or not api_secret:
        print("❌ API credentials are required!")
        return
    
    try:
        # Initialize bot
        bot = BinanceFuturesBot(api_key, api_secret, testnet=True)
        print("✓ Bot initialized successfully!")
        
        while True:
            print_menu()
            choice = input("\nEnter your choice: ").strip()
            
            try:
                if choice == '0':
                    print("\n👋 Exiting bot. Happy trading!")
                    break
                
                elif choice == '1':
                    # View balance
                    balances = bot.get_balance()
                    print("\n💰 Account Balances:")
                    for asset in balances:
                        print(f"   {asset['asset']}: {asset['walletBalance']} (Available: {asset['availableBalance']})")
                
                elif choice == '2':
                    # Get current price
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    price = bot.get_current_price(symbol)
                    print(f"\n📊 {symbol}: ${price}")
                
                elif choice == '3':
                    # Market order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = float(input("Enter quantity: ").strip())
                    
                    confirm = input(f"\nConfirm {side} {quantity} {symbol} at MARKET? (y/n): ")
                    if confirm.lower() == 'y':
                        order = bot.place_market_order(symbol, side, quantity)
                        print(f"\n✓ Order placed! Order ID: {order['orderId']}")
                        print(f"   Status: {order['status']}")
                
                elif choice == '4':
                    # Limit order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = float(input("Enter quantity: ").strip())
                    price = float(input("Enter limit price: ").strip())
                    
                    confirm = input(f"\nConfirm {side} {quantity} {symbol} @ ${price}? (y/n): ")
                    if confirm.lower() == 'y':
                        order = bot.place_limit_order(symbol, side, quantity, price)
                        print(f"\n✓ Order placed! Order ID: {order['orderId']}")
                        print(f"   Status: {order['status']}")
                
                elif choice == '5':
                    # Stop-limit order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = float(input("Enter quantity: ").strip())
                    stop_price = float(input("Enter stop price: ").strip())
                    limit_price = float(input("Enter limit price: ").strip())
                    
                    confirm = input(f"\nConfirm {side} {quantity} {symbol} @ stop:${stop_price}, limit:${limit_price}? (y/n): ")
                    if confirm.lower() == 'y':
                        order = bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                        print(f"\n✓ Order placed! Order ID: {order['orderId']}")
                        print(f"   Status: {order['status']}")
                
                elif choice == '6':
                    # TWAP order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    total_quantity = float(input("Enter total quantity: ").strip())
                    duration = int(input("Enter duration (minutes): ").strip())
                    num_slices = int(input("Enter number of slices: ").strip())
                    
                    confirm = input(f"\nConfirm TWAP: {side} {total_quantity} {symbol} over {duration}m in {num_slices} slices? (y/n): ")
                    if confirm.lower() == 'y':
                        orders = bot.place_twap_order(symbol, side, total_quantity, duration, num_slices)
                        print(f"\n✓ TWAP completed! {len(orders)} orders executed")
                
                elif choice == '7':
                    # View open orders
                    symbol = input("Enter symbol (or press Enter for all): ").strip() or None
                    orders = bot.get_open_orders(symbol)
                    
                    if orders:
                        print(f"\n📋 Open Orders ({len(orders)}):")
                        for order in orders:
                            print(f"   ID: {order['orderId']} | {order['symbol']} | {order['side']} | "
                                  f"Type: {order['type']} | Qty: {order['origQty']} | "
                                  f"Price: {order.get('price', 'N/A')} | Status: {order['status']}")
                    else:
                        print("\n✓ No open orders")
                
                elif choice == '8':
                    # Cancel order
                    symbol = input("Enter symbol: ").strip()
                    order_id = int(input("Enter order ID: ").strip())
                    
                    confirm = input(f"\nConfirm cancel order {order_id}? (y/n): ")
                    if confirm.lower() == 'y':
                        bot.cancel_order(symbol, order_id)
                        print("\n✓ Order cancelled")
                
                elif choice == '9':
                    # Cancel all orders
                    symbol = input("Enter symbol: ").strip()
                    
                    confirm = input(f"\n⚠️  Cancel ALL orders for {symbol}? (y/n): ")
                    if confirm.lower() == 'y':
                        bot.cancel_all_orders(symbol)
                        print("\n✓ All orders cancelled")
                
                elif choice == '10':
                    # View positions
                    symbol = input("Enter symbol (or press Enter for all): ").strip() or None
                    positions = bot.get_position_info(symbol)
                    
                    if positions:
                        print(f"\n📈 Active Positions ({len(positions)}):")
                        for pos in positions:
                            print(f"   {pos['symbol']} | Amount: {pos['positionAmt']} | "
                                  f"Entry: {pos['entryPrice']} | "
                                  f"Unrealized PnL: {pos['unRealizedProfit']} | "
                                  f"Leverage: {pos['leverage']}x")
                    else:
                        print("\n✓ No active positions")
                
                else:
                    print("\n❌ Invalid choice. Please try again.")
            
            except ValueError as e:
                print(f"\n❌ Invalid input: {e}")
            except BinanceAPIException as e:
                print(f"\n❌ API Error: {e}")
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    except Exception as e:
        print(f"\n❌ Failed to initialize bot: {e}")
        logger.error(f"Bot initialization failed: {e}")


if __name__ == "__main__":
    main()