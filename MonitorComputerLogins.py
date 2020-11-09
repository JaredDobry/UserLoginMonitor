import tkinter as tk
import tkinter.messagebox as mb
import tkinter.simpledialog as sd
import subprocess as sp
import queue
import time
import threading

QUERY_EXE = 'C:\\Windows\\System32\\query.exe'
QUERY_FREQ = 10.0 #once every 10 sec

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title('User Login Monitor') 
        tk.Label(self, text = 'Entry Table').pack(fill = 'x', padx = 5, pady = 5)
        self.entryFrame = tk.Frame(self)
        self.entryFrame.pack(expand = 'true', fill = 'both')
        tk.Button(self, text = 'New Query', command = self.AddEntry).pack(side = 'right', padx = 5, pady = 5)

    def AddEntry(self):
        computerName = sd.askstring('User Login Monitor', 'Input computer name:')
        Entry(self.entryFrame, self, computerName).pack(fill = 'x')

class Entry(tk.Frame):
    def __init__(self, parent, master, computerName):
        self.master = master
        self.computerName = computerName
        tk.Frame.__init__(self, parent)
        tk.Label(self, text = 'Computer: ' + computerName).pack(side = 'left', padx = 5, pady = 5)
        tk.Button(self, text = 'x', command = self.HandleClose).pack(side = 'right', padx = 5, pady = 5)
        self.activeLabel = tk.Label(self, text = 'Active User: Querying...')
        self.activeLabel.pack(side = 'right', padx = 5, pady = 5)
        self.q = queue.Queue()
        self.killQ = queue.Queue()
        threading.Thread(target = Poll, args = (computerName, self.q, self.killQ, QUERY_FREQ), daemon = True).start()
        self.after(16, self.Poll)
    
    def HandleClose(self):
        self.killQ.put(True)
        self.destroy()

    def Poll(self):
        try:
            item = self.q.get_nowait()
            if item == 'ERROR':
                mb.showerror('User Login Monitor', 'Invalid query: ' + self.computerName)
                self.HandleClose()
            elif item == 'None':
                self.activeLabel.config(text = 'Active User: None')
            else:
                self.activeLabel.config(text = 'Active User: ' + item)
        except queue.Empty: ()
        self.after(16, self.Poll)

def Poll(computerName, returnQueue, killQueue, sleepTime):
    while True:
        #Check to kill the thread
        try:
            item = killQueue.get_nowait()
            if item == True:
                return
        except queue.Empty: ()

        process = sp.Popen(QUERY_EXE + ' user /server:' + computerName, shell = True, stdout = sp.PIPE, stderr = sp.STDOUT)
        out, err = process.communicate()
        conv = out.decode('utf-8')
        if 'Error' in conv:
            returnQueue.put('ERROR')
            return
        arr = conv.split('\r\n')
        found = False
        for line in arr:
            if 'Active' in line:
                found = True
                lineSplit = line.split(' ')
                returnQueue.put(lineSplit[1])
        if not found:
            returnQueue.put('None')
        time.sleep(sleepTime)

if __name__ == '__main__':
    app = App()
    app.mainloop()