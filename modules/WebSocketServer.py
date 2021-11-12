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

	def broadcast(self, room: str, data: dict[str, Any], excludedUser: Optional[User] = None) -> None:
		dataEncoded = json.dumps(data, separators = (",", ":"))
		logger.info("[BROADCAST] [%s] %s", room, dataEncoded)
		broadcast([user.websocket for user in users if user != excludedUser and (user.room == room or not room)], dataEncoded)

	def broadcastMessage(self, room: str, message: str, excludedUser: Optional[User] = None) -> None:
		self.broadcast(room, { "event": "MESSAGE", "payload": message }, excludedUser)

	async def connectionHandler(self, websocket: WebSocketServerProtocol, _path: str) -> None:
		if "X-Forwarded-For" in websocket.request_headers:
			address = websocket.request_headers["X-Forwarded-For"]
		else:
			address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
		logger.info("[CONNECT] [%s]", address)
		user: Optional[User] = None
		try:
			async for dataEncoded in websocket:
				if not isinstance(dataEncoded, str):
					logger.error("Invalid data received from %s", address)
					continue
				try:
					data: dict[str, Any] = json.loads(dataEncoded)
				except:
					logger.error("Malformed JSON received from %s", address)
					continue
				if "event" not in data or "payload" not in data:
					logger.error("Incomplete data received from %s", address)
					continue
				event = data["event"]
				payload = data["payload"]
				if not user:
					logger.info("[IN] [%s] %s", address, dataEncoded)
					if event == "HANDSHAKE":
						if "name" not in payload or "room" not in payload:
							logger.error("Incomplete data received from %s", address)
							continue
						name = payload["name"].strip()
						room = payload["room"].strip()
						if not name or not room:
							logger.error("Incomplete data received from %s", address)
							continue
						user = User(websocket, address, name, room)
						users.append(user)
						self.broadcast(user.room, { "event": "USER_JOINED", "payload": { "name": user.name } }, user)
						await user.send({ "event": "HANDSHAKE", "payload": None })
					continue
				logger.info("[IN] [%s] [%s - %s] %s", user.room, user.name, user.address, dataEncoded)
				match event:
					case "PONG":
						user.handlePong()
					case "USERS":
						await user.send({ "event": "USERS", "payload": [{ "name": user.name } for user in users]})
					case "CONTROL_MEDIA":
						if self.pendingAction:
							continue # TODO: Send error message
						action = payload["action"]
						self.lowestTime = payload["time"]
						totalOtherUsers = len(users) - 1
						if totalOtherUsers == 0:
							self.broadcast(user.room, { "event": "CONTROL_MEDIA", "payload": { "action": action, "at": self.lowestTime }})
						else:
							self.broadcast(user.room, { "event": "MEDIA_STATUS", "payload": { "action": action, "requestingUser": { "name": user.name } }}, user)
							self.pendingResponses += totalOtherUsers # TODO: Track user-wise
							self.pendingAction = action
					case "MEDIA_STATUS":
						if not self.pendingAction:
							continue # TODO: Send error message
						self.pendingResponses -= 1
						if "error" in payload:
							self.broadcastMessage(user.room, f"{user.name} failed to connect to their media player. Reason: {data['payload']['error']['message']}", user)
							continue
						self.lowestTime = min(self.lowestTime, payload["time"])
						if self.pendingResponses == 0:
							self.broadcast(user.room, { "event": "CONTROL_MEDIA", "payload": { "action": self.pendingAction, "at": self.lowestTime }})
							self.pendingAction = ""
					case "QUIT":
						await user.disconnect("Quit")
		except ConnectionClosedError:
			pass
		except:
			traceback.print_exc()
		if user:
			user.cancelTimers()
			users.remove(user)
			logger.info("[DISCONNECT] [%s] [%s - %s] %s", user.room, user.name, user.address, user.disconnectReason)
			self.broadcast(user.room, { "event": "USER_LEFT", "payload": { "name": user.name, "reason": user.disconnectReason } })
		else:
			logger.info("[DISCONNECT] [%s]", address)
