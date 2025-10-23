import os
import tkinter as tk
import customtkinter as ctk
import logging
from console import BinanceFuturesBot
from tkinter import messagebox

# Configure logging for the main application
logging.basicConfig(
    level=logging.ERROR,  # Only show errors in the console
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler() # Show errors in the console
    ]
)
logger = logging.getLogger(__name__)

class BinanceTradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Binance Futures Trading Bot")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

        self.api_key = None
        self.api_secret = None
        self.bot = None

        self.create_widgets()
        self.check_api_keys()

    def create_widgets(self):
        self.tabview = ctk.CTkTabview(self, width=700, height=500)
        self.tabview.pack(padx=20, pady=20)
        self.tabview.add("API Keys")
        self.tabview.add("Dashboard")

        self.create_api_key_tab()
        self.create_dashboard_tab()

    def create_api_key_tab(self):
        api_key_frame = ctk.CTkFrame(self.tabview.tab("API Keys"))
        api_key_frame.pack(pady=20, padx=20)

        self.api_key_label = ctk.CTkLabel(api_key_frame, text="API Key:")
        self.api_key_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.api_key_entry = ctk.CTkEntry(api_key_frame, placeholder_text="Enter your API Key")
        self.api_key_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.api_secret_label = ctk.CTkLabel(api_key_frame, text="Secret Key:")
        self.api_secret_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.api_secret_entry = ctk.CTkEntry(api_key_frame, placeholder_text="Enter your Secret Key", show="*")
        self.api_secret_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.login_button = ctk.CTkButton(api_key_frame, text="Login", command=self.login)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=20)

    def place_market_order(self):
        if self.bot:
            symbol = self.market_symbol_entry.get().strip()
            side = self.market_side_combobox.get()
            quantity = self.market_quantity_entry.get().strip()

            if not symbol or not side or not quantity:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                order = self.bot.place_market_order(symbol, side, quantity)
                messagebox.showinfo("Success", f"Market order placed! Order ID: {order['orderId']}")
            except Exception as e:
                logger.error(f"Failed to place market order: {e}")
                messagebox.showerror("Error", f"Failed to place market order: {e}")

    def place_limit_order(self):
        if self.bot:
            symbol = self.limit_symbol_entry.get().strip()
            side = self.limit_side_combobox.get()
            quantity = self.limit_quantity_entry.get().strip()
            price = self.limit_price_entry.get().strip()

            if not symbol or not side or not quantity or not price:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                price = float(price)
                order = self.bot.place_limit_order(symbol, side, quantity, price)
                messagebox.showinfo("Success", f"Limit order placed! Order ID: {order['orderId']}")
            except Exception as e:
                logger.error(f"Failed to place limit order: {e}")
                messagebox.showerror("Error", f"Failed to place limit order: {e}")

    def place_stop_limit_order(self):
        if self.bot:
            symbol = self.stop_limit_symbol_entry.get().strip()
            side = self.stop_limit_side_combobox.get()
            quantity = self.stop_limit_quantity_entry.get().strip()
            stop_price = self.stop_limit_stop_price_entry.get().strip()
            limit_price = self.stop_limit_limit_price_entry.get().strip()

            if not symbol or not side or not quantity or not stop_price or not limit_price:
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                stop_price = float(stop_price)
                limit_price = float(limit_price)
                order = self.bot.place_stop_limit_order(symbol, side, quantity, stop_price, limit_price)
                messagebox.showinfo("Success", f"Stop-Limit order placed! Order ID: {order['orderId']}")
            except Exception as e:
                logger.error(f"Failed to place stop-limit order: {e}")
                messagebox.showerror("Error", f"Failed to place stop-limit order: {e}")
                
    def create_dashboard_tab(self):
        dashboard_frame = ctk.CTkFrame(self.tabview.tab("Dashboard"))
        dashboard_frame.pack(pady=20, padx=20)

        self.balance_label = ctk.CTkLabel(dashboard_frame, text="Account Balance: Loading...")
        self.balance_label.pack(pady=10)

        self.symbol_label = ctk.CTkLabel(dashboard_frame, text="Symbol:")
        self.symbol_label.pack(pady=5)
        self.symbol_entry = ctk.CTkEntry(dashboard_frame, placeholder_text="Enter symbol (e.g., BTCUSDT)")
        self.symbol_entry.pack(pady=5)

        self.price_button = ctk.CTkButton(dashboard_frame, text="Get Price", command=self.get_current_price)
        self.price_button.pack(pady=5)
        self.price_label = ctk.CTkLabel(dashboard_frame, text="Current Price: ")
        self.price_label.pack(pady=5)
        
        # Market Order
        self.market_order_frame = ctk.CTkFrame(dashboard_frame)
        self.market_order_frame.pack(pady=10)

        self.market_symbol_label = ctk.CTkLabel(self.market_order_frame, text="Symbol:")
        self.market_symbol_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.market_symbol_entry = ctk.CTkEntry(self.market_order_frame, placeholder_text="BTCUSDT")
        self.market_symbol_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.market_side_label = ctk.CTkLabel(self.market_order_frame, text="Side:")
        self.market_side_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.market_side_combobox = ctk.CTkComboBox(self.market_order_frame, values=["BUY", "SELL"])
        self.market_side_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.market_side_combobox.set("BUY")

        self.market_quantity_label = ctk.CTkLabel(self.market_order_frame, text="Quantity:")
        self.market_quantity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.market_quantity_entry = ctk.CTkEntry(self.market_order_frame, placeholder_text="0.01")
        self.market_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.place_market_order_button = ctk.CTkButton(self.market_order_frame, text="Place Market Order", command=self.place_market_order)
        self.place_market_order_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Limit Order
        self.limit_order_frame = ctk.CTkFrame(dashboard_frame)
        self.limit_order_frame.pack(pady=10)

        self.limit_symbol_label = ctk.CTkLabel(self.limit_order_frame, text="Symbol:")
        self.limit_symbol_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.limit_symbol_entry = ctk.CTkEntry(self.limit_order_frame, placeholder_text="BTCUSDT")
        self.limit_symbol_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.limit_side_label = ctk.CTkLabel(self.limit_order_frame, text="Side:")
        self.limit_side_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.limit_side_combobox = ctk.CTkComboBox(self.limit_order_frame, values=["BUY", "SELL"])
        self.limit_side_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.limit_side_combobox.set("BUY")

        self.limit_quantity_label = ctk.CTkLabel(self.limit_order_frame, text="Quantity:")
        self.limit_quantity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.limit_quantity_entry = ctk.CTkEntry(self.limit_order_frame, placeholder_text="0.01")
        self.limit_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.limit_price_label = ctk.CTkLabel(self.limit_order_frame, text="Price:")
        self.limit_price_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.limit_price_entry = ctk.CTkEntry(self.limit_order_frame, placeholder_text="10000")
        self.limit_price_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.place_limit_order_button = ctk.CTkButton(self.limit_order_frame, text="Place Limit Order", command=self.place_limit_order)
        self.place_limit_order_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Stop-Limit Order
        self.stop_limit_order_frame = ctk.CTkFrame(dashboard_frame)
        self.stop_limit_order_frame.pack(pady=10)

        self.stop_limit_symbol_label = ctk.CTkLabel(self.stop_limit_order_frame, text="Symbol:")
        self.stop_limit_symbol_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_symbol_entry = ctk.CTkEntry(self.stop_limit_order_frame, placeholder_text="BTCUSDT")
        self.stop_limit_symbol_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.stop_limit_side_label = ctk.CTkLabel(self.stop_limit_order_frame, text="Side:")
        self.stop_limit_side_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_side_combobox = ctk.CTkComboBox(self.stop_limit_order_frame, values=["BUY", "SELL"])
        self.stop_limit_side_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.stop_limit_side_combobox.set("BUY")

        self.stop_limit_quantity_label = ctk.CTkLabel(self.stop_limit_order_frame, text="Quantity:")
        self.stop_limit_quantity_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_quantity_entry = ctk.CTkEntry(self.stop_limit_order_frame, placeholder_text="0.01")
        self.stop_limit_quantity_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.stop_limit_stop_price_label = ctk.CTkLabel(self.stop_limit_order_frame, text="Stop Price:")
        self.stop_limit_stop_price_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_stop_price_entry = ctk.CTkEntry(self.stop_limit_order_frame, placeholder_text="10000")
        self.stop_limit_stop_price_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.stop_limit_limit_price_label = ctk.CTkLabel(self.stop_limit_order_frame, text="Limit Price:")
        self.stop_limit_limit_price_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_limit_price_entry = ctk.CTkEntry(self.stop_limit_order_frame, placeholder_text="10000")
        self.stop_limit_limit_price_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        self.place_stop_limit_order_button = ctk.CTkButton(self.stop_limit_order_frame, text="Place Stop-Limit Order", command=self.place_stop_limit_order)
        self.place_stop_limit_order_button.grid(row=5, column=0, columnspan=2, pady=10)

    def check_api_keys(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET_KEY")
        if api_key and api_secret:
            self.api_key_entry.insert(0, api_key)
            self.api_secret_entry.insert(0, api_secret)
            self.login()

    def login(self):
        self.api_key = self.api_key_entry.get()
        self.api_secret = self.api_secret_entry.get()

        if not self.api_key or not self.api_secret:
            messagebox.showerror("Error", "API Key and Secret Key are required.")
            return

        try:
            self.bot = BinanceFuturesBot(self.api_key, self.api_secret, testnet=True)
            self.tabview.set("Dashboard")
            messagebox.showinfo("Success", "Login successful!")
            self.update_balance()
        except Exception as e:
            logger.error(f"Login failed: {e}")
            messagebox.showerror("Error", f"Login failed: {e}")

    def update_balance(self):
        if self.bot:
            try:
                balances = self.bot.get_balance()
                total_balance = sum(float(asset['walletBalance']) for asset in balances)
                self.balance_label.configure(text=f"Account Balance: {total_balance:.2f} USDT")
            except Exception as e:
                logger.error(f"Failed to update balance: {e}")
                self.balance_label.configure(text=f"Failed to retrieve balance: {e}")

    def get_current_price(self):
        if self.bot:
            symbol = self.symbol_entry.get().strip()
            if not symbol:
                messagebox.showerror("Error", "Please enter a symbol.")
                return
            try:
                price = self.bot.get_current_price(symbol)
                self.price_label.configure(text=f"Current Price: {price}")
            except Exception as e:
                logger.error(f"Failed to get price: {e}")
                messagebox.showerror("Error", f"Failed to get price: {e}")
                self.price_label.configure(text=f"Failed to get price: {e}")

if __name__ == "__main__":
    app = BinanceTradingApp()
    app.mainloop()
