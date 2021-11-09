from models import Client
import requests
import threading
import time

class KeepAlive(threading.Thread):

	clients: list[Client] = []

	def __init__(self) -> None:
		super().__init__()

	def run(self) -> None:
		while (True):
			if (len(self.clients) > 0):
				requests.get("https://watchalong-s.herokuapp.com")
				time.sleep(900)
			else:
				time.sleep(60)
