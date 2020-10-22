from ..models import Client
import os
import socket
import threading
import traceback

class SocketServerClientHandler(threading.Thread):

	def __init__(self, clientSocket, client):
		super().__init__()
		self.clientSocket = clientSocket
		self.client = client

	def run(self):
		try:
			while (True):
				message = self.clientSocket.recv(1024).decode("UTF-8")
				self.client.receive(message)
		except ConnectionAbortedError as e:
			self.client.disconnectReason = "Connection Aborted"
		except (ConnectionResetError, OSError):
			pass
		except Exception as e:
			print(traceback.format_exc())
		finally:
			self.client.close()

class SocketServer(threading.Thread):

	clients = []
	port = int(os.environ.get("PORT", 22333))

	def __init__(self):
		super().__init__()

	def run(self):
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(("", self.port))
		self.server.listen(5)
		print("Server Running on Port " + str(self.port))
		while (True):
			clientSocket, address = self.server.accept()
			address = address[0] + ":" + str(address[1])
			print("[CONNECT] " + address)
			client = Client(clientSocket, address)
			self.clients.append(client)
			socketServerClientHandler = SocketServerClientHandler(clientSocket, client)
			socketServerClientHandler.start()
		self.server.close()