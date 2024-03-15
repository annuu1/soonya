import datetime
import json
import threading
import time
from typing import Tuple
import customtkinter as ctk
import tkinter.messagebox as ttkmsg

class Order:
    def __init__(self, instrument=None, qty=None, entry_price=None,
                 transaction_type=None, entry_timestamp=None, exit_price = None, exit_premium = None,
                max_loss = None, max_profit = None, expiry = None, note=None):
        if entry_timestamp is None:
            entry_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.order_id = None
        self.entry_timestamp = entry_timestamp
        self.instrument = instrument
        self.entry_price = entry_price
        self.qty = qty
        self.transaction_type = transaction_type
        self.exit_price = exit_price
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.exit_timestamp = None
        self.dynamic_max_loss = None
        self.dynamic_max_profit = None
        self.note = note
        self.monitoring_flag = True


    def calculate_max_loss_profit(self):
        if self.premium is not None and self.exit_premium is not None:
            if self.transaction_type == 'B':
                self.max_loss = (self.exit_premium - self.premium)* self.qty
                self.max_profit = (self.exit_premium - self.premium) * self.qty
            elif self.transaction_type == 'S':
                self.max_loss = (self.exit_premium - self.premium)* self.qty * self.qty
                self.max_profit = (self.exit_premium - self.premium)* self.qty * self.qty

    def update_dynamic_max_loss_profit(self, current_price):
        if current_price is not None:
            if self.transaction_type == 'B':
                self.dynamic_max_loss = min(self.dynamic_max_loss, current_price)
                self.dynamic_max_profit = max(self.dynamic_max_profit, current_price)
            elif self.transaction_type == 'S':
                self.dynamic_max_loss = min(self.dynamic_max_loss, current_price)
                self.dynamic_max_profit = max(self.dynamic_max_profit, current_price)
                
    def stop_monitoring(self):
        self.monitoring_flag = False

    def start_monitoring(self):
        self.monitoring_flag = True
        

class OrderManager:
    def __init__(self, api):
        self.api = api
        self.orders = []
        self.portfolio = {'anu': 45, 'anu1': 45, 'anu2': 45, 'anu3': 45,'anu4': 45
                          , 'anu14': 45, 'anu24': 45, 'anu34': 45}
        
    def save_data(self):
        data = {
            "orders": [order.__dict__ for order in self.orders],
            "portfolio": self.portfolio
        }
        with open("trades_portfolio_data.json", "w") as file:
            json.dump(data, file)

    def place_order(self, instrument=None, entry_price=None, note=None, qty=None, transaction_type=None):
        new_order = Order(instrument=instrument, entry_timestamp=None, qty=qty, entry_price=entry_price,
                      transaction_type=transaction_type, note=note)
        
        self.orders.append(new_order)
        new_order.order_id = len(self.orders)

        #start monitoring the ltps
        # monitoring_thread = threading.Thread(target=self.monitor_trade, args=(new_order.order_id,))
        # monitoring_thread.start()
        self.save_data()
        return new_order

    def square_off(self, order_id, exit_price = None):

        order_to_square_off = next((order for order in self.orders if order.order_id == order_id), None)
        if order_to_square_off:

            ltp = '48750'
    
            # Assuming a simple exit condition (e.g., exit at current market price)
            order_to_square_off.exit_price = exit_price
            order_to_square_off.exit_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            order_to_square_off.monitoring_flag = False
            
            self.save_data()
            
            # Calculate max_loss and max_profit
            # order_to_square_off.calculate_max_loss_profit()
            # Stop monitoring for this order
            # order_to_square_off.stop_monitoring()
            
            print(f"Square off Order {order_id} - Exit Price: {order_to_square_off.exit_price}")
        else:
            print(f"Order with order_id {order_id} not found.")


class OrderWindow(ctk.CTk):
    def __init__(self, tsym = 'ACC-EQ', order_type = 'S', ex_seg = "NSE", order_manager = None):
        super().__init__()
        self.geometry('500x250')
        self.tsym = tsym
        self.type = order_type
        self.ex_seg = ex_seg
        self.fg_color = f"Red" if self.type == "S" else "Green"
        self.order_manager = order_manager

        #Grid configuration
        self.columnconfigure((0,1,2,3,4), weight=1)
        self.rowconfigure(0 , weight=0)
        self.rowconfigure((1, 2, 3, 4, 5), weight=1)

        self.head_label = ctk.CTkLabel(self, text= f'{self.type} --> {self.tsym}', fg_color= self.fg_color)
        self.head_label.grid(row = 0, column = 0, columnspan = 5, sticky = 'nsew')

        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row =1, column = 0, columnspan = 5, rowspan = 6, sticky = 'nsew')
        
        #Grid Configuration
        self.top_frame.columnconfigure(0 , weight=0)
        self.top_frame.columnconfigure((1,2,3,4), weight=1)
        self.top_frame.rowconfigure(0 , weight=0)
        self.top_frame.rowconfigure((1, 2, 3, 4, 5), weight=1)
        
        ctk.CTkLabel(self.top_frame, text= "Entry Price:", width = 50).grid(row = 0, column = 0, sticky = 'nsew')
        self.entry_price = ctk.CTkEntry(self.top_frame)
        self.entry_price.grid(row = 0, column = 1)

        ctk.CTkLabel(self.top_frame, text= "Quantity:", width = 50).grid(row = 1, column = 0, sticky = 'nsew')
        self.qty_price = ctk.CTkEntry(self.top_frame)
        self.qty_price.grid(row = 1, column = 1)
        self.qty_price.insert(0, '1')

        ctk.CTkLabel(self.top_frame, text='Note:').grid(row = 2, column = 0)
        self.note = ctk.CTkEntry(self.top_frame)
        self.note.grid(row = 2, column = 1, pady= (2,2))

        self.order_place = ctk.CTkButton(self.top_frame, text="Place Order", command=self.order_place)
        self.order_place.grid(row = 6, column = 0, columnspan = 6)

        # Start a separate thread to continuously update LTP
        self.running_thread = True  # Define running_thread as an attribut
        self.ltp_thread = threading.Thread(target=self.update_ltp)
        self.ltp_thread.daemon = True  # Daemonize the thread so it will be terminated when the main program exits
        self.ltp_thread.start()
        
        #Destroye window Event-
        self.protocol("WM_DELETE_WINDOW", self.destroy_widnow)
    
    def order_place(self):
        # print(self.order_manager.api.get_quotes("NSE", '26009'))
        if self.entry_price.get() and self.qty_price.get() and self.tsym:
            self.order_manager.place_order(instrument=self.tsym, entry_price=self.entry_price.get()
                                        , note=self.note.get(), qty=self.qty_price.get()
                                , transaction_type="B" if self.type == "B" else "S")
            ttkmsg.showinfo('Successful', 'Order Placed successfully')
        else:
            ttkmsg.showerror('Unuccessful', 'Please fill all the details')
            
    def update_ltp(self):
        try: 
            label_text = self.head_label.cget('text')
            while self.running_thread:
                ltp = self.order_manager.api.get_quotes(self.ex_seg,
                            self.order_manager.api.searchscrip(exchange=self.ex_seg,
                                            searchtext=self.tsym)['values'][0]['token'])['lp'] 
                  
                # lambda function to capture the current value of 'ltp'
                self.after(0, lambda ltp=ltp: self.head_label.configure(text=f'{label_text}   ({ltp})'))
                self.after(0, lambda ltp=ltp: self.entry_price.delete(0, ctk.END))
                self.after(0, lambda ltp=ltp: self.entry_price.insert(0 , str(ltp)))
        except Exception as e:
            print(e)

    def destroy_widnow(self):
        self.running_thread = False
        self.destroy()
        print("clsoed window")