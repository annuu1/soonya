from datetime import datetime
import pandas as pd
import pandas_ta as ta
import threading
import time
from datetime import datetime
import time
import threading

class Strategy:
    def __init__(self, ohlc_converter, order_manager, telegram_notifier, soonya_api, header):
        self.ohlc_converter = ohlc_converter
        self.order_manager = order_manager
        self.telegram_notifier = telegram_notifier
        self.soonya_api = soonya_api
        self.run_live = True
        self.signal = None
        self.in_trade = False
        self.order = None
        self.order1 =None
        # self.header_obj = header
        self.call_tk = header.call_token.get()
        self.put_tk = header.put_token.get()

        print(self.call_tk)
        self.trade_data = {'signal': None, 'entry': None, 'exit': None, 'sl_price': None,
                           'entry_timestamp': None, 'exit_timestamp': None, 'entry_premium': None,
                           'exit_premium': None, 'max_profit': None, 'max_loss': None}
        self.trades = None
        
    def calculate_indicators(self, data):
        # Calculate EMAs
        data['ema_low'] = ta.ema(data['Close'], length=5)
        data['ema_medium'] = ta.ema(data['Close'], length=8)
        data['ema_long'] = ta.ema(data['Close'], length=13)

        # Calculate Super Trend using pandas_ta
        data.ta.supertrend(length=10, multiplier=1.5, append=True)
        data.to_csv('dataframe1.csv')

    def execute_trade_logic(self, data, ltp):

        # self.order = self.order_manager.place_order(instrument=self.call_tk
        #                 , entry_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.call_tk)['lp'],
        #                                                     note='strategy1', qty=15, transaction_type='B',
        #                                                     )
        
        timestamp = int(time.time())
        dt = datetime.fromtimestamp(timestamp)
        message = ""

        # self.order_manager.square_off(order_id=self.order.order_id
        #                               , exit_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.call_tk)['lp'])

        self.signal = self.trade_data['signal']
        time.sleep(1)

        try:
            self.trade_data['sl_price'] = data['SUPERT_10_1.5'].iloc[-2]
            if self.in_trade and self.signal == "Sell":
                sl = self.trade_data['sl_price'] < ltp
                if sl:
                    self.trade_data['exit'] = ltp
                    self.trade_data['exit_timestamp'] = dt
                    self.in_trade = False
                    self.trade_data['signal'] = None
                    print('exiting the sell trade')
                    self.order_manager.square_off(order_id=self.order.order_id, exit_price=ltp)
                    self.order_manager.square_off(order_id=self.order.order_id
                            , exit_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.call_tk)['lp'])
                    # print(self.order.dynamic_max_profit)
                    
                    #send telegram
                    # message = f"\n*Trade Analysis:*\n"
                    # message += f"📈 @{self.order.dynamic_max_profit} *Max Gone:* {self.order.dynamic_max_profit}\n"
                    # self.telegram_notifier.start_trade_exit(message)
                    
                    time.sleep(5)

            elif self.in_trade and self.signal == "Buy":
                sl = self.trade_data['sl_price'] > ltp

                if sl:
                    self.trade_data['exit'] = ltp
                    self.trade_data['exit_timestamp'] = dt
                    self.in_trade = False
                    self.trade_data['signal'] = None
                    print('exiting the buy trade')
                    self.order_manager.square_off(order_id=self.order.order_id, exit_price=ltp)
                    self.order_manager.square_off(order_id=self.order1.order_id
                        , exit_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.call_tk)['lp'])
                    # print(self.order.dynamic_max_profit)
                    
                    #send telegram
                    # message = f"\n*Trade Analysis:*\n"
                    # message += f"📈 @{self.order.exit_premium} *Max Gone:* {self.order.dynamic_max_profit}\n"
                    # self.telegram_notifier.start_trade_exit(message)
                    time.sleep(5)
            #Buy codition
            if data['ema_low'].iloc[-1] > data['ema_medium'].iloc[-1] and \
                    data['ema_low'].iloc[-1] > data['ema_long'].iloc[-1] and \
                    self.trade_data['signal'] != "Buy" and ltp > data['SUPERT_10_1.5'].iloc[-1]:
                # Buy signal
                self.trade_data['signal'] = "Buy"
                self.in_trade = True
                self.trade_data['entry'] = ltp
                self.trade_data['sl_price'] = min(data['Low'].iloc[-1], self.trade_data['entry'] - 30)
                self.trade_data['entry_timestamp'] = dt
                self.order = self.order_manager.place_order(instrument='BANKNIFTY', entry_price=ltp,
                                                            note='strategy1', qty=15, transaction_type='B',
                                                            )
                self.order1 = self.order_manager.place_order(instrument=self.call_tk
                        , entry_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.call_tk)['lp'],
                                                            note='strategy1', qty=15, transaction_type='B',
                                                            )
                
                # self.telegram_notifier.start_trade_alert(signal="B", symbol='BANKNIFTY', ltp=int(ltp), premium=self.order.premium, sl=self.trade_data['sl_price'], entry_timestamp=dt)
            
            #Sell condition
            elif data['ema_low'].iloc[-1] < data['ema_medium'].iloc[-1] and \
                    data['ema_low'].iloc[-1] < data['ema_long'].iloc[-1] and \
                    self.trade_data['signal'] != "Sell" and ltp < data['SUPERT_10_1.5'].iloc[-1]:
                # Sell signal
                self.trade_data['signal'] = "Sell"
                self.in_trade = True
                self.trade_data['entry'] = ltp
                self.trade_data['sl_price'] = min(data['High'].iloc[-1], self.trade_data['entry'] + 30)
                self.trade_data['entry_timestamp'] = dt
                self.order = self.order_manager.place_order(instrument='BANKNIFTY', entry_price=ltp,
                                                            strategy='strategy1', qty=15, transaction_type='S',
                                                            )
                
                self.order1 = self.order_manager.place_order(instrument=self.put_tk
                            , entry_price=self.soonya_api.get_quotes(exchange ="NFO", token = self.put_tk)['lp'],
                                                            strategy='strategy1', qty=15, transaction_type='S',
                                                            )
                # self.telegram_notifier.start_trade_alert(signal="S", symbol='BANKNIFTY', ltp=int(ltp), premium=self.order.premium, sl=self.trade_data['sl_price'], entry_timestamp=dt)

        except Exception as e:
            print(f"exception caused while testing {e}")

        if datetime.now().second % 50 == 0:
            print(f"trade - {self.trade_data}")
            print('\n')

    def test_strategy(self):
        while self.run_live:
            ohlc_data = self.ohlc_converter.ohlcdf  # Access data from the ohlc_converter
            if not ohlc_data:
                print('No candle Data Found')
            else:
                # print(ohlc_data)
                data = pd.DataFrame(ohlc_data)
    
                self.calculate_indicators(data)
                
                # Assuming ltp is available from somewhere in your code
                ltp = self.ohlc_converter.ltp # Your code to get the latest price
    
                self.execute_trade_logic(data, ltp)
            time.sleep(1)
    
    def start_strategy(self):
        test_strategy_thread = threading.Thread(target=self.test_strategy)
        test_strategy_thread.start()

