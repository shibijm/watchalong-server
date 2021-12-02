from .WebSocketServer import WebSocketServer
import requests
import threading
import time

class KeepAlive(threading.Thread):

	def __init__(self) -> None:
		super().__init__()
		self.daemon = True
		self.start()

	def run(self) -> None:
		while (True):
			time.sleep(900)
			if (len(WebSocketServer.users) > 0):
				requests.get("https://watchalong-s.herokuapp.com")
