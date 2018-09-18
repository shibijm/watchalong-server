from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
import os
import socket
import threading
import time
import traceback

clients = []

class client(threading.Thread):

	def __init__(self, client, name, playing, time):
		super().__init__()
		self.client = client
		self.address = self.client.address[0] + ":" + str(self.client.address[1])
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
		self.client.sendMessage(message.encode("UTF-8"))
		print("[OUT] [" + self.name + " - " + self.address + "] " + message)

	def handleMessage(self, message):
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
				users = self.name
				for client in clients:
					if (client != self):
						users += ", " + client.name
						client.send("Connect: " + self.name)
				self.send("Welcome, " + self.name + ". Users connected: " + users)
				self.pingTimer = threading.Timer(1, self.ping)
				self.pingTimer.start()
			elif (args[0] == "USERS"):
				users = self.name
				for client in clients:
					if (client != self):
						users += ", " + client.name
				self.send("Users connected: " + users)
			elif (args[0] == "REQUEST"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				lowestTime = self.time
				awaitingResponses = 0
				for client in clients:
					if (client != self):
						client.send("STATUS_REQUEST:" + self.name)
						awaitingResponses += 1
			elif (args[0] == "STATUS"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				if (self.time < lowestTime):
					lowestTime = self.time
				awaitingResponses -= 1
				if (awaitingResponses == 0):
					for client in clients:
						client.send("DONE:" + str(lowestTime))
			elif (args[0] == "STATUS_REQUEST_FAILED"):
				awaitingResponses = 0
				for client in clients:
					if (client != self):
						client.send(self.name + " failed to connect to their player: " + args[1])

	def handleClose(self):
		if (self.pingTimer):
			self.pingTimer.cancel()
		if (self.pingTimedOut):
			self.disconnectReason = "Ping Timeout"
		print("[DISCONNECT] " + self.name + " - " + self.address + " (" + self.disconnectReason + ")")
		clients.remove(self)
		for client in clients:
			client.send("Disconnect: " + self.name + " (" + self.disconnectReason + ")")

class webSocketServer(WebSocket):

	def handleMessage(self):
		try:
			for client in clients:
				if (client.client == self):
					client.handleMessage(self.data)
		except:
			print(traceback.format_exc())

	def handleConnected(self):
		try:
			print("[CONNECT] " + self.address[0] + ":" + str(self.address[1]))
			clientInstance = client(self, "NOT_SET", False, 0)
			clients.append(clientInstance)
		except:
			print(traceback.format_exc())

	def handleClose(self):
		try:
			for client in clients:
				if (client.client == self):
					client.handleClose()
		except:
			print(traceback.format_exc())

port = int(os.environ.get("PORT", 22333))
server = SimpleWebSocketServer("", port, webSocketServer)
print("Bound on port " + str(port))
server.serveforever()