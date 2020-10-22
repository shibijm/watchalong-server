import threading

lowestTime = 0
awaitingResponses = 0

class Client:

	clients = []

	def __init__(self, client, address, name = "NOT_SET", playing = False, time = 0):
		self.Client = client
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
		self.Client.close()

	def send(self, message):
		self.Client.sendall(message.encode("UTF-8")) if self.Client.__class__.__name__ == "socket" else self.Client.sendMessage(message)
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
				[client.send("Connect: " + self.name) for client in self.clients if client != self]
				self.send("Welcome, " + self.name + ". Users connected: " + ", ".join(client.name for client in self.clients))
				self.pingTimer = threading.Timer(1, self.ping)
				self.pingTimer.start()
			elif (args[0] == "USERS"):
				self.send("Users connected: " + ", ".join(client.name for client in self.clients))
			elif (args[0] == "REQUEST"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				lowestTime = self.time
				awaitingResponses = 0
				for client in self.clients:
					if (client != self):
						client.send("STATUS_REQUEST:" + self.name)
						awaitingResponses += 1
				[client.send("DONE:" + str(lowestTime)) for client in self.clients if awaitingResponses == 0]
			elif (args[0] == "STATUS"):
				self.playing = True if args[1] == "playing" else False
				self.time = int(args[2])
				lowestTime = min(lowestTime, self.time)
				awaitingResponses -= 1
				[client.send("DONE:" + str(lowestTime)) for client in self.clients if awaitingResponses == 0]
			elif (args[0] == "STATUS_REQUEST_FAILED"):
				awaitingResponses = 0
				[client.send(self.name + " failed to connect to their player: " + args[1]) for client in self.clients if client != self]
			elif (args[0] == "QUIT"):
				self.Client.close()

	def close(self):
		if (self.pingTimer):
			self.pingTimer.cancel()
		if (self.pingTimedOut):
			self.disconnectReason = "Ping Timeout"
		print("[DISCONNECT] " + self.name + " - " + self.address + " (" + self.disconnectReason + ")")
		self.clients.remove(self)
		[client.send("Disconnect: " + self.name + " (" + self.disconnectReason + ")") for client in self.clients]