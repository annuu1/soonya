from datetime import datetime
import time
import threading
import customtkinter as ctk
import  tkinter.messagebox
from strategies import Strategy
from const import kotak
from telegram import Bot
from neo_api_client import NeoAPI

from live_fetch import subscribe_to_live_data

class Algo(ctk.CTk):
    def __init__(self, order_manager, soonya_api):
        super().__init__()

        self.order_manager = order_manager
        self.soonya_api = soonya_api

        self.geometry('700x250')
        self.title('Algorithmic Trading Home')

        #Grid Configuration
        self.columnconfigure((0,1,2,3), weight= 1)

        self.client = None
        self.ohlc_converter = OHLCConverter()
        self.message_handler = MessageHandler(self.ohlc_converter)
        self.error_handler = ErrorHandler()
        self.telegram_notifier = TelegramNotifier(token='6948246303:AAGtwyniJ7t3Wk2_Gri6i8UmOJydKLKG6AU', chat_id='-1002039236264')
        
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

        self.grid(row = 0, column = 0, columnspan = 4, sticky = 'nsew')
        
        #Grid Configuration
        self.columnconfigure((0,1,2,3), weight= 1)

        self.titleLabel = ctk.CTkLabel(self, text='Quant Quest', font=('Arial', 18))
        self.titleLabel.grid(row=0, column=0, columnspan=2, pady=10)

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
        print(message)
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
