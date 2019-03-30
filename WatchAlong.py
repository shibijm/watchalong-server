from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import os
import requests
import socket
import threading
import time
import traceback

class client:

	def __init__(self, client, address, name = "NOT_SET", playing = False, time = 0):
		self.client = client
		self.address = address
		self.name = name
		self.playing = playing
		self.time = time
		self.pingInterval = 30
		self.pingTimeoutDelay = 15
		self.disconnectReason = "Quit"
		self.pingTimer = None
		self.pingTimeoutTimer = None
		self.pingTimedOut = False

	def ping(self):
		self.send("PING")
		self.pingTimeoutTimer = threading.Timer(self.pingTimeoutDelay, self.pingTimeout)
		self.pingTimeoutTimer.start()

	def pingTimeout(self):
		self.pingTimedOut = True
		self.client.close()

	def send(self, message):
		self.client.sendall(message.encode("UTF-8")) if self.client.__class__.__name__ == "socket" else self.client.sendMessage(message)
		print("[OUT] [" + self.name + " - " + self.address + "] " + message)

	def receive(self, message):
		message = message.replace("\r\n", "")
		if (message not in [None, ""]):
			print("[IN] [" + self.name + " - " + self.address + "] " + message)
			args = message.split(":")
			if (args[0] == "PONG"):
				self.pingTimeoutTimer.cancel()
				self.pingTimer = threading.Timer(self.pingInterval, self.ping)
				self.pingTimer.start()
			elif (args[0] == "HELLO"):
				self.name = args[1]
				[client.send("Connect: " + self.name) for client in clients if client != self]
				self.send("Welcome, " + self.name + ". Users connected: " + ", ".join(client.name for client in clients))
				self.pingTimer = threading.Timer(1, self.ping)
				self.pingTimer.start()
			elif (args[0] == "USERS"):
				self.send("Users connected: " + ", ".join(client.name for client in clients))
			elif (args[0] == "REQUEST"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				lowestTime = self.time
				awaitingResponses = 0
				for client in clients:
					if (client != self):
						client.send("STATUS_REQUEST:" + self.name)
						awaitingResponses += 1
				[client.send("DONE:" + str(lowestTime)) for client in clients if awaitingResponses == 0]
			elif (args[0] == "STATUS"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				lowestTime = min(lowestTime, self.time)
				awaitingResponses -= 1
				[client.send("DONE:" + str(lowestTime)) for client in clients if awaitingResponses == 0]
			elif (args[0] == "STATUS_REQUEST_FAILED"):
				awaitingResponses = 0
				[client.send(self.name + " failed to connect to their player: " + args[1]) for client in clients if client != self]
			elif (args[0] == "QUIT"):
				self.client.close()

	def close(self):
		if (self.pingTimer):
			self.pingTimer.cancel()
		if (self.pingTimedOut):
			self.disconnectReason = "Ping Timeout"
		print("[DISCONNECT] " + self.name + " - " + self.address + " (" + self.disconnectReason + ")")
		clients.remove(self)
		[client.send("Disconnect: " + self.name + " (" + self.disconnectReason + ")") for client in clients]

class webSocketServer(WebSocket):

	port = int(os.environ.get("PORT", 22334))

	def handleMessage(self):
		try:
			for client in clients:
				if (client.client == self):
					client.receive(self.data)
					break
		except:
			print(traceback.format_exc())

	def handleConnected(self):
		try:
			address = self.address[0] + ":" + str(self.address[1])
			print("[CONNECT] " + address)
			clientInstance = client(self, address)
			clients.append(clientInstance)
		except:
			print(traceback.format_exc())

	def handleClose(self):
		try:
			for client in clients:
				if (client.client == self):
					client.close()
					break
		except:
			print(traceback.format_exc())

class socketServerClientHandler(threading.Thread):

	def __init__(self, clientSocket, clientInstance):
		super().__init__()
		self.clientSocket = clientSocket
		self.clientInstance = clientInstance

	def run(self):
		try:
			while (True):
				message = self.clientSocket.recv(1024).decode("UTF-8")
				self.clientInstance.receive(message)
		except ConnectionAbortedError as e:
			self.clientInstance.disconnectReason = "Connection Aborted"
		except (ConnectionResetError, OSError):
			pass
		except Exception as e:
			print(traceback.format_exc())
		finally:
			self.clientInstance.close()

class socketServer(threading.Thread):

	def __init__(self):
		super().__init__()
		self.port = int(os.environ.get("PORT", 22333))

	def run(self):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(("", self.port))
		self.server.listen(5)
		print("Server Running on Port " + str(self.port))
		while (True):
			clientSocket, address = self.server.accept()
			address = address[0] + ":" + str(address[1])
			print("[CONNECT] " + address)
			clientInstance = client(clientSocket, address)
			clients.append(clientInstance)
			socketServerClientHandlerInstance = socketServerClientHandler(clientSocket, clientInstance)
			socketServerClientHandlerInstance.start()
		self.server.close()

class keepAlive(threading.Thread):

	def __init__(self):
		super().__init__()

	def run(self):
		while (True):
			if (len(clients) > 0):
				requests.get("https://watchalong-s.herokuapp.com")
				time.sleep(900)
			else:
				time.sleep(60)

clients = []
lowestTime = 0
awaitingResponses = 0

if ("PORT" in os.environ):
	keepAliveThread = keepAlive()
	keepAliveThread.daemon = True
	keepAliveThread.start()
else:
	server = socketServer()
	server.start()
server = SimpleWebSocketServer("", webSocketServer.port, webSocketServer)
print("Websocket Server Running on Port " + str(webSocketServer.port))
server.serveforever()
