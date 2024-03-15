import datetime
import json
import threading
import time
from typing import Tuple
import customtkinter as ctk
import tkinter.messagebox as ttkmsg
import sqlite3
from sqlite3 import Error

class Order:
    def __init__(self, order_id = None, instrument=None, qty=None, entry_price=None,
                 transaction_type=None, entry_timestamp=None, exit_price = None, exit_premium = None,
                max_loss = None, max_profit = None, expiry = None, note=None, monitoring_flag = True):
        if entry_timestamp is None:
            entry_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if order_id is None:
            self.order_id = datetime.datetime.now().strftime('%y%m%d%H%M%S')
        else:
            self.order_id = order_id

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
        self.monitoring_flag = monitoring_flag


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

class DatabaseManager:
    def __init__(self, db_file):
        self.conn = self.create_connection(db_file)
        self.create_tables()

    def create_connection(self, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            return conn
        except Error as e:
            print(e)
        return conn

    def create_tables(self):
        orders_table = """CREATE TABLE IF NOT EXISTS orders (
                            order_id INTEGER PRIMARY KEY,
                            entry_timestamp TEXT NOT NULL,
                            instrument TEXT NOT NULL,
                            qty INTEGER NOT NULL,
                            entry_price REAL NOT NULL,
                            transaction_type TEXT NOT NULL,
                            exit_price REAL,
                            max_loss REAL,
                            max_profit REAL,
                            exit_timestamp TEXT,
                            dynamic_max_loss REAL,
                            dynamic_max_profit REAL,
                            note TEXT,
                            monitoring_flag INTEGER
                        );"""
        portfolio_table = """CREATE TABLE IF NOT EXISTS portfolio (
                                symbol TEXT PRIMARY KEY,
                                quantity INTEGER NOT NULL
                            );"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(orders_table)
            cursor.execute(portfolio_table)
        except Error as e:
            print(e)

    def insert_order(self, order):
        sql = """INSERT INTO orders (order_id, entry_timestamp, instrument, qty, entry_price, transaction_type,
                exit_price, max_loss, max_profit, exit_timestamp, dynamic_max_loss, dynamic_max_profit, note,
                monitoring_flag) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        cursor = self.conn.cursor()
        cursor.execute(sql, (order.order_id, order.entry_timestamp, order.instrument, order.qty, order.entry_price,
                            order.transaction_type, order.exit_price, order.max_loss, order.max_profit,
                            order.exit_timestamp, order.dynamic_max_loss, order.dynamic_max_profit, order.note,
                            order.monitoring_flag))
        self.conn.commit()
        print('order stored in DB')
        return cursor.lastrowid


    def update_order_exit_info(self, order_id, exit_price, monitoring_flag = True):
        if not monitoring_flag:
            sql = """UPDATE orders SET exit_price = ? WHERE order_id = ?"""
            set_monitoring_flag = """UPDATE orders SET monitoring_flag = ? WHERE order_id = ?"""
            cursor = self.conn.cursor()
            cursor.execute(sql, (exit_price, order_id))
            cursor.execute(set_monitoring_flag, (False, order_id))
            self.conn.commit()
            print('The order updated with monitoring flag')
        else:
            sql = """UPDATE orders SET exit_price = ? WHERE order_id = ?"""
            cursor = self.conn.cursor()
            cursor.execute(sql, (exit_price, order_id))
            self.conn.commit()
            print('The order updated')

    def close_connection(self):
        if self.conn:
            self.conn.close()

    def get_portfolio_data(self):
        sql = "SELECT * FROM portfolio"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        portfolio_data = [(row[0], row[1]) for row in rows]
        return portfolio_data

    def get_trade_data(self):
        sql = "SELECT * FROM orders"
        cursor = self.conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        trade_data = []
        for row in rows:
            trade = Order(order_id = row[0], instrument=row[2], qty=row[3], entry_price=row[4],
                transaction_type=row[5], entry_timestamp=row[1], exit_price=row[6],
                max_loss=row[7], max_profit=row[8], expiry=row[9], note=row[12], monitoring_flag = row[13])
            trade_data.append(trade)
        return trade_data
        
    def get_orders_with_monitoring_flag(self, monitoring_flag=True):
        sql = "SELECT * FROM orders WHERE monitoring_flag = ?"
        cursor = self.conn.cursor()
        cursor.execute(sql, (monitoring_flag,))
        rows = cursor.fetchall()
        orders_data = []
        for row in rows:
            orders_data.append(row)
        return orders_data

class OrderManager:
    def __init__(self, api, db_file):
        self.api = api
        self.db_manager = DatabaseManager(db_file)
        self.orders = []
        self.portfolio = {}
        self.load_orders_with_monitoring_flag()

    # self.load_orders_with_monitoring_flag() #loading the order not squared off
    def load_orders_with_monitoring_flag(self):
        orders_data = self.db_manager.get_orders_with_monitoring_flag(True)
        for order_data in orders_data:
            order = Order(
                order_id=order_data[0],
                instrument=order_data[1],
                qty=order_data[2],
                entry_price=order_data[3],
                transaction_type=order_data[4],
                entry_timestamp=order_data[5]
            )
            self.orders.append(order)

    def place_order(self, instrument=None, entry_price=None, note=None, qty=None, transaction_type=None):
        new_order = Order(instrument=instrument, entry_timestamp=None, qty=qty, entry_price=entry_price,
                          transaction_type=transaction_type, note=note)
        order_id = self.db_manager.insert_order(new_order)
        new_order.order_id = order_id
        self.orders.append(new_order)
        return new_order

    def square_off(self, order_id, exit_price=None):
        order_to_square_off = next((order for order in self.orders if order.order_id == order_id), None)
        if order_to_square_off:
            order_to_square_off.exit_price = exit_price
            order_to_square_off.exit_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db_manager.update_order_exit_info(order_id, exit_price, monitoring_flag= False)
            print(f"Square off Order {order_id} - Exit Price: {order_to_square_off.exit_price}")
        else:
            print(f"Order with order_id {order_id} not found.")

    def get_portfolio_data_from_database(self):
        portfolio_data = self.db_manager.get_portfolio_data()
        return portfolio_data

    def get_trade_data_from_database(self):
        trade_data = self.db_manager.get_trade_data()
        return trade_data


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