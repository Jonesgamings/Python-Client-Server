import socket
import _thread
import json
import tkinter as tk

class Server:

    def __init__(self, ui) -> None:
        self.port = 8000
        self.host = socket.gethostname()
        self.ip = socket.gethostbyname(self.host)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.ui = ui
        self.max_clients = 10
        self.clients = []
        self.client_info = {}
        self.running = False

    def genAuthCode(self, addr):
        tot = 0
        for digit in addr[0]:
            tot += hash(digit)

        tot = abs(tot)

        return str(tot)

    def clientThread(self, conn, addr):
        authCode = str(self.genAuthCode(addr))
        authMessage = f"AUTH-{authCode}"
        conn.send(authMessage.encode())

        while True:

            try:
                message = conn.recv(2048).decode()
                if message:
                    if "-" in message:
                        #AUTHENTICATION
                        split_message = message.split("-")
                        if split_message[0] == authCode:
                            self.authenticate(conn, split_message[1], addr)

                        if split_message[0] == "DISCONNECT":
                            if split_message[1] == authCode:
                                self.disconnect(conn)

                    elif message[0] == "/":
                        #COMMANDS
                        pass

                    else:
                        toSend = f"<{self.client_info[conn]['NAME']}>: {message}"
                        self.broadcast(toSend)

                else:
                    self.kick(conn)

            except Exception as e:
                if e.args[0] == 10038:
                    break

                else:
                    continue

        return "END"

    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message.encode())

            except:
                self.disconnect(client)

    def authenticate(self, conn, message, addr):
        message = message.replace("\'", "\"")
        data = json.loads(message)
        data["ADDR"] = addr
        self.client_info[conn] = data
        self.ui.addUser(json.loads(message)["NAME"], addr, conn)

    def kick(self, conn):
        addr = self.client_info[conn]["ADDR"]
        conn.sendall(f"DISCONNECT-{self.genAuthCode(addr)}".encode())
        conn.close()
        self.clients.remove(conn)
        self.client_info.pop(conn)

    def disconnect(self, conn):
        conn.close()
        self.clients.remove(conn)
        self.ui.disconnectKey(self.client_info[conn]["ADDR"])
        self.client_info.pop(conn)

    def activate(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.max_clients)
        self.clients = []
        self.client_info = {}
        self.running = True

        while self.running:
            try:
                conn, addr = self.socket.accept()
                self.clients.append(conn)
                self.client_info[conn] = {}
                _thread.start_new_thread(self.clientThread, (conn, addr))
            
            except OSError as e:
                if e.args[0] != 10038:
                    raise

                else:
                    continue

        return "END"

    def close(self):
        clients = []
        for client in self.clients:
            clients.append(client)

        for client in clients:
            self.kick(client)

        self.clients.clear()
        self.running = False
        self.socket.close()

class ServerUI(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.resizable(width=False, height=False)
        self.server = Server(self)
        self.ipLabel = tk.Label(self, text = f"IP: ")
        self.ipEntry = tk.Entry(self)
        self.portLabel = tk.Label(self, text = f"PORT: ")
        self.portEntry = tk.Entry(self)
        self.maxClientsLabel = tk.Label(self, text = "Max Clients: ")
        self.maxClientsEntry = tk.Entry(self)
        self.activateButton = tk.Button(self, text = "Activate", command=self.threadActivate)
        self.userListBox = tk.Listbox(self, height=22, width = 65)
        self.disconnetButton = tk.Button(self, text="Disconnect", command=self.disconnectSelected)
        self.activeLabel = tk.Label(self, text="OFF")

        self.ipEntry.insert(tk.END, f"{self.server.ip}")
        self.portEntry.insert(tk.END, f"{self.server.port}")
        self.maxClientsEntry.insert(tk.END, 10)

        self.disconnetButton.grid(column=0, row=100, sticky=tk.W)
        self.userListBox.grid(column=0, row=4, sticky=tk.W, columnspan = 2, rowspan=4)
        self.ipLabel.grid(column=0, row=0, sticky=tk.W)
        self.ipEntry.grid(column=1, row=0, sticky=tk.W)
        self.portLabel.grid(column=0, row=1, sticky=tk.W)
        self.portEntry.grid(column=1, row=1, sticky=tk.W)
        self.maxClientsLabel.grid(column=0, row=2, sticky=tk.W)
        self.maxClientsEntry.grid(column=1, row=2, sticky=tk.W)
        self.activateButton.grid(column=0, row=3, sticky=tk.W)
        self.activeLabel.grid(column=1, row=3, sticky=tk.W)

        self.connections = {}

        self.protocol("WM_DELETE_WINDOW", self.onClose)
        self.setName("OFF")
    
    def setName(self, sub):
        self.title(f"Server - {sub}")

    def onClose(self):
        self.server.close()
        self.destroy()

    def threadActivate(self):
        self.setName("ON")
        self.activeLabel["text"] = "ON"
        self.server.max_clients = int(self.maxClientsEntry.get())
        self.server.port = int(self.portEntry.get())
        self.server.ip = self.ipEntry.get()
        _thread.start_new_thread(self.server.activate, ())
        self.maxClientsEntry["state"] = "readonly"
        self.portEntry["state"] = "readonly"
        self.ipEntry["state"] = "readonly"

        self.activateButton["text"] = "Deactivate"
        self.activateButton["command"] = self.threadDeactivate

    def threadDeactivate(self):
        self.setName("OFF")
        self.activeLabel["text"] = "OFF"
        self.maxClientsEntry["state"] = "normal"
        self.portEntry["state"] = "normal"
        self.ipEntry["state"] = "normal"
        self.userListBox.delete(0, tk.END)
        self.server.close()

        self.activateButton["text"] = "Activate"
        self.activateButton["command"] = self.threadActivate

    def addUser(self, name, addr, conn):
        self.connections[str(addr)] = conn
        self.userListBox.insert(tk.END, f"{name}: {addr}")

    def disconnectSelected(self):
        selected = self.userListBox.get(self.userListBox.curselection())
        addr = selected.split(": ")[1]
        self.server.kick(self.connections[str(addr)])
        self.connections.pop(addr)
        self.userListBox.delete(self.userListBox.curselection())

    def disconnectKey(self, key):
        index_ = list(self.connections.keys()).index(str(key))
        self.userListBox.delete(index_)
        self.connections.pop(key)
        return

server = ServerUI()
server.geometry("500x500")
server.mainloop()