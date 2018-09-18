import os
import socket
import threading
import time
import traceback

class client(threading.Thread):

	def __init__(self, server, socket, address, name, playing, time):
		super().__init__()
		self.server = server
		self.socket = socket
		self.address = address
		self.name = name
		self.playing = playing
		self.time = time
		self.pingInterval = 60
		self.pingTimeoutDelay = 15
		self.disconnectReason = "Quit"
		self.pingTimer = None
		self.pingTimeoutTimer = None
		self.pingTimedOut = False

	def ping(self):
		self.write("PING")
		self.pingTimeoutTimer = threading.Timer(self.pingTimeoutDelay, self.pingTimeout)
		self.pingTimeoutTimer.start()

	def pingTimeout(self):
		self.socket.close()
		self.pingTimedOut = True

	def write(self, message):
		self.socket.sendall(message.encode("UTF-8"))
		print("[OUT] [" + self.name + " - " + self.address + "] " + message)

	def run(self):
		try:
			while (True):
				message = self.socket.recv(1024).decode("UTF-8")
				message = message.replace("\r\n", "")
				if (message in [None, ""]):
					break
				else:
					print("[IN] [" + self.name + " - " + self.address + "] " + message)
					args = message.split(":")
					if (args[0] == "PONG"):
						self.pingTimeoutTimer.cancel()
						self.pingTimer = threading.Timer(self.pingInterval, self.ping)
						self.pingTimer.start()
					elif (args[0] == "HELLO"):
						self.name = args[1]
						users = self.name
						for client in self.server.clients:
							if (client != self):
								users += ", " + client.name
								client.write("Connect: " + self.name)
						self.write("Welcome, " + self.name + ". Users connected: " + users)
						self.pingTimer = threading.Timer(1, self.ping)
						self.pingTimer.start()
					elif (args[0] == "USERS"):
						users = self.name
						for client in self.server.clients:
							if (client != self):
								users += ", " + client.name
						self.write("Users connected: " + users)
					elif (args[0] == "REQUEST"):
						self.playing = True if args[1] == "playing" else False
						self.time = int(args[2])
						self.server.lowestTime = self.time
						self.server.awaitingResponses = 0
						for client in self.server.clients:
							if (client != self):
								client.write("STATUS_REQUEST:" + self.name)
								self.server.awaitingResponses += 1
					elif (args[0] == "STATUS"):
						self.playing = True if args[1] == "playing" else False
						self.time = int(args[2])
						if (self.time < self.server.lowestTime):
							self.server.lowestTime = self.time
						self.server.awaitingResponses -= 1
						if (self.server.awaitingResponses == 0):
							for client in self.server.clients:
								client.write("DONE:" + str(self.server.lowestTime))
					elif (args[0] == "STATUS_REQUEST_FAILED"):
						self.server.awaitingResponses = 0
						for client in self.server.clients:
							if (client != self):
								client.write(self.name + " failed to connect to their player: " + args[1])
		except ConnectionAbortedError as e:
			self.disconnectReason = "Connection Aborted"
		except ConnectionResetError:
			pass
		except Exception as e:
			print(traceback.format_exc())
		finally:
			if (self.pingTimer):
				self.pingTimer.cancel()
			if (self.pingTimedOut):
				self.disconnectReason = "Ping Timeout"
			print("[DISCONNECT] " + self.name + " - " + self.address + " (" + self.disconnectReason + ")")
			self.server.clients.remove(self)
			for client in self.server.clients:
				client.write("Disconnect: " + self.name + " (" + self.disconnectReason + ")")

class server:

	def __init__(self):
		self.clients = []
		self.awaitingResponses = 0
		self.lowestTime = 0
		self.port = 22333

	def start(self):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(("0.0.0.0", self.port))
		self.server.listen(5)
		print("Bound on port " + str(self.port))
		while (True):
			clientSocket, address = self.server.accept()
			address = address[0] + ":" + str(address[1])
			print("[CONNECT] " + address)
			clientInstance = client(self, clientSocket, address, "NOT_SET", False, 0)
			self.clients.append(clientInstance)
			clientInstance.start()
		self.server.close()

os.system("cls")
serverInstance = server()
serverInstance.start()