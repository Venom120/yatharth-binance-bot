"""
Binance Futures Testnet Trading Bot
A comprehensive trading bot with support for multiple order types
"""

import logging
import json
from typing import Optional, Dict, List, Any
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import time, os, dotenv
from limit_orders import place_limit_order
from market_orders import place_market_order
from advanced.oco import place_stop_limit_order
from advanced.twap import place_twap_order

dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all messages
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        #logging.StreamHandler() # Remove StreamHandler to prevent INFO from showing in console
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
        # Initialize client with timestamp offset correction
        self.client = Client(api_key, api_secret, testnet=testnet)
        
        # Set testnet URL
        if testnet:
            self.client.API_URL = 'https://testnet.binancefuture.com'
            logger.info("Connected to Binance Futures Testnet")
        else:
            logger.warning("Connected to Binance LIVE environment")
        
        # Synchronize timestamp with Binance servers
        self._sync_time()
        
        # Validate connection
        self._validate_connection()
    
    def _sync_time(self):
        """Synchronize local time with Binance server time"""
        try:
            # Get server time
            server_time = self.client.get_server_time()
            local_time = int(time.time() * 1000)
            time_offset = server_time['serverTime'] - local_time
            
            # Set timestamp offset
            self.client.timestamp_offset = time_offset
            
            logger.info(f"Time synchronized. Offset: {time_offset}ms")
        except Exception as e:
            logger.warning(f"Could not sync time: {e}. Continuing anyway...")
    
    def _validate_connection(self):
        """Validate API connection and permissions"""
        try:
            # Test connection with futures account endpoint
            account = self.client.futures_account()
            logger.info("[OK] API connection validated successfully")
            logger.info("[OK] Account permissions verified")
            
            # Display account info
            total_balance = sum(float(asset['walletBalance']) for asset in account['assets'])
            logger.info(f"[OK] Total wallet balance: {total_balance:.2f} USDT")
            
        except BinanceAPIException as e:
            if e.code == -1021:
                logger.error("❌ Timestamp error. Attempting to resync...")
                self._sync_time()
                # Retry validation
                try:
                    self.client.futures_account()
                    logger.info("[OK] Connection validated after time sync")
                except Exception as retry_error:
                    logger.error(f"❌ Still failing after time sync: {retry_error}")
                    raise
            elif e.code == -2015:
                logger.error("❌ Invalid API key or permissions. Please check:")
                logger.error("   1. API key is correct")
                logger.error("   2. API secret is correct")
                logger.error("   3. API key is not expired")
                raise ValueError("Invalid API credentials")
            else:
                logger.error(f"❌ API connection failed: {e}")
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
            # self._log_response("GET_ACCOUNT", account)
            return account
        except BinanceAPIException as e:
            self._log_error("GET_ACCOUNT", e)
            raise
    
    def get_balance(self) -> List[Dict]:
        """Get account balance"""
        try:
            account = self.get_account_info()
            balances = [asset for asset in account['assets'] if float(asset['walletBalance']) > 0]

            # Display account info
            total_balance = sum(float(asset['walletBalance']) for asset in account['assets'])
            logger.info(f"[OK] Total wallet balance: {total_balance:.2f} USDT")
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

    def get_all_futures_symbols(self) -> List[str]:
        """Get all available futures symbols"""
        try:
            exchange_info = self.client.futures_exchange_info()
            # Filter for only symbols that are currently trading
            symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']
            logger.info(f"Loaded {len(symbols)} trading symbols")
            return sorted(symbols)
        except Exception as e:
            self._log_error("GET_ALL_SYMBOLS", e)
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
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            if symbol:
                orders = self.client.futures_get_open_orders(symbol=symbol.upper())
            else:
                orders = self.client.futures_get_open_orders()
            
            logger.info(f"Open orders: {len(orders)}")
            return orders # type: ignore
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
            logger.info(f"[OK] Order {order_id} cancelled")
            return result
        except Exception as e:
            self._log_error("CANCEL_ORDER", e)
            raise
    
    def cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders for a symbol"""
        try:
            result = self.client.futures_cancel_all_open_orders(symbol=symbol.upper())
            logger.info(f"[OK] All orders cancelled for {symbol}")
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
    print("\n[!] IMPORTANT: System time synchronization")
    print("If you get timestamp errors, your system clock may be off.")
    print("The bot will attempt to auto-sync with Binance servers.\n")
    
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
        print("[X] API credentials are required!")
        return
    
    try:
        # Initialize bot
        print("\n[>>>] Initializing bot and syncing time...")
        bot = BinanceFuturesBot(api_key, api_secret, testnet=True)
        print("[OK] Bot initialized successfully!")
        
        while True:
            print_menu()
            choice = input("\nEnter your choice: ").strip()
            
            try:
                if choice == '0':
                    print("\n[BYE] Exiting bot. Happy trading!")
                    break
                
                elif choice == '1':
                    # View balance
                    balances = bot.get_balance()
                    print("\n[$] Account Balances:")
                    for asset in balances:
                        print(f"   {asset['asset']}: {asset['walletBalance']} (Available: {asset['availableBalance']})")
                
                elif choice == '2':
                    # Get current price
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    price = bot.get_current_price(symbol)
                    print(f"\n[#] {symbol}: ${price}")
                
                elif choice == '3':
                    # Market order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = float(input("Enter quantity: ").strip())
                    
                    confirm = input(f"\nConfirm {side} {quantity} {symbol} at MARKET? (y/n): ")
                    if confirm.lower() == 'y':
                        order = place_market_order(bot.client, symbol, side, quantity)
                        print(f"\n[OK] Order placed! Order ID: {order['orderId']}")
                        print(f"   Status: {order['status']}")
                
                elif choice == '4':
                    # Limit order
                    symbol = input("Enter symbol (e.g., BTCUSDT): ").strip()
                    side = input("Enter side (BUY/SELL): ").strip().upper()
                    quantity = float(input("Enter quantity: ").strip())
                    price = float(input("Enter limit price: ").strip())
                    
                    confirm = input(f"\nConfirm {side} {quantity} {symbol} @ ${price}? (y/n): ")
                    if confirm.lower() == 'y':
                        order = place_limit_order(bot.client, symbol, side, quantity, price)
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
                        order = place_stop_limit_order(bot.client, symbol, side, quantity, stop_price, limit_price)
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
                        orders = place_twap_order(symbol, side, total_quantity, duration, num_slices)
                        print(f"\n[OK] TWAP completed! {len(orders)} orders executed")
                
                elif choice == '7':
                    # View open orders
                    symbol = input("Enter symbol (or press Enter for all): ").strip() or None
                    orders = bot.get_open_orders(symbol)
                    
                    if orders:
                        print(f"\n[=] Open Orders ({len(orders)}):")
                        for order in orders:
                            print(f"   ID: {order['orderId']} | {order['symbol']} | {order['side']} | "
                                  f"Type: {order['type']} | Qty: {order['origQty']} | "
                                  f"Price: {order.get('price', 'N/A')} | Status: {order['status']}")
                    else:
                        print("\n[OK] No open orders")
                
                elif choice == '8':
                    # Cancel order
                    symbol = input("Enter symbol: ").strip()
                    order_id = int(input("Enter order ID: ").strip())
                    
                    confirm = input(f"\nConfirm cancel order {order_id}? (y/n): ")
                    if confirm.lower() == 'y':
                        bot.cancel_order(symbol, order_id)
                        print("\n[OK] Order cancelled")
                
                elif choice == '9':
                    # Cancel all orders
                    symbol = input("Enter symbol: ").strip()
                    
                    confirm = input(f"\n[!] Cancel ALL orders for {symbol}? (y/n): ")
                    if confirm.lower() == 'y':
                        bot.cancel_all_orders(symbol)
                        print("\n[OK] All orders cancelled")
                
                elif choice == '10':
                    # View positions
                    symbol = input("Enter symbol (or press Enter for all): ").strip() or None
                    positions = bot.get_position_info(symbol)
                    
                    if positions:
                        print(f"\n[^] Active Positions ({len(positions)}):")
                        for pos in positions:
                            print(f"   {pos['symbol']} | Amount: {pos['positionAmt']} | "
                                  f"Entry: {pos['entryPrice']} | "
                                  f"Unrealized PnL: {pos['unRealizedProfit']} | "
                                  f"Leverage: {pos['leverage']}x")
                    else:
                        print("\n[OK] No active positions")
                
                else:
                    print("\n[X] Invalid choice. Please try again.")
            
            except ValueError as e:
                print(f"\n[X] Invalid input: {e}")
            except BinanceAPIException as e:
                print(f"\n[X] API Error: {e}")
            except Exception as e:
                print(f"\n[X] Error: {e}")
    
    except ValueError as e:
        print(f"\n[X] {e}")
        print("\n[!] Please verify:")
        print("   1. You're using testnet.binancefuture.com API keys")
        print("   2. API key and secret are correct")
        print("   3. Keys are not expired")
    except Exception as e:
        print(f"\n[X] Failed to initialize bot: {e}")
        logger.error(f"Bot initialization failed: {e}")
        print("\n[!] Troubleshooting steps:")
        print("   1. Check your system time is correct")
        print("   2. Verify API credentials")
        print("   3. Check internet connection")


if __name__ == "__main__":
    main()