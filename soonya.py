import sqlite3
import customtkinter as ctk
from const import finvasia
from api_helper import ShoonyaApiPy
import threading

root = ctk.CTk()
root.geometry("930x350")

def startScanThread():
    print("Starting the scan")
    thread = threading.Thread(target=startScan)
    thread.start()

def startScan():
    widgets = scrollable_frame.winfo_children()
    i = 0
    instruments= []
    size = len(widgets)/6
    print(size)

    while (i<size):
        try:
            instruments.append(widgets[i*6].cget("text"))
            quote = api.get_quotes("NSE", api.searchscrip(exchange= "NSE", searchtext=widgets[i*6]
                                           .cget("text"))['values'][0]['token'])          

            print(quote['lp'])
            widgets[i*6+1].configure(text = quote['lp'])
            widgets[i*6+2].configure(text = quote['lp'])
            widgets[i*6+3].configure(text = quote['lp'])
            widgets[i*6+4].configure(text = quote['lp'])
            widgets[i*6+5].configure(text = quote['lp'])
        except Exception as e:
            print(f"The exception {e}")
        i+=1

def connectBroker():
    global api
    api = ShoonyaApiPy()
    ret = api.login(userid=finvasia['user'], password=finvasia['pwd']
                        , twoFA=finvasia['factor2'], vendor_code=finvasia['vc']
                        , api_secret=finvasia['app_key'], imei=finvasia['imei'])
    print(ret)



def addDb():
    conn = sqlite3.connect("stockmarket.db")
    # conn.execute("create table stocks(name text not null, indices text not null, primary key(name, indices))")
    stockList = stockName.get().split(",")
    for name in stockList:
        conn.execute("insert into stocks(name, indices) values('"+name+"','"+indices.get()+"')")
    conn.commit()
    conn.close()
    print("DB updated")

def refreshTable(value = None):
    i = 0
    conn= sqlite3.connect("stockmarket.db")
    cursor = conn.execute("select * from stocks where indices = '"+indices.get()+"'")
    print(indices.get())
    # scrollable_frame = ctk.CTkScrollableFrame(root, )
    # scrollable_frame.grid(row=1, column=0, sticky="nsew")
    for row in cursor:
        ctk.CTkLabel(scrollable_frame, text= row[0], width= 25).grid(row = i, column = 0)
        ctk.CTkLabel(scrollable_frame, text= "", width= 100).grid(row = i, column = 1)
        ctk.CTkLabel(scrollable_frame, text= "", width= 100).grid(row = i, column = 2)
        ctk.CTkLabel(scrollable_frame, text= "", width= 100).grid(row = i, column = 3)
        ctk.CTkLabel(scrollable_frame, text= "", width= 100).grid(row = i, column = 4)
        ctk.CTkLabel(scrollable_frame, text= "", width= 100).grid(row = i, column = 5)
        i+=1

def clearWidget():
    widgets = scrollable_frame.winfo_children()
    i = 0
    while(i<len(widgets)):
        widgets[i].destroy()
        i+=1



topFrame = ctk.CTkFrame(root)
topFrame.grid(row=0, column=0, sticky="nsew")
ctk.CTkButton(topFrame, text="Connect" , command = connectBroker).grid(row=0, column=0)
ctk.CTkLabel(topFrame, text = "Index").grid(row = 0, column=1)
indices = ctk.CTkComboBox(topFrame, values=["NIFTY 50", "BANK NIFTY", "NIFTY IT"], command= refreshTable)
# indices.bind("<<ComboboxSelected>>", refreshTable)

indices.grid(row = 0, column = 2)
ctk.CTkLabel(topFrame, text="Name").grid(row= 0, column= 3)
stockName = ctk.CTkEntry(topFrame)
stockName.grid(row= 0, column= 4)
ctk.CTkButton(topFrame, text= "Add to DB", command= addDb).grid(row=0, column=5)
ctk.CTkButton(topFrame, text= "start", command= startScanThread).grid(row=0, column=6)
ctk.CTkButton(topFrame, text= "stop").grid(row=0, column=7)
# topFrame.pack()
#
titleFrame = ctk.CTkFrame(root)
titleFrame.grid(row = 1, column = 0, sticky= "nsew")
ctk.CTkLabel(topFrame, text = "Name").grid(row = 1, column=0)
ctk.CTkLabel(topFrame, text = "high").grid(row = 1, column=1)
ctk.CTkLabel(topFrame, text = "Low").grid(row = 1, column=2)
ctk.CTkLabel(topFrame, text = "volume").grid(row = 1, column=3)
ctk.CTkLabel(topFrame, text = "ltp").grid(row = 1, column=4)
ctk.CTkLabel(topFrame, text = "change").grid(row = 1, column=5)
# titleFrame.pack()


# create scrollable frame
scrollable_frame = ctk.CTkScrollableFrame(root, )
scrollable_frame.grid(row=1, column=0, sticky="nsew")
# scrollable_frame.grid_columnconfigure(0, weight=1)
scrollable_frame_switches = []

root.mainloop()


