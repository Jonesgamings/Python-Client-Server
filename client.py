import socket
import tkinter as tk
import _thread
import json

#BACKGROUND CODE

class System:
    def __init__(self) -> None:
        self.filename_accounts = "accounts.json"
        self.filename_servers = "servers.json"
        self.accounts = {}
        self.savedServers = {}

    def init(self):
        with open(self.filename_accounts, "w") as f:
            json.dump({}, f)

        with open(self.filename_servers, "w") as f:
            json.dump({}, f)

    def load(self):
        try:
            with open(self.filename_accounts, "r") as file:
                accountData = json.load(file)
                for key, value in accountData.items():
                    self.accounts[value["USERNAME"]] = value

            with open(self.filename_servers, "r") as file:
                serversData = json.load(file)
                for key, value in serversData.items():
                    self.savedServers[value["NAME"]] = value
        except:
            self.init()

    def save(self):
        with open(self.filename_accounts, "w") as file:
            json.dump(self.accounts, file, indent = 4)

        with open(self.filename_servers, "w") as file:
            json.dump(self.savedServers, file, indent = 4)

    def addServer(self, serverJSON):
        if serverJSON["NAME"] in self.savedServers.keys():
            return f"'{serverJSON['NAME']}' already in use"

        else:
            self.savedServers[serverJSON["NAME"]] = serverJSON
            return True

    def getServers(self):
        return self.savedServers

    def getServer(self, name):
        return self.savedServers[name]

    def removeServer(self, name):
        if name in self.savedServers.keys():
            del self.savedServers[name]
            return True

        else:
            return f"'{name}' is not a saved server"

    def deleteAccount(self, user):
        if user in self.accounts.keys():
            del self.accounts[user]
            return True

        else:
            return f"'{user}' does not exist"

    def check(self, username, password):
        if username in self.accounts.keys():
            if self.accounts[username]["PASSWORD"] == password:
                return True

            else:
                return "Password is incorrect"

        else:
            return f"No account exists under username of '{username}'"

    def createAccount(self, username, password):
        if username in self.accounts.keys():
            return f"'{username}' already taken"

        else:
            self.accounts[username] = {"USERNAME": username, "PASSWORD": password, "ACCESS": 0}
            return f"Account '{username}' created"

class Client:

    def __init__(self, ui) -> None:
        self.ui = ui 
        self.name = ""
        self.authCode = None
        self.access = ""
        self.connected = False
        self.connectedTo = None
        self.running = False
        self.messages = []
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def setInfo(self, name, access):
        self.name = name
        self.access = access

    def join(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((ip, port))
            self.connected = True
            self.connectedTo = ip
            return True

        except (ConnectionRefusedError, TimeoutError):
            return f"Failed to connect to {ip}: {port}"

    def disconnect(self):
        self.ui.loadSavedServersMenu()
        self.send(f"DISCONNECT-{self.authCode}")

        self.running = False
        self.socket.close()

        self.connected = False
        self.connectedTo = None

    def forceDisconnect(self):
        self.ui.loadSavedServersMenu()
        self.running = False
        self.socket.close()

        self.connected = False
        self.connectedTo = None

    def send(self, message):
        if self.connected:
            self.socket.send(message.encode())

    def activate(self):
        self.running = True
        while self.running:
            try:
                message = self.socket.recv(2048).decode()
                if message:
                    if "-" in message:
                        split_message = message.split("-")
                        if split_message[0] == "AUTH":
                            self.authCode = split_message[1]
                            dataToSend = {"NAME": self.name, "ACCESS": self.access}
                            toSend = f"{self.authCode}-{dataToSend}"
                            self.send(toSend)

                        if split_message[0] == "DISCONNECT":
                            if split_message[1] == self.authCode:
                                self.forceDisconnect()

                    else:
                        self.messages.append(message)
                        self.ui.onMessage(message)

                else:
                    self.disconnect()

            except Exception as e:
                if type(e).__name__ == "ConnectionResetError":
                    self.forceDisconnect()

        return "END"

#UI CODE

class MainMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.createAccountLabel = tk.Label(self, text= "Create Account")
        self.loginAccountLabel = tk.Label(self, text= "Login Account")

        self.createAccountButton = tk.Button(self, text = "Create", command=self.container.loadCreateAccountMenu)
        self.loginAccountButton = tk.Button(self, text="Login", command=self.container.loadLoginAccountMenu)

        self.createAccountLabel.grid(column=0, row=0)
        self.loginAccountLabel.grid(column=1, row=0)
        self.createAccountButton.grid(column=0, row=1)
        self.loginAccountButton.grid(column=1, row=1)

class ServerMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.disconnectButton = tk.Button(self, text = "Disconnect", command=self.container.disconnect)
        self.messageBox = tk.Listbox(self, height=26, width = 70)
        self.messageEntry = tk.Entry(self)
        self.enterButton = tk.Button(self, text = "Enter", command=self.container.send)
        
        self.disconnectButton.grid(column=0, row = 101, sticky=tk.W)
        self.enterButton.grid(column= 5, row =100, sticky=tk.W)
        self.messageEntry.grid(column = 0, row=100, sticky="we", columnspan=5)
        self.messageBox.grid(column=0, row=0, sticky=tk.W, columnspan=5)

    def addMessage(self, message):
        self.messageBox.insert(tk.END, message)

    def load(self):
        self.messageBox.delete(0, tk.END)
        self.messageEntry.delete(0, tk.END)

class SavedServersMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.backButton = tk.Button(self, text="Logout", command=self.container.loadMainMenu)
        self.backButton.grid(column=0, row=100)

        self.savedServerBox = tk.Listbox(self, height=22, width=45)
        self.directConnectButton = tk.Button(self, text = "Direct Connect", command=self.container.loadDirectConnectMenu)

        self.serverNameLabel = tk.Label(self, text = "Server Name")
        self.serverIpLabel = tk.Label(self, text = "Server Ip")
        self.serverPortLabel = tk.Label(self, text = "Server Port")
        self.serverNameEntry = tk.Entry(self)
        self.serverIpEntry = tk.Entry(self)
        self.serverPortEntry = tk.Entry(self)
        self.addButton = tk.Button(self, text = "Add Server", command = self.addServer)
        self.removeButton = tk.Button(self, text = "Remove Server", command = self.removeServer)
        self.connectButtom = tk.Button(self, text = "Connect", command = self.connect)
        self.infoBox = tk.Label(self, text = "")

        self.serverNameLabel.grid(column=4, row=0)
        self.serverIpLabel.grid(column=4, row=1)
        self.serverPortLabel.grid(column=4, row=2)

        self.serverNameEntry.grid(column=5, row=0)
        self.serverIpEntry.grid(column=5, row=1)
        self.serverPortEntry.grid(column=5, row=2)

        self.addButton.grid(column=5, row=3)

        self.savedServerBox.grid(column=0, row=0, rowspan=100, columnspan=3)
        self.directConnectButton.grid(column=4, row=5)
        self.infoBox.grid(column=4, row=6)
        self.removeButton.grid(column=1, row=100)
        self.connectButtom.grid(column=2, row=100)

    def connect(self):
        selection = self.savedServerBox.curselection()
        name = self.savedServerBox.get(selection).split(":")[0]
        server = self.container.system.getServer(name)
        ip = server["IP"]
        port = int(server["PORT"])
        connErr = self.container.join(ip, port)
        if connErr != True:
            self.infoBox["text"] = connErr

    def removeServer(self):
        selection = self.savedServerBox.curselection()
        name = self.savedServerBox.get(selection).split(":")[0]
        removeErr = self.container.system.removeServer(name) 
        if removeErr == True:
            self.savedServerBox.delete(selection)

        else:
            self.infoBox["text"] = removeErr

    def addServer(self):
        name= self.serverNameEntry.get()
        ip = self.serverIpEntry.get()
        port = self.serverPortEntry.get()
        toJSON = {"NAME": name, "IP": ip, "PORT": port}
        toSTRING = f"{name}: {ip}:{port}"
        addErr = self.container.system.addServer(toJSON)
        if addErr == True:
            self.savedServerBox.insert(tk.END, toSTRING)
        
        else:
            self.infoBox["text"] = addErr

    def load(self):
        self.savedServerBox.delete(0, tk.END)
        servers = self.container.system.getServers()
        for key, value in servers.items():
            ip = value["IP"]
            port = value["PORT"]
            toSTRING = f"{key}: {ip}:{port}"
            self.savedServerBox.insert(tk.END, toSTRING)

class DirectConnectMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.serverIpLabel = tk.Label(self, text = "Server Ip")
        self.serverPortLabel = tk.Label(self, text = "Server Port")
        self.serverIpEntry = tk.Entry(self)
        self.serverPortEntry = tk.Entry(self)
        self.connectButton = tk.Button(self, text = "Connect", command= self.connect)
        self.infoBox = tk.Label(self, text = "")

        self.serverIpLabel.grid(column= 0, row = 0)
        self.serverPortLabel.grid(column=0, row=1)
        self.serverIpEntry.grid(column=1, row=0)
        self.serverPortEntry.grid(column=1, row=1)
        self.connectButton.grid(column=0, row=2)
        self.infoBox.grid(column=0, row=3)

        self.backButton = tk.Button(self, text="Back", command=self.container.loadSavedServersMenu)
        self.backButton.grid(column=0, row=100)

    def connect(self):
        ip = self.serverIpEntry.get()
        port = int(self.serverPortEntry.get())
        connErr = self.container.join(ip, port)
        if connErr != True:
            self.infoBox["text"] = connErr

class CreateAccountMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.backButton = tk.Button(self, text="Back", command=self.container.loadMainMenu)
        self.backButton.grid(column=0, row=100)

        self.usernameLabel = tk.Label(self, text = "Username")
        self.passwordLabel = tk.Label(self, text = "Password")

        self.usernameEntry = tk.Entry(self)
        self.passwordEntry = tk.Entry(self)

        self.createButton = tk.Button(self, text = "Create", command= self.createAccount)

        self.infoBox = tk.Label(self, text= "")

        self.usernameLabel.grid(column=0, row=0)
        self.passwordLabel.grid(column=1, row=0)
        self.usernameEntry.grid(column=0, row=1)
        self.passwordEntry.grid(column=1, row=1)
        self.createButton.grid(column=0, row=2)
        self.infoBox.grid(column=0, row=5)

    def createAccount(self):
        user = self.usernameEntry.get()
        pasw = self.passwordEntry.get()
        self.infoBox["text"] = self.container.system.createAccount(user, pasw)

    def load(self):
        self.usernameEntry.delete(0, tk.END)
        self.passwordEntry.delete(0, tk.END)
        self.infoBox["text"] = ""

class LoginAccountMenu(tk.Frame):
    def __init__(self, container):
        super().__init__(container)
        self.container = container

        self.backButton = tk.Button(self, text="Back", command=self.container.loadMainMenu)
        self.backButton.grid(column=0, row=100)

        self.usernameLabel = tk.Label(self, text = "Username")
        self.passwordLabel = tk.Label(self, text = "Password")

        self.usernameEntry = tk.Entry(self)
        self.passwordEntry = tk.Entry(self)

        self.loginButton = tk.Button(self, text = "Login", command= self.loginAccount)
        self.deleteButton = tk.Button(self, text = "Delete Account", command= self.deleteAccount)

        self.infoBox = tk.Label(self, text= "")

        self.usernameLabel.grid(column=0, row=0)
        self.passwordLabel.grid(column=1, row=0)
        self.usernameEntry.grid(column=0, row=1)
        self.passwordEntry.grid(column=1, row=1)
        self.loginButton.grid(column=0, row=2)
        self.deleteButton.grid(column=1, row=2)
        self.infoBox.grid(column=0, row=5)

    def deleteAccount(self):
        user = self.usernameEntry.get()
        pasw = self.passwordEntry.get()
        output = self.container.system.check(user, pasw)
        if output == True:
            self.container.system.deleteAccount(user)
            self.infoBox["text"] = f"'{user}' deleted"

        else:
            self.infoBox["text"] = output

    def loginAccount(self):
        user = self.usernameEntry.get()
        pasw = self.passwordEntry.get()
        output = self.container.system.check(user, pasw)
        if output == True:
            self.container.setClientInfo(user, pasw)
            self.container.loadSavedServersMenu()

        else:
            self.infoBox["text"] = output

class ClientUI(tk.Tk):

    def __init__(self) -> None:
        super().__init__()
        self.resizable(width=False, height=False)
        self.client = Client(self)
        self.savedServers = {}
        self.system = System()

        self.MainMenu = MainMenu(self)
        self.ServerMenu = ServerMenu(self)
        self.SavedServersMenu = SavedServersMenu(self)
        self.DirectConnectMenu = DirectConnectMenu(self)
        self.CreateAccountMenu = CreateAccountMenu(self)
        self.LoginAccountMenu = LoginAccountMenu(self)

        self.MainMenu.pack(fill=tk.BOTH, expand=True)
        self.ServerMenu.pack(fill=tk.BOTH, expand=True)
        
        self.bind("<Return>", lambda event:self.send())
        self.protocol("WM_DELETE_WINDOW", self.onClose)
        self.loadMainMenu()

        self.system.load()


    def onClose(self):
        try:
            self.client.disconnect()

        except AttributeError:
            pass
        
        self.system.save()
        self.destroy()

    def disconnect(self):
        self.client.disconnect()
        self.loadSavedServersMenu()

    def forceDisconnect(self):
        self.client.forceDisconnect()
        self.loadSavedServersMenu()

    def send(self):
        message = self.ServerMenu.messageEntry.get()
        self.ServerMenu.messageEntry.delete(0, tk.END)
        self.client.send(message)

    def setName(self, sub):
        self.title(f"Client - {sub}")

    def unload(self):
        self.MainMenu.pack_forget()
        self.ServerMenu.pack_forget()
        self.LoginAccountMenu.pack_forget()
        self.SavedServersMenu.pack_forget()
        self.DirectConnectMenu.pack_forget()
        self.CreateAccountMenu.pack_forget()

    def loadMainMenu(self):
        self.unload()
        self.MainMenu.pack(fill=tk.BOTH, expand=True)
        self.setName("Main Menu")

    def loadServerMenu(self):
        self.unload()
        self.ServerMenu.pack(fill=tk.BOTH, expand=True)
        self.ServerMenu.load()
        self.setName(f"Server '{self.client.connectedTo}'")

    def loadLoginAccountMenu(self):
        self.unload()
        self.LoginAccountMenu.pack(fill=tk.BOTH, expand=True)
        self.setName("Login Menu")

    def loadDirectConnectMenu(self):
        self.unload()
        self.DirectConnectMenu.pack(fill=tk.BOTH, expand=True)
        self.setName("Direct Connect")

    def loadSavedServersMenu(self):
        self.unload()
        self.SavedServersMenu.pack(fill=tk.BOTH, expand=True)
        self.setName("Server Browser")
        self.SavedServersMenu.load()

    def loadCreateAccountMenu(self):
        self.unload()
        self.CreateAccountMenu.pack(fill=tk.BOTH, expand=True)
        self.CreateAccountMenu.load()
        self.setName("Account Creation")

    def onMessage(self, message):
        self.ServerMenu.messageBox.insert(tk.END, message)

    def setClientInfo(self, name, access):
        self.client.setInfo(name, access)

    def join(self, ip, port):
        connErr = self.client.join(ip, port)
        if connErr == True:

            self.loadServerMenu()
            _thread.start_new_thread(self.client.activate, ())
            return True

        else:
            return connErr

c = ClientUI()
c.geometry("500x500")
c.mainloop()