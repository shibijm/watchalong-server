import requests
import threading
import time

class KeepAlive(threading.Thread):

	clients = []

	def __init__(self):
		super().__init__()

	def run(self):
		while (True):
			if (len(self.clients) > 0):
				requests.get("https://watchalong-s.herokuapp.com")
				time.sleep(900)
			else:
				time.sleep(60)
