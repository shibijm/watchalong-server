from ..models import Client
from SimpleWebSocketServer import WebSocket
import os
import traceback

class WebSocketServer(WebSocket):

	clients = []
	port = int(os.environ.get("PORT", 22334))

	def handleMessage(self):
		try:
			for client in self.clients:
				if (client.client == self):
					client.receive(self.data)
					break
		except:
			print(traceback.format_exc())

	def handleConnected(self):
		try:
			address = self.address[0] + ":" + str(self.address[1])
			print("[CONNECT] " + address)
			client = Client(self, address)
			self.clients.append(client)
		except:
			print(traceback.format_exc())

	def handleClose(self):
		try:
			for client in self.clients:
				if (client.client == self):
					client.close()
					break
		except:
			print(traceback.format_exc())