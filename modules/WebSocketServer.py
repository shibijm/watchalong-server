from helpers.logging import logger
from helpers.stores import users
from models import User
from typing import Any, Optional
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.protocol import broadcast
from websockets.server import serve, WebSocketServerProtocol
import asyncio
import json
import traceback

class WebSocketServer():

	def __init__(self, port: int) -> None:
		self.port = port
		self.lowestTime = 0
		self.pendingResponses = 0
		self.pendingAction = ""
		asyncio.run(self.start())

	async def start(self) -> None:
		server = await serve(self.connectionHandler, None, self.port, ping_interval = None, ping_timeout = None)
		await server.wait_closed()

	def broadcast(self, data: dict[str, Any], excludedUser: Optional[User] = None) -> None:
		dataEncoded = json.dumps(data, separators = (",", ":"))
		logger.info("[BROADCAST] %s", dataEncoded)
		broadcast([user.websocket for user in users if user != excludedUser], dataEncoded)

	def broadcastMessage(self, message: str, excludedUser: Optional[User] = None) -> None:
		self.broadcast({ "event": "MESSAGE", "payload": message }, excludedUser)

	async def connectionHandler(self, websocket: WebSocketServerProtocol, _path: str) -> None:
		if "X-Forwarded-For" in websocket.request_headers:
			address = websocket.request_headers["X-Forwarded-For"]
		else:
			address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
		logger.info("[CONNECT] %s", address)
		user: Optional[User] = None
		try:
			async for dataEncoded in websocket:
				if not isinstance(dataEncoded, str):
					continue
				try:
					data: dict[str, Any] = json.loads(dataEncoded)
				except:
					logger.error("Malformed JSON received from %s", address)
					continue
				if not user:
					if data["event"] == "HANDSHAKE":
						user = User(websocket, address, data["payload"]["name"])
						users.append(user)
						logger.info("[HANDSHAKE] %s - %s", user.name, user.address)
						await user.sendMessage(f"Welcome, {user.name}. Users connected: {', '.join(user.name for user in users)}")
						self.broadcastMessage(f"{user.name} has joined", user)
					continue
				logger.info("[IN] [%s - %s] %s", user.name, user.address, dataEncoded)
				match data["event"]:
					case "PONG":
						user.handlePong()
					case "USERS":
						await user.sendMessage(f"Users connected: {', '.join(user.name for user in users)}")
					case "PLAY_PAUSE_REQUEST":
						action = data["payload"]["action"]
						self.lowestTime = data["payload"]["time"]
						totalOtherUsers = len(users) - 1
						if totalOtherUsers == 0:
							self.broadcast({ "event": "PLAY_PAUSE", "payload": { "action": action, "at": self.lowestTime }})
						else:
							self.broadcast({ "event": "STATUS_REQUEST", "payload": { "action": action, "requestingUser": { "name": user.name } }}, user)
							self.pendingResponses += totalOtherUsers
							self.pendingAction = action
					case "STATUS_UPDATE":
						if "error" in data["payload"]:
							self.pendingResponses = 0
							self.pendingAction = ""
							self.broadcastMessage(f"{user.name} failed to connect to their media player. Reason: {data['payload']['error']['message']}", user)
							continue
						self.lowestTime = min(self.lowestTime, data["payload"]["time"])
						self.pendingResponses -= 1
						if self.pendingResponses == 0:
							self.broadcast({ "event": "PLAY_PAUSE", "payload": { "action": self.pendingAction, "at": self.lowestTime }})
							self.pendingAction = ""
					case "QUIT":
						user.disconnectReason = "Quit"
						await websocket.close()
		except ConnectionClosedError:
			pass
		except:
			traceback.print_exc()
		if user:
			logger.info("[DISCONNECT] %s - %s (%s)", user.name, user.address, user.disconnectReason)
			users.remove(user)
			self.broadcastMessage(f"{user.name} has left ({user.disconnectReason})")
		else:
			logger.info("[DISCONNECT] %s", address)
