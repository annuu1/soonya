import datetime
import time
import threading
import customtkinter as ctk
import  tkinter.messagebox

import pandas as pd
from strategies import Strategy
from const import kotak
from telegram import Bot
from neo_api_client import NeoAPI
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mplfinance as mpf
import plotly.graph_objects as go
from plotly.subplots import make_subplots


from live_fetch import subscribe_to_live_data

class Algo(ctk.CTk):
    def __init__(self, order_manager, soonya_api):
        super().__init__()

        self.order_manager = order_manager
        self.soonya_api = soonya_api

        self.geometry('900x350')
        self.title('Algorithmic Trading Home')

        #Grid Configuration
        self.columnconfigure((0,1,2,3), weight= 1)

        self.client = None
        self.ohlc_converter = OHLCConverter()
        self.message_handler = MessageHandler(self.ohlc_converter)
        self.error_handler = ErrorHandler()
        self.telegram_notifier = TelegramNotifier(token='6948246303:AAGtwyniJ7t3Wk2_Gri6i8UmOJydKLKG6AU', chat_id='-1002039236264')
        
        self.side_frame = SideFrame(self, self.ohlc_converter)

        # self.main_frame = MainFrame(self)
        self.header = Header(self, self.ohlc_converter, self.message_handler
                             , self.error_handler, self.telegram_notifier, self.order_manager
                             , self.client, self.soonya_api)

class Header(ctk.CTkFrame):
    def __init__(self, master, ohlc_converter, message_handler, error_handler, telegram, order_manager, client, soonya_api): 
        super().__init__(master)

        self.ohlc_converter = ohlc_converter
        self.message_handler = message_handler
        self.error_handler = error_handler
        self.telegram = telegram
        self.order_manager = order_manager
        self.client = client
        self.soonya_api = soonya_api

        self.grid(row = 0, column = 2, columnspan = 4, sticky = 'nsew', padx = (2,2), pady = (0,0))
        
        #Grid Configuration
        self.columnconfigure((0,1,2,3), weight= 1)

        self.titleLabel = ctk.CTkLabel(self, text='Quant Quest', font=('Arial', 18))
        self.titleLabel.grid(row=0, column=0, pady=10)

        # Create buttons
        self.orderButton = ctk.CTkButton(self, text='Login', command=self.login)
        self.orderButton.grid(row=0, column=2, padx=10, pady=5)

        self.orderButton = ctk.CTkButton(self, text='Start Algo', command=self.run_strategy)
        self.orderButton.grid(row=0, column=3, padx=10, pady=5)

        self.portfolioButton = ctk.CTkButton(self, text='Subscribe', command=self.subscribe)
        self.portfolioButton.grid(row=0, column=4, padx=10, pady=5)

        self.call_token_label = ctk.CTkLabel(self, text='Call Token')
        self.call_token_label.grid(row=1, column=0)

        self.call_token = ctk.CTkEntry(self)
        self.call_token.grid(row = 1, column = 1)

        self.put_token_label = ctk.CTkLabel(self, text='Put Token')
        self.put_token_label.grid(row=1, column=2)

        self.put_token = ctk.CTkEntry(self)
        self.put_token.grid(row = 1, column = 3)


    def login(self):
        if not self.client:
            client = KotakNeo(self.message_handler, self.error_handler)
            client.login()
            self.client = client.client
        else:
            tkinter.messagebox.showinfo("Login Failed", "Already logged in")
        
    def subscribe(self) :  
        inst_tokens = [{"instrument_token": "26009", "exchange_segment": "nse_cm"}]
        if self.client != None:
            subscribe_thread = threading.Thread(target=subscribe_to_live_data, args=(self.client, inst_tokens))
            subscribe_thread.start()
        else:
            tkinter.messagebox.showerror("Cann't subscribe", "Please login first")

    def run_strategy(self):
        strategy_instance = Strategy(ohlc_converter=self.message_handler.ohlc_converter
                    , order_manager=self.order_manager, telegram_notifier = self.telegram
                    , soonya_api=self.soonya_api, header= self)
        strategy_instance.start_strategy()

class MainFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.grid(row = 1, column = 0, columnspan = 4, sticky = 'nsew')
        #Grid Configuration
        self.columnconfigure((0,1,2,3), weight= 1)

        self.call_token_label = ctk.CTkLabel(self, text='Call Token')
        self.call_token_label.grid(row=0, column=0)

        self.call_token = ctk.CTkEntry(self)
        self.call_token.grid(row = 0, column = 1)

        self.put_token_label = ctk.CTkLabel(self, text='Put Token')
        self.put_token_label.grid(row=0, column=2)

        self.put_token = ctk.CTkEntry(self)
        self.put_token.grid(row = 0, column = 3)

class SideFrame(ctk.CTkFrame):
    def __init__(self, master, ohlc_converter):
        super().__init__(master)
        self.ohlc_converter = ohlc_converter

        self.grid(row=0, column=0, sticky="nsew", padx = (2,2), pady = (0,0))

        self.indices_list = {'Select Instrument': "^NSEBANK", "NIFTY 50": "^NSEI", "BANK NIFTY": "^NSEBANK"
                             , "MIDCAP" : "^NSEMDCP50", "FINNIFTY" : "NIFTY_FIN_SERVICE.NS"}

        self.indices_var = ctk.StringVar(value='Select Instrument')
        self.indices_values = ['Select Instrument', 'NIFTY 50', "BANK NIFTY", "MIDCAP", "FINNIFTY"]
        self.indices = ctk.CTkComboBox(self, values=self.indices_values)
        self.indices.grid(row=0, column=0)
        self.indices.set('NIFTY 50')  # Set default value

        ctk.CTkLabel(self, text="Algo Trading").grid(row=1, column=0)

        today = datetime.date.today()
        # Calculate yesterday and tomorrow
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        ctk.CTkLabel(self, text="Start Date").grid(row=2, column=0)
        self.start_date = ctk.CTkEntry(self)
        self.start_date.grid(row=3, column=0, sticky = 'nsew')
        self.start_date.insert(0, yesterday.strftime("%Y-%m-%d"))  # Set default value

        ctk.CTkLabel(self, text="End Date").grid(row=4, column=0)
        self.end_date = ctk.CTkEntry(self)
        self.end_date.grid(row=5, column=0)
        self.end_date.insert(0, tomorrow.strftime("%Y-%m-%d"))  # Set default value

        ctk.CTkLabel(self, text="Time Frame").grid(row=6, column=0)
        self.time_frame = ctk.CTkComboBox(self, values=['1m', '5m', '10m', '15m', '30m', '1D', '1M'])
        self.time_frame.grid(row=7, column=0)
        self.time_frame.set('5m')  # Set default value

        self.update_ohlc = ctk.CTkButton(self, text="Update OHLC", command= self.update_ohlc)
        self.update_ohlc.grid(row = 8, column = 0)

        self.show_chart_btn = ctk.CTkButton(self, text="Show Candlestick Chart", command=self.show_candlestick_chart)
        self.show_chart_btn.grid(row=9, column=0)

    def update_ohlc(self):
        indice = self.indices.get()
        start = self.start_date.get()
        end = self.end_date.get()
        time_frame = self.time_frame.get()
        
        data = []
        df = yf.download(self.indices_list[indice], start, end, interval=time_frame)
        data.extend(self.df_to_dict(df))
        self.ohlc_converter.ohlcdf = data
        print(f"updated the dataframe from {start} to {end} at {time_frame}")

    def df_to_dict(self, df):
        data = []
        for index, row in df.iterrows():
            timestamp = index.strftime('%d-%m-%Y %H:%M')
            ohlc_data = {
                'timestamp': timestamp,
                'Open': row['Open'],
                'High': row['High'],
                'Low': row['Low'],
                'Close': row['Close']
            }
            data.append(ohlc_data)
        return data
    
    def show_candlestick_chart(self):
        # Prepare data for candlestick chart
        data = self.ohlc_converter.ohlcdf

        df = pd.DataFrame(data)
        df['Volume'] = 102
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Create figure with subplots
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                            vertical_spacing=0.02, subplot_titles=('Candlestick Chart', 'Volume'))

        # Add candlestick chart
        fig.add_trace(go.Candlestick(x=df.index,
                                    open=df['Open'], high=df['High'],
                                    low=df['Low'], close=df['Close'],
                                    name='Candlestick'), row=1, col=1)

        # Add volume bar chart
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'],
                            marker_color='gray', name='Volume'), row=2, col=1)

        # Update layout
        fig.update_layout(title='Interactive Candlestick Chart',
                        xaxis_rangeslider_visible=False)

        # Display the chart
        fig.show()

    def show_candlestick_chart_mpl(self):
            # Prepare data for candlestick chart
            data = self.ohlc_converter.ohlcdf

            df = pd.DataFrame(data)
            df['Volume'] = 102
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Create a new window for the candlestick chart
            chart_window = ctk.CTk()
            chart_window.title("Candlestick Chart")
            chart_window.geometry("800x600")

            # Plot the candlestick chart
            mpf.plot(df, type='candle', mav=(5, 8, 13), style='charles', volume=True)

            # Display the window
            chart_window.mainloop()



class OHLCConverter:
    def __init__(self):
        self.ltp = None
        self.ltp_list = []
        self.ohlcdf = []

    def convert_ohlc(self, dt, ltp):
        self.ltp = ltp
        self.ltp_list.append(ltp)
        open_price = self.ltp_list[0]
        low = min(self.ltp_list)
        high = max(self.ltp_list)
        close = self.ltp_list[-1]
        timestamp = dt
        candle = {
            'timestamp': timestamp,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close
        }
        try:
            ohlc_time = self.ohlcdf[-1]['timestamp']
            if ohlc_time == timestamp:
                self.ohlcdf[-1]['Open'] = open_price
                self.ohlcdf[-1]['High'] = high
                self.ohlcdf[-1]['Low'] = low
                self.ohlcdf[-1]['Close'] = close
            else:
                self.ohlcdf.append(candle)
                self.ltp_list.clear()
                self.ltp_list.append(ltp)

        except Exception as e:
            print(f"exception in ohlc converter : {e}")
            if not self.ohlcdf:
                # If ohlcdf is empty, create the first candle
                open_price = ltp
                low = ltp
                high = ltp
                close = ltp
                self.ohlcdf.append({
                    'timestamp': dt,
                    'Open': open_price,
                    'High': high,
                    'Low': low,
                    'Close': close
                })

class MessageHandler:
    def __init__(self, ohlc_converter):
        self.ohlc_converter = ohlc_converter

    def on_message(self, message):
        # print(message)
        key = 'ltp'
        timestamp = int(time.time())
        dt = datetime.fromtimestamp(timestamp)
        try:
            ltp = float(message[0][key])
            timestamp_str = message[0]['fdtm']
            dt_object = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S')
            formatted_dt = dt_object.strftime('%d-%m-%Y %H:%M')
            print(formatted_dt)
            self.ohlc_converter.convert_ohlc(formatted_dt, ltp)
        except KeyError as e:
            print(f"Error accessing '{key}' key: {e}")

class ErrorHandler:
    def on_error(self, error_message):
        print(error_message)

class KotakNeo:
    def __init__(self, message_handler, error_handler):
        self.client = NeoAPI(
            consumer_key = kotak['consumer_key'],
            consumer_secret = kotak['secretKey'],
            environment = 'uat',
            on_message = message_handler.on_message,
            on_error = error_handler.on_error,
            on_close=None,
            on_open=None,
            access_token=kotak['access_token'],
        )

    def login(self):
        # client = NeoAPI(consumer_key = Config.consumer_key, consumer_secret = Config.secretKey, 
        #         environment='uat', on_message=self.on_message, on_error=self.on_error, on_close=None, on_open=None, access_token = Config.access_token)
        print(self.client)
        print(self.client.login(mobilenumber=kotak['mobileNumber'], password=kotak['login_password']))
        print(self.client.session_2fa(OTP=kotak['MPIN']))
        return self.client

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    def send_trade_alert(self, signal = None, symbol = None, ltp = None, premium = None, sl = None, entry_timestamp = None):
        message = f"Options Trade Alert 🚀\n In testing Phase \n"
        ltp = int(ltp)
    
        if signal == "B":
            message += f"📈 Buy {symbol}@ {round(ltp, -2)}CE\n"
            message += f"🔢 Strike Price: {round(ltp, -2)} @ {premium}\n"
        elif signal == "S":  # Corrected the condition for "Sell"
            message += f"📈 Buy {symbol}@ {round(ltp, -2)}PE\n"
            message += f"🔢 Strike Price: {round(ltp, -2)} @ {premium}\n"
    
        message += f"⏰ Entry Time: {entry_timestamp}\n"
        message += f"🛑 Stop-Loss: {sl:.2f}\n"
        
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def send_trade_exit(self, trade_data = None):
        message = f"*Options Trade Exit 🛑*\n\n"
        message += f'{trade_data}'
        self.bot.send_message(chat_id=self.chat_id, text=message)

    def start_trade_alert(self, signal, symbol, ltp, premium, sl, entry_timestamp):
        tel_thread = threading.Thread(target=self.send_trade_alert, args=(signal, symbol, ltp, premium, sl, entry_timestamp))
        tel_thread.start()

    def start_trade_exit(self, trade_data):
        tel_thread = threading.Thread(target=self.send_trade_exit, args=(trade_data,))
        tel_thread.start()
