import os
import tkinter as tk
import customtkinter as ctk
import logging
from console import BinanceFuturesBot
from tkinter import messagebox
from functools import partial
from limit_orders import place_limit_order
from market_orders import place_market_order
from advanced.oco import place_stop_limit_order
from advanced.twap import place_twap_order

# Configure logging for the main application
logging.basicConfig(
    level=logging.ERROR,  # Only show errors in the console
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler() # Show errors in the console
    ]
)
logger = logging.getLogger(__name__)

class BinanceTradingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Binance Futures Trading Bot")
        self.geometry("1200x768") # Increased width for new page
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.api_key = None
        self.api_secret = None
        self.bot = None
        self.symbol_list = ["Loading..."] # Placeholder

        # Configure main window grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create login frame
        self.create_login_frame()
        
        # Auto-login if .env keys exist
        self.check_api_keys()

    def create_login_frame(self):
        """Creates the initial login screen."""
        self.login_frame = ctk.CTkFrame(self, corner_radius=0)
        self.login_frame.grid(row=0, column=0, sticky="nsew")
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_rowconfigure(0, weight=1)

        center_frame = ctk.CTkFrame(self.login_frame)
        center_frame.grid(row=0, column=0, padx=20, pady=20)

        title_label = ctk.CTkLabel(center_frame, text="Bot Login", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=2, padx=30, pady=(20, 10))

        api_key_label = ctk.CTkLabel(center_frame, text="API Key:")
        api_key_label.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.api_key_entry = ctk.CTkEntry(center_frame, placeholder_text="Enter your API Key", width=300)
        self.api_key_entry.grid(row=1, column=1, padx=20, pady=10)

        api_secret_label = ctk.CTkLabel(center_frame, text="Secret Key:")
        api_secret_label.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.api_secret_entry = ctk.CTkEntry(center_frame, placeholder_text="Enter your Secret Key", show="*", width=300)
        self.api_secret_entry.grid(row=2, column=1, padx=20, pady=10)

        self.login_button = ctk.CTkButton(center_frame, text="Login", command=self.login)
        self.login_button.grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 30))

    def create_main_ui(self):
        """Creates the main application UI (navbar, sidebar, content) after login."""
        
        # Reconfigure main window grid for the app layout
        self.grid_rowconfigure(0, weight=0)  # Navbar (fixed)
        self.grid_rowconfigure(1, weight=1)  # Main content row
        self.grid_columnconfigure(0, weight=0) # Sidebar (fixed)
        self.grid_columnconfigure(1, weight=1) # Content area

        # --- Navbar ---
        self.navbar_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.navbar_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.navbar_frame.grid_columnconfigure(0, weight=1)
        
        navbar_title = ctk.CTkLabel(self.navbar_frame, text="Binance Futures Bot", font=ctk.CTkFont(size=16, weight="bold"))
        navbar_title.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.navbar_balance_label = ctk.CTkLabel(self.navbar_frame, text="Balance: Loading...", font=ctk.CTkFont(size=14))
        self.navbar_balance_label.grid(row=0, column=1, padx=20, pady=10, sticky="e")

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar_frame.grid(row=1, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(5, weight=1) # Push logout to bottom

        logo_label = ctk.CTkLabel(self.sidebar_frame, text="Navigation", font=ctk.CTkFont(size=16, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, text="Dashboard", command=self.show_dashboard_page)
        self.dashboard_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.trade_button = ctk.CTkButton(self.sidebar_frame, text="Place Order", command=self.show_trade_page)
        self.trade_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.manage_button = ctk.CTkButton(self.sidebar_frame, text="Manage Positions", command=self.show_manage_page)
        self.manage_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.twap_button = ctk.CTkButton(self.sidebar_frame, text="TWAP Order", command=self.show_twap_page)
        self.twap_button.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # --- Main Content Frame (Container) ---
        self.main_content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_content_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_content_frame.grid_rowconfigure(0, weight=1)
        self.main_content_frame.grid_columnconfigure(0, weight=1)

        # Create the different "pages"
        self.create_dashboard_page()
        self.create_trade_page()
        self.create_manage_page() # Create the new page
        self.create_twap_page()

    def create_dashboard_page(self):
        """Creates the dashboard page widgets."""
        self.dashboard_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.dashboard_frame.grid_columnconfigure(0, weight=1)

        # --- Price Checker ---
        price_frame = ctk.CTkFrame(self.dashboard_frame)
        price_frame.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        price_frame.grid_columnconfigure(1, weight=1)
        
        price_title = ctk.CTkLabel(price_frame, text="Check Price", font=ctk.CTkFont(size=16, weight="bold"))
        price_title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        symbol_label = ctk.CTkLabel(price_frame, text="Symbol:")
        symbol_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.price_symbol_combobox = ctk.CTkComboBox(price_frame, values=self.symbol_list, command=self.update_current_price)
        self.price_symbol_combobox.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        self.price_label = ctk.CTkLabel(price_frame, text="Current Price: --", font=ctk.CTkFont(size=14), text_color="gray")
        self.price_label.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
        
    def create_trade_page(self):
        """Creates the trade page with order forms."""
        self.trade_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.trade_frame.grid(row=0, column=0, sticky="nsew")
        # 3-column grid for the order forms
        self.trade_frame.grid_columnconfigure(0, weight=1)
        self.trade_frame.grid_columnconfigure(1, weight=1)
        self.trade_frame.grid_columnconfigure(2, weight=1)

        # --- Create and place the order frames ---
        self.market_order_frame = self.create_market_order_frame()
        self.market_order_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.limit_order_frame = self.create_limit_order_frame()
        self.limit_order_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.stop_limit_order_frame = self.create_stop_limit_order_frame()
        self.stop_limit_order_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

    def create_manage_page(self):
        """Creates the page for managing open orders and positions."""
        self.manage_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.manage_frame.grid(row=0, column=0, sticky="nsew")
        # --- Start of content moved from create_twap_page ---
        self.manage_frame.grid_rowconfigure(1, weight=1)
        self.manage_frame.grid_columnconfigure(0, weight=1)
        self.manage_frame.grid_columnconfigure(1, weight=1)

        # --- Refresh Button ---
        refresh_button = ctk.CTkButton(self.manage_frame, text="Refresh Data", command=self.refresh_all_data)
        refresh_button.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        # --- Open Positions Column ---
        positions_container = ctk.CTkFrame(self.manage_frame)
        positions_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        positions_container.grid_rowconfigure(1, weight=1)
        positions_container.grid_columnconfigure(0, weight=1)

        positions_title = ctk.CTkLabel(positions_container, text="Active Positions", font=ctk.CTkFont(size=16, weight="bold"))
        positions_title.grid(row=0, column=0, padx=10, pady=10)

        self.positions_list_frame = ctk.CTkScrollableFrame(positions_container, label_text="Your Positions")
        self.positions_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # --- Open Orders Column ---
        orders_container = ctk.CTkFrame(self.manage_frame)
        orders_container.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        orders_container.grid_rowconfigure(1, weight=1)
        orders_container.grid_columnconfigure(0, weight=1)

        orders_title = ctk.CTkLabel(orders_container, text="Open Orders", font=ctk.CTkFont(size=16, weight="bold"))
        orders_title.grid(row=0, column=0, padx=10, pady=10)

        self.open_orders_list_frame = ctk.CTkScrollableFrame(orders_container, label_text="Your Open Orders")
        self.open_orders_list_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        # --- End of moved content ---

    def create_twap_page(self):
        self.twap_order_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=0, fg_color="transparent")
        self.twap_order_frame.grid(row=0, column=0, sticky="nsew")
        
        # --- Start of content moved from create_twap_order_frame ---
        # Configure grid to center the form
        self.twap_order_frame.grid_columnconfigure(0, weight=1)
        self.twap_order_frame.grid_rowconfigure(0, weight=1)
        
        # Create a frame to hold the content, so it doesn't stretch
        frame = ctk.CTkFrame(self.twap_order_frame)
        frame.grid(row=0, column=0, padx=20, pady=20, sticky="") # Not sticky, so it centers

        frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(frame, text="TWAP Order", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        symbol_label = ctk.CTkLabel(frame, text="Symbol:")
        symbol_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.twap_symbol_combobox = ctk.CTkComboBox(frame, values=self.symbol_list, command=self.update_twap_price)
        self.twap_symbol_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.twap_price_label = ctk.CTkLabel(frame, text="Price: --", text_color="gray")
        self.twap_price_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        side_label = ctk.CTkLabel(frame, text="Side:")
        side_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.twap_side_combobox = ctk.CTkComboBox(frame, values=["BUY", "SELL"])
        self.twap_side_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.twap_side_combobox.set("BUY")

        quantity_label = ctk.CTkLabel(frame, text="Quantity:")
        quantity_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.twap_quantity_entry = ctk.CTkEntry(frame, placeholder_text="0.01")
        self.twap_quantity_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        duration_label = ctk.CTkLabel(frame, text="Duration (minutes):")
        duration_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.twap_duration_entry = ctk.CTkEntry(frame, placeholder_text="60")
        self.twap_duration_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        slices_label = ctk.CTkLabel(frame, text="Slices:")
        slices_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.twap_slices_entry = ctk.CTkEntry(frame, placeholder_text="10")
        self.twap_slices_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        button = ctk.CTkButton(frame, text="Place TWAP Order", command=self.place_twap_order_gui, fg_color="purple", hover_color="dark purple")
        button.grid(row=7, column=0, columnspan=2, pady=10, padx=10)
        # --- End of moved content ---


    # --- Page Navigation ---
    def show_dashboard_page(self):
        self.dashboard_frame.tkraise()

    def show_trade_page(self):
        self.trade_frame.tkraise()

    def show_manage_page(self):
        """Show the manage page and refresh its data."""
        self.manage_frame.tkraise()
        self.refresh_all_data()

    def show_twap_page(self):
        """Show the TWAP page."""
        self.twap_order_frame.tkraise()
        # Update price on page show
        self.update_twap_price(self.twap_symbol_combobox.get())

    def refresh_all_data(self):
        """Refresh both open orders and positions."""
        self.refresh_open_orders()
        self.refresh_positions()

    # --- Order Form Creators ---
    def create_market_order_frame(self):
        frame = ctk.CTkFrame(self.trade_frame)
        frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(frame, text="Market Order", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        symbol_label = ctk.CTkLabel(frame, text="Symbol:")
        symbol_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.market_symbol_combobox = ctk.CTkComboBox(frame, values=self.symbol_list, command=self.update_market_price)
        self.market_symbol_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.market_price_label = ctk.CTkLabel(frame, text="Price: --", text_color="gray")
        self.market_price_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        side_label = ctk.CTkLabel(frame, text="Side:")
        side_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.market_side_combobox = ctk.CTkComboBox(frame, values=["BUY", "SELL"])
        self.market_side_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.market_side_combobox.set("BUY")

        quantity_label = ctk.CTkLabel(frame, text="Quantity:")
        quantity_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.market_quantity_entry = ctk.CTkEntry(frame, placeholder_text="0.01")
        self.market_quantity_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        button = ctk.CTkButton(frame, text="Place Market Order", command=self.place_market_order, fg_color="green", hover_color="dark green")
        button.grid(row=5, column=0, columnspan=2, pady=10, padx=10)
        return frame

    def create_limit_order_frame(self):
        frame = ctk.CTkFrame(self.trade_frame)
        frame.grid_columnconfigure(1, weight=1)
        
        title = ctk.CTkLabel(frame, text="Limit Order", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        symbol_label = ctk.CTkLabel(frame, text="Symbol:")
        symbol_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.limit_symbol_combobox = ctk.CTkComboBox(frame, values=self.symbol_list, command=self.update_limit_price)
        self.limit_symbol_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.limit_price_label = ctk.CTkLabel(frame, text="Price: --", text_color="gray")
        self.limit_price_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        side_label = ctk.CTkLabel(frame, text="Side:")
        side_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.limit_side_combobox = ctk.CTkComboBox(frame, values=["BUY", "SELL"])
        self.limit_side_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.limit_side_combobox.set("BUY")

        quantity_label = ctk.CTkLabel(frame, text="Quantity:")
        quantity_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.limit_quantity_entry = ctk.CTkEntry(frame, placeholder_text="0.01")
        self.limit_quantity_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        price_label = ctk.CTkLabel(frame, text="Price:")
        price_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.limit_price_entry = ctk.CTkEntry(frame, placeholder_text="10000")
        self.limit_price_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        button = ctk.CTkButton(frame, text="Place Limit Order", command=self.place_limit_order)
        button.grid(row=6, column=0, columnspan=2, pady=10, padx=10)
        return frame

    # This function is now deleted, its content was moved to create_twap_page
    # def create_twap_order_frame(self):
    #     ...

    def create_stop_limit_order_frame(self):
        frame = ctk.CTkFrame(self.trade_frame)
        frame.grid_columnconfigure(1, weight=1)

        title = ctk.CTkLabel(frame, text="Stop-Limit Order", font=ctk.CTkFont(size=16, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        symbol_label = ctk.CTkLabel(frame, text="Symbol:")
        symbol_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_symbol_combobox = ctk.CTkComboBox(frame, values=self.symbol_list, command=self.update_stop_limit_price)
        self.stop_limit_symbol_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.stop_limit_price_label = ctk.CTkLabel(frame, text="Price: --", text_color="gray")
        self.stop_limit_price_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        side_label = ctk.CTkLabel(frame, text="Side:")
        side_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_side_combobox = ctk.CTkComboBox(frame, values=["BUY", "SELL"])
        self.stop_limit_side_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.stop_limit_side_combobox.set("BUY")

        quantity_label = ctk.CTkLabel(frame, text="Quantity:")
        quantity_label.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_quantity_entry = ctk.CTkEntry(frame, placeholder_text="0.01")
        self.stop_limit_quantity_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        stop_price_label = ctk.CTkLabel(frame, text="Stop Price:")
        stop_price_label.grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_stop_price_entry = ctk.CTkEntry(frame, placeholder_text="9900")
        self.stop_limit_stop_price_entry.grid(row=5, column=1, padx=5, pady=5, sticky="ew")

        limit_price_label = ctk.CTkLabel(frame, text="Limit Price:")
        limit_price_label.grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.stop_limit_limit_price_entry = ctk.CTkEntry(frame, placeholder_text="9850")
        self.stop_limit_limit_price_entry.grid(row=6, column=1, padx=5, pady=5, sticky="ew")

        button = ctk.CTkButton(frame, text="Place Stop-Limit Order", command=self.place_stop_limit_order, fg_color="red", hover_color="dark red")
        button.grid(row=7, column=0, columnspan=2, pady=10, padx=10)
        return frame

    # --- Bot Logic & Actions ---

    def check_api_keys(self):
        """Check for env variables and auto-login."""
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET_KEY")
        if api_key and api_secret:
            self.api_key_entry.insert(0, api_key)
            self.api_secret_entry.insert(0, api_secret)
            if api_key and api_secret:
                self.login()

    def login(self):
        """Handle user login."""
        if not self.api_key:
            self.api_key = self.api_key_entry.get()
            if self.api_key:
                os.environ['BINANCE_API_KEY'] = self.api_key
        if not self.api_secret:
            self.api_secret = self.api_secret_entry.get()
            if self.api_secret:
                os.environ['BINANCE_SECRET_KEY'] = self.api_secret

        # if not self.api_key or not self.api_secret:
        #     messagebox.showerror("Error", "API Key and Secret Key are required.")
        #     return

        try:
            self.bot = BinanceFuturesBot(self.api_key, self.api_secret, testnet=True)
            # messagebox.showinfo("Success", "Login successful!")
            
            # Hide login frame and build main UI
            self.login_frame.grid_forget()
            self.create_main_ui()
            
            # Load bot data (balance, symbols)
            self.load_bot_data()
            
            # Show the dashboard first
            self.show_dashboard_page()

        except Exception as e:
            logger.error(f"Login failed: {e}")
            messagebox.showerror("Error", f"Login failed: {e}")
            self.bot = None

    def load_bot_data(self):
        """Fetch initial data from bot after login."""
        self.update_balance()
        self.load_symbols()
        self.refresh_all_data() # Refresh positions and orders

    def update_balance(self):
        """Update the balance label in the navbar."""
        if self.bot:
            try:
                balances = self.bot.get_balance()
                total_balance = sum(float(asset['walletBalance']) for asset in balances if asset['asset'] == 'USDT')
                self.navbar_balance_label.configure(text=f"Balance: {total_balance:.2f} USDT")
            except Exception as e:
                logger.error(f"Failed to update balance: {e}")
                self.navbar_balance_label.configure(text="Balance: Error")

    def load_symbols(self):
        """Fetch all symbols and update all comboboxes."""
        if self.bot:
            try:
                self.symbol_list = self.bot.get_all_futures_symbols()
                
                # Update all comboboxes with the new list
                comboboxes = [
                    self.price_symbol_combobox,
                    self.market_symbol_combobox,
                    self.limit_symbol_combobox,
                    self.stop_limit_symbol_combobox,
                    self.twap_symbol_combobox  # <-- Added this
                ]
                for cb in comboboxes:
                    if cb: # Check if combobox exists
                        cb.configure(values=self.symbol_list)
                
                # Set a default value
                if "BTCUSDT" in self.symbol_list:
                    default_symbol = "BTCUSDT"
                else:
                    default_symbol = self.symbol_list[0] if self.symbol_list else ""
                
                for cb in comboboxes:
                    if cb: # Check if combobox exists
                        cb.set(default_symbol)

                if default_symbol:
                    # Use after to ensure widgets are drawn before fetching price
                    self.after(100, lambda: self.update_current_price(default_symbol))
                    self.after(100, lambda: self.update_market_price(default_symbol))
                    self.after(100, lambda: self.update_limit_price(default_symbol))
                    self.after(100, lambda: self.update_stop_limit_price(default_symbol))
                    self.after(100, lambda: self.update_twap_price(default_symbol)) # <-- Added this


            except Exception as e:
                logger.error(f"Failed to load symbols: {e}")
                messagebox.showerror("Error", f"Failed to load symbols: {e}")

    def get_current_price(self):
        """Get price for the selected symbol in the dashboard."""
        if self.bot:
            symbol = self.price_symbol_combobox.get().strip()
            if not symbol or symbol == "Loading...":
                messagebox.showerror("Error", "Please select a symbol.")
                return
            try:
                price = self.bot.get_current_price(symbol)
                self.price_label.configure(text=f"Current Price: {price}")
            except Exception as e:
                logger.error(f"Failed to get price: {e}")
                self.price_label.configure(text="Failed to get price")

    def _fetch_and_set_price(self, symbol, label_widget):
        """Generic helper to fetch price and update a specific label."""
        if not self.bot or not symbol or symbol == "Loading..." or not label_widget:
            if label_widget:
                label_widget.configure(text="Price: --", text_color="gray")
            return
        try:
            # Run in a separate thread to avoid freezing UI (optional but good practice)
            # For simplicity, we'll run it directly. If it's slow, we'd thread this.
            price = self.bot.get_current_price(symbol)
            label_widget.configure(text=f"Price: {price}", text_color="cyan")
        except Exception as e:
            logger.warning(f"Failed to get price for {symbol}: {e}")
            label_widget.configure(text="Price: Error", text_color="red")
    
    def update_current_price(self, symbol: str):
        """Callback for update current symbol."""
        self._fetch_and_set_price(symbol, self.price_label)

    def update_market_price(self, symbol: str):
        """Callback for market order symbol combobox."""
        self._fetch_and_set_price(symbol, self.market_price_label)

    def update_limit_price(self, symbol: str):
        """Callback for limit order symbol combobox."""
        self._fetch_and_set_price(symbol, self.limit_price_label)

    def update_stop_limit_price(self, symbol: str):
        """Callback for stop-limit order symbol combobox."""
        self._fetch_and_set_price(symbol, self.stop_limit_price_label)

    def update_twap_price(self, symbol: str):
        """Callback for twap order symbol combobox."""
        self._fetch_and_set_price(symbol, self.twap_price_label)

    def refresh_open_orders(self):
        """Fetches and displays open orders in the manage page."""
        if not self.bot:
            return
        
        # Clear existing widgets
        for widget in self.open_orders_list_frame.winfo_children():
            widget.destroy()

        try:
            orders = self.bot.get_open_orders()
            if not orders:
                no_orders_label = ctk.CTkLabel(self.open_orders_list_frame, text="No open orders.")
                no_orders_label.pack(pady=10)
                return

            for order in orders:
                order_frame = ctk.CTkFrame(self.open_orders_list_frame)
                order_frame.pack(fill="x", pady=5, padx=5)
                order_frame.grid_columnconfigure(0, weight=1)
                
                info = f"{order['symbol']} {order['side']} {order['origQty']} @ {order['price']} ({order['type']})"
                label = ctk.CTkLabel(order_frame, text=info)
                label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
                
                # Use partial to pass arguments to the command
                cancel_command = partial(self.cancel_order, order['symbol'], order['orderId'])
                cancel_button = ctk.CTkButton(order_frame, text="Cancel", command=cancel_command, fg_color="red", hover_color="dark red", width=80)
                cancel_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        except Exception as e:
            logger.error(f"Failed to refresh open orders: {e}")
            messagebox.showerror("Error", f"Failed to refresh open orders: {e}")

    def refresh_positions(self):
        """Fetches and displays active positions in the manage page."""
        if not self.bot:
            return

        # Clear existing widgets
        for widget in self.positions_list_frame.winfo_children():
            widget.destroy()

        try:
            positions = self.bot.get_position_info()
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]

            if not active_positions:
                no_pos_label = ctk.CTkLabel(self.positions_list_frame, text="No active positions.")
                no_pos_label.pack(pady=10)
                return

            for pos in active_positions:
                pos_frame = ctk.CTkFrame(self.positions_list_frame)
                pos_frame.pack(fill="x", pady=5, padx=5)
                pos_frame.grid_columnconfigure(0, weight=1)

                symbol = pos['symbol']
                amount = float(pos['positionAmt'])
                entry_price = float(pos['entryPrice'])
                pnl = float(pos['unRealizedProfit'])
                
                pnl_color = "green" if pnl >= 0 else "red"
                pos_type = "LONG" if amount > 0 else "SHORT"
                
                info1 = f"{symbol} ({pos_type}) | Qty: {amount}"
                info2 = f"Entry: {entry_price:.4f} | PnL: {pnl:.4f} USDT"
                
                label1 = ctk.CTkLabel(pos_frame, text=info1, font=ctk.CTkFont(weight="bold"))
                label1.grid(row=0, column=0, padx=5, pady=(5,0), sticky="w")
                
                label2 = ctk.CTkLabel(pos_frame, text=info2, text_color=pnl_color)
                label2.grid(row=1, column=0, padx=5, pady=(0,5), sticky="w")
                
                # Use partial to pass arguments
                close_command = partial(self.close_position, symbol, amount)
                close_button = ctk.CTkButton(pos_frame, text="Market Close", command=close_command, fg_color="red", hover_color="dark red", width=100)
                close_button.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="e")

        except Exception as e:
            logger.error(f"Failed to refresh positions: {e}")
            messagebox.showerror("Error", f"Failed to refresh positions: {e}")

    def cancel_order(self, symbol, order_id):
        """Cancels a specific open order."""
        if not self.bot:
            return
        
        try:
            self.bot.cancel_order(symbol, order_id)
            messagebox.showinfo("Success", f"Order {order_id} for {symbol} cancelled.")
            self.refresh_open_orders() # Refresh the list
        except Exception as e:
            logger.error(f"Failed to cancel order: {e}")
            messagebox.showerror("Error", f"Failed to cancel order: {e}")

    def place_market_order(self):
        if self.bot:
            symbol = self.market_symbol_combobox.get().strip()
            side = self.market_side_combobox.get()
            quantity = self.market_quantity_entry.get().strip()

            if not symbol or not side or not quantity or symbol == "Loading...":
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                order = place_market_order(self.bot.client, symbol, side, quantity)
                messagebox.showinfo("Success", f"Market order placed! Order ID: {order['orderId']}")
                self.update_balance() # Refresh balance after trade
                self.refresh_all_data() # Refresh orders and positions
            except Exception as e:
                logger.error(f"Failed to place market order: {e}")
                messagebox.showerror("Error", f"Failed to place market order: {e}")

    def place_limit_order(self):
        if self.bot:
            symbol = self.limit_symbol_combobox.get().strip()
            side = self.limit_side_combobox.get()
            quantity = self.limit_quantity_entry.get().strip()
            price = self.limit_price_entry.get().strip()

            if not symbol or not side or not quantity or not price or symbol == "Loading...":
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                price = float(price)
                order = place_limit_order(self.bot.client, symbol, side, quantity, price)
                messagebox.showinfo("Success", f"Limit order placed! Order ID: {order['orderId']}")
                self.update_balance() # Refresh balance after trade
                self.refresh_all_data() # Refresh orders and positions
            except Exception as e:
                logger.error(f"Failed to place stop-limit order: {e}")
                messagebox.showerror("Error", f"Failed to place stop-limit order: {e}")

    def place_twap_order_gui(self):
        if self.bot:
            symbol = self.twap_symbol_combobox.get().strip()
            side = self.twap_side_combobox.get()
            quantity = self.twap_quantity_entry.get().strip()
            duration = self.twap_duration_entry.get().strip()
            slices = self.twap_slices_entry.get().strip()

            if not all([symbol, side, quantity, duration, slices]) or symbol == "Loading...":
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                duration = int(duration)
                slices = int(slices)
                orders = place_twap_order(symbol, side, quantity, duration, slices)
                messagebox.showinfo("Success", f"TWAP order placed! {len(orders)} orders executed")
                self.update_balance()
                self.refresh_all_data()
            except Exception as e:
                logger.error(f"Failed to place TWAP order: {e}")
                messagebox.showerror("Error", f"Failed to place TWAP order: {e}")
    def place_stop_limit_order(self):
        if self.bot:
            symbol = self.stop_limit_symbol_combobox.get().strip()
            side = self.stop_limit_side_combobox.get()
            quantity = self.stop_limit_quantity_entry.get().strip()
            stop_price = self.stop_limit_stop_price_entry.get().strip()
            limit_price = self.stop_limit_limit_price_entry.get().strip()

            if not all([symbol, side, quantity, stop_price, limit_price]) or symbol == "Loading...":
                messagebox.showerror("Error", "Please fill in all fields.")
                return

            try:
                quantity = float(quantity)
                stop_price = float(stop_price)
                limit_price = float(limit_price)
                order = place_stop_limit_order(self.bot.client, symbol, side, quantity, stop_price, limit_price)
                messagebox.showinfo("Success", f"Stop-Limit order placed! Order ID: {order['orderId']}")
                self.update_balance()
                self.refresh_all_data()
            except Exception as e:
                logger.error(f"Failed to place stop-limit order: {e}")
                messagebox.showerror("Error", f"Failed to place stop-limit order: {e}")

    def close_position(self, symbol, position_amt):
        """Closes an active position with a market order."""
        if not self.bot:
            return
        
        try:
            amount = float(position_amt)
            if amount == 0:
                messagebox.showinfo("Info", "Position is already closed.")
                return
            
            side = "SELL" if amount > 0 else "BUY" # Opposite side to close
            quantity = abs(amount)
            
            confirm = messagebox.askyesno("Confirm Close", f"Are you sure you want to market {side} {quantity} {symbol} to close this position?")
            
            if not confirm:
                return
                
            order = place_market_order(self.bot.client, symbol, side, quantity)
            messagebox.showinfo("Success", f"Position {symbol} closed. Order ID: {order['orderId']}")
            
            # Refresh data
            self.update_balance()
            self.refresh_positions()

        except Exception as e:
            logger.error(f"Failed to close position: {e}")
            messagebox.showerror("Error", f"Failed to close position: {e}")

if __name__ == "__main__":
    app = BinanceTradingApp()
    app.mainloop()
