import datetime
import json
import time
import customtkinter as ctk
from const import finvasia
from api_helper import ShoonyaApiPy
import yfinance as yf
import pandas_ta as ta
import threading
import tkinter.messagebox
import tkinter as ttk
from order_manager import Order, OrderManager as OM, OrderWindow
from algo_bot import Algo
from const import database_file

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.api = ShoonyaApiPy()

        self.geometry("800x550")
        # grid configurations
        self.columnconfigure(0, weight=0)
        self.columnconfigure((1, 2, 3, 4), weight=1)
        self.columnconfigure((4), weight=0)

        self.rowconfigure(0, weight=0)
        self.rowconfigure((1, 2, 3, 5), weight=1)
        self.rowconfigure((5), weight=0)

        self.menu = Menu(self)  # fg_color = "#011c0e"
               
        # Initialize OrderManager
        self.order_manager = OM(self.api, database_file)
        self.main_frame = MainFrame(self, self.menu, self.api, self.order_manager)
        self.header = Header(self, self.main_frame, fg_color="#fa3966")
        self.footer = Footer(self, self.main_frame, self.order_manager, fg_color="Green")

class Header(ctk.CTkFrame):
    def __init__(self, master, main_frame, **kwargs):
        super().__init__(master, **kwargs)
        self.main_frame = main_frame

        self.columnconfigure((0,1,2,4,5,6), weight= 1)
        self.columnconfigure(3, weight= 0)
        self.columnconfigure(7, weight=0)

        self.grid(row=0, column=0, columnspan=4, sticky="nsew")

        #Exchange Dorpdown
        self.exchange = ctk.CTkComboBox(self, values=['NFO', 'NSE', 'BFO', 'BSE', 'MCX'], width=70)
        self.exchange.grid(row = 0, column =3)

        # Search box
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(self, textvariable=self.search_var, font=("Helvetica", 10), width=15)
        search_entry.grid(row=0, column=4, pady=(2, 1), padx=(0, 0), columnspan = 3, sticky ='nsew')

        # Search button
        search_button = ctk.CTkButton(self, text="Search", width=60, command=self.search_data)
        search_button.grid(row=0, column=7, pady=(2, 1), padx=(1, 3), sticky = 'nsew')

        # creating the LOGO
        ctk.CTkLabel(self, text="Quant Quest").grid(row=0, column=0)

    def search_data(self):
        search_text = self.search_var.get()
        exchange = self.exchange.get()
        # print(search_text)
        self.main_frame.search_data(search_text, exchange)

class Footer(ctk.CTkFrame):
    def __init__(self, master, main_frame,order_manager , **kwargs):
        super().__init__(master,height= 5 , **kwargs)
        self.main_frame = main_frame
        self.order_manager = order_manager

        self.columnconfigure((0,1,2,4,5,6), weight= 1)
        self.columnconfigure(3, weight= 0)
        self.columnconfigure(7, weight=0)

        self.grid(row=3, column=0, columnspan=4, sticky="nsew")

        #Portfolio window
        self.trades_portfolio_window = None

        # Button to open trades and portfolio window
        self.trades_portfolio_button = ctk.CTkButton(self, text="View Trades and Portfolio", width=50, command=self.open_trades_portfolio_window)
        self.trades_portfolio_button.grid(row=6, column=0, sticky='nsew')

    def open_trades_portfolio_window(self):
        # order_manager = OrderManager()
        if not self.trades_portfolio_window or not ctk.CTkToplevel.winfo_exists(self.trades_portfolio_window):
            self.trades_portfolio_window = TradesPortfolioWindow(self.master, self.order_manager)
            self.trades_portfolio_window.grab_set()
        else:
            self.trades_portfolio_window.lift()

class Menu(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid(row=1, column=0, sticky="nsew")
        # creating the menu
        ctk.CTkLabel(self, text="Select the index", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=(10, 5))

        self.indices = ctk.CTkComboBox(self, values=['NIFTY 50', 'BANKNFTY', 'FINNIFTY'], font=("Helvetica", 10))
        self.indices.grid(row=1, column=0,padx = (5,5), pady=(5, 10))

        labels_info = [
            ("NIFTY 50", 2),
            ("", 3),
            ("BANKNIFTY", 4),
            ("", 5),
            ("FINIFTY", 6),
            ("", 7),
            ("MIDCAP", 8),
            ("", 9)
        ]

        for text, row in labels_info:
            label = ctk.CTkLabel(self, text=text, font=("Helvetica", 10, "bold"))
            label.grid(row=row, column=0, pady=(5, 5), padx = 4, sticky = 'nsew')
            setattr(self, f"ltp_label{row}", label)

    def update_label_text(self, row, text, bg_color=None):
        label_name = f"ltp_label{row}"
        label = getattr(self, label_name, None)
        if label:
            label.configure(text=text, bg_color=bg_color)

class MainFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, menu, api, order_manager):
        super().__init__(master)

        self.order_manager = order_manager
        self.exchange = None
        self.grid(row=1, column=1, columnspan=3, stick="nsew")

        #grid config
        self.columnconfigure((0,1,2,3,4), weight = 1)
        self.menu = menu
        self.api = api

        # broker connect
        connect_broker = ctk.CTkButton(self, text="Connect", width=50, command=self.connect_broker)
        connect_broker.grid(row=5, column=0, sticky='nsew')

        algo_button = ctk.CTkButton(self, text="Open algo", width=50 , command=self.open_algo_window)
        algo_button.grid(row=5, column=1, sticky='nsew')

        # Search results frame
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=6, column=0, columnspan=5, sticky='nsew')
        
        #Grid Configuration 
        self.results_frame.columnconfigure((0,1,2,3), weight=1)
        self.results_frame.columnconfigure((4,5), weight=0)      
 
    def connect_broker(self):
        ret = self.api.login(userid=finvasia['user'], password=finvasia['pwd'],
                        twoFA=finvasia['factor2'], vendor_code=finvasia['vc'],
                        api_secret=finvasia['app_key'], imei=finvasia['imei'])
        self.refresh_ltp_thread()

    def refresh_ltps(self):
        while True:
            # Get quotes
            nifty_data = self.api.get_quotes(exchange="NSE", token="26000")
            banknifty_data = self.api.get_quotes(exchange="NSE", token="26009")
            finnifty_data = self.api.get_quotes(exchange="NSE", token="26037")
            midcap_data = self.api.get_quotes(exchange="NSE", token="26074")

            # Update labels in the Menu frame with the received data
            self.update_label_data(self.menu.ltp_label3, nifty_data)
            self.update_label_data(self.menu.ltp_label5, banknifty_data)
            self.update_label_data(self.menu.ltp_label7, finnifty_data)
            self.update_label_data(self.menu.ltp_label9, midcap_data)

    def update_label_data(self, label, data):
        if data:
            open_price = float(data.get('o', ''))
            last_price = float(data.get('lp', ''))
            if open_price > 0:
                change_percentage = (float(last_price) - float(open_price))/float(open_price)
            else:
                change_percentage = 0
                print(change_percentage)
            label_text = f"{last_price} | "+"{:.2f}%".format(change_percentage * 100)
            label.configure(text=label_text, bg_color=self.get_color_from_change(change_percentage))

    def get_color_from_change(self, change_percentage):
        if not change_percentage:
            return None

        change_value = float(change_percentage)
        if change_value > 0:
            return "green"
        elif change_value < 0:
            return "red"
        else:
            return "gray"

    def search_data(self, search_text, exchange):
        self.exchange = exchange
        try:
            search_result = self.api.searchscrip(exchange=exchange, searchtext=search_text)
            if search_result:
                self.display_search_results(search_result['values'])
            else:
                tkinter.messagebox.showerror("Couldn't search", f"Match {exchange}, {search_text}")
        except Exception as e:
            tkinter.messagebox.showerror("Not Logged In", f"Got Error {e}")

    def display_search_results(self, search_result):
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
                
        ctk.CTkLabel(self.results_frame, text="token",bg_color="red").grid(row = 0, column = 0, sticky = 'nsew')    
        ctk.CTkLabel(self.results_frame, text="Instrument",bg_color="red").grid(row = 0, column = 1, columnspan = 3, sticky = 'nsew')    
        ctk.CTkLabel(self.results_frame, text="Buy",bg_color="red").grid(row = 0, column = 4, sticky = 'nsew')    
        ctk.CTkLabel(self.results_frame, text="Sell",bg_color="red").grid(row = 0, column = 5, sticky = 'nsew') 

        # Display new results
        for idx, result in enumerate(search_result):
            token_label = ctk.CTkLabel(self.results_frame, text=result['token'])
            token_label.grid(row=idx+1, column=0)

            symbol_label = ctk.CTkLabel(self.results_frame, text=result['tsym'])
            symbol_label.grid(row=idx+1, column=1, columnspan = 3)

            buy_button = ctk.CTkButton(self.results_frame, text="Buy", width=50, command=lambda t=result['tsym']: self.buy_action(t))
            buy_button.grid(row=idx+1, column=4, sticky = 'e')

            sell_button = ctk.CTkButton(self.results_frame, text="Sell" , width=50, command=lambda t=result['tsym']: self.sell_action(t))
            sell_button.grid(row=idx+1, column=5, sticky = 'e')

    def buy_action(self, tsym):
        order_window = OrderWindow(tsym, "B", self.exchange, self.order_manager)
        order_window.mainloop()
            # try:
            #     # Implement the buy action for the specified token
            #     ret = self.api.place_order(buy_or_sell='B', product_type='C',
            #                             exchange='NSE', tradingsymbol=tsym,
            #                             quantity=1, discloseqty=0, price_type='SL-LMT', price=200.00, trigger_price=199.50,
            #                             retention='DAY', remarks='Buy order')
            #     tkinter.messagebox.showinfo("Order Placed", "Buy order has been placed successfully.")
            # except Exception as e:
            #     tkinter.messagebox.showerror("Order Failed", f"Failed to place buy order: {e}")

    def sell_action(self, tsym):
        order_window = OrderWindow(tsym, "S", self.exchange, self.order_manager)
        order_window.mainloop()
        # try:
        #     # Implement the sell action for the specified token
        #     ret = self.api.place_order(buy_or_sell='S', product_type='C',
        #                                 exchange='NSE', tradingsymbol=token,
        #                                 quantity=1, discloseqty=0, price_type='SL-LMT', price=200.00, trigger_price=199.50,
        #                                 retention='DAY', remarks='Sell order')
        #     tkinter.messagebox.showinfo("Order Placed", "Sell order has been placed successfully.")
        # except Exception as e:
        #     tkinter.messagebox.showerror("Order Failed", f"Failed to place sell order: {e}")

    def refresh_ltp_thread(self):
        refresh_ltp_thread = threading.Thread(target=self.refresh_ltps)
        refresh_ltp_thread.start()

    def open_algo_window(self):
        algo_page = Algo(self.order_manager, self.api)

        algo_page.mainloop()

class TradesPortfolioWindow(ctk.CTkToplevel):
    def __init__(self, master, order_manager):
        super().__init__(master)
        self.order_manager = order_manager
        self.title("Trades and Portfolio")
        self.geometry("800x420")

        # Grid configuration
        self.columnconfigure((0, 1, 2, 3), weight=1)

        self.portfolio_frame = ctk.CTkScrollableFrame(self)
        self.portfolio_frame.grid(row=0, column=1, columnspan=3, sticky='nsew')
        self.portfolio_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.portfolio_label = ctk.CTkLabel(self.portfolio_frame, text="Portfolio:")
        self.portfolio_label.grid(row=0, column=0, columnspan=5)

        ctk.CTkLabel(self.portfolio_frame, text="Instrument").grid(row=1, column=0)
        ctk.CTkLabel(self.portfolio_frame, text="Quantity").grid(row=1, column=1)

        # Display portfolio data from the database
        portfolio_data = self.order_manager.get_portfolio_data_from_database()
        for idx, (instrument, quantity) in enumerate(portfolio_data, start=2):
            ctk.CTkLabel(self.portfolio_frame, text=instrument).grid(row=idx, column=0)
            ctk.CTkLabel(self.portfolio_frame, text=quantity).grid(row=idx, column=1)

        self.orders_frame = ctk.CTkScrollableFrame(self)
        self.orders_frame.grid(row=1, column=1, columnspan=3, sticky='nsew')
        self.orders_frame.columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.trade_label = ctk.CTkLabel(self.orders_frame, text="Trades:")
        self.trade_label.grid(row=0, column=0, columnspan=5)

        ctk.CTkLabel(self.orders_frame, text="Instrument").grid(row=1, column=0)
        ctk.CTkLabel(self.orders_frame, text="Qty").grid(row=1, column=1)
        ctk.CTkLabel(self.orders_frame, text="Price").grid(row=1, column=2)
        ctk.CTkLabel(self.orders_frame, text="B/S").grid(row=1, column=3)
        ctk.CTkLabel(self.orders_frame, text="PnL").grid(row=1, column=4)
        ctk.CTkLabel(self.orders_frame, text="Time").grid(row=1, column=5)

        # Display trade data from the database
        trade_data = self.order_manager.get_trade_data_from_database()
        for idx, trade in enumerate(trade_data, start=2):
            ctk.CTkLabel(self.orders_frame, text=trade.instrument).grid(row=idx, column=0)
            ctk.CTkLabel(self.orders_frame, text=trade.qty).grid(row=idx, column=1)
            ctk.CTkLabel(self.orders_frame, text=trade.entry_price).grid(row=idx, column=2)
            ctk.CTkLabel(self.orders_frame, text=trade.transaction_type).grid(row=idx, column=3)
            ctk.CTkLabel(self.orders_frame, text=f"{trade.exit_price - trade.entry_price}" if trade.exit_price else "").grid(row=idx, column=4)  # Display exit price
            ctk.CTkLabel(self.orders_frame, text=trade.entry_timestamp).grid(row=idx, column=5)
            
            if trade.monitoring_flag:                   
                square_off_button = ctk.CTkButton(self.orders_frame, text="Square Off", width=20,
                                    command=lambda order_id=trade.order_id
                                    , instrument = trade.instrument: self.square_off(order_id, instrument))
                square_off_button.grid(row=idx, column=6)


    def square_off(self, order_id, instrument):
        # Call the square_off method of the order manager with the provided order_id
        ex_seg = "NFO"
        ltp = self.order_manager.api.get_quotes(ex_seg,
                            self.order_manager.api.searchscrip(exchange=ex_seg,
                                            searchtext=instrument)['values'][0]['token'])['lp']
        # print(self.order_manager.api.searchscrip(exchange=ex_seg,
        #                                     searchtext=instrument)['values'][0]['token'])
        self.order_manager.square_off(order_id, ltp)

if __name__ == "__main__":
    app = App()
    app.mainloop()