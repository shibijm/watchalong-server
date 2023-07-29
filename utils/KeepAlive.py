from models import User
import requests
import threading
import time

class KeepAlive(threading.Thread):

	def __init__(self, url: str, users: list[User]) -> None:
		super().__init__()
		self.url = url
		self.users = users
		self.daemon = True
		self.start()

	def run(self) -> None:
		while (True):
			time.sleep(600)
			if self.users:
				requests.get(self.url)
