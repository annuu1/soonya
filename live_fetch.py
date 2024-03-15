import time
import time
import threading


subscribe = True
def subscribe_to_live_data(client, inst_tokens):
    while subscribe:
        time.sleep(10)
        try:
            client.subscribe(instrument_tokens=inst_tokens, isIndex=False, isDepth=False)
        except Exception as e:
            print(f'Exception in subscribe: {e}')
            time.sleep(1)