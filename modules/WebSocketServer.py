import functools
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
		self.lowestPosition = 0
		self.pendingResponses = 0
		self.pendingAction = ""
		asyncio.run(self.start())

	async def start(self) -> None:
		server = await serve(self.connectionHandler, None, self.port, ping_interval = None, ping_timeout = None)
		await server.wait_closed()

	def broadcast(self, room: str, envelope: dict[str, Any], excludedUser: Optional[User] = None) -> None:
		envelopeEncoded = json.dumps(envelope, separators = (",", ":"))
		logger.info("[BROADCAST] [%s] %s", room, envelopeEncoded)
		broadcast([user.websocket for user in users if user != excludedUser and (user.room == room or not room)], envelopeEncoded)

	def broadcastMessage(self, room: str, message: str, excludedUser: Optional[User] = None) -> None:
		self.broadcast(room, { "type": "MESSAGE", "data": message }, excludedUser)

	async def closeAbnormally(self, errorMessage: str, websocket: WebSocketServerProtocol, address: str):
		logger.info("[OUT] [%s] Abnormal Close: %s", address, errorMessage)
		await websocket.close(1002, errorMessage)

	async def connectionHandler(self, websocket: WebSocketServerProtocol, _path: str) -> None:
		if "X-Forwarded-For" in websocket.request_headers:
			address = websocket.request_headers["X-Forwarded-For"]
		else:
			address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
		closeAbnormally = functools.partial(self.closeAbnormally, websocket = websocket, address = address)
		logger.info("[CONNECT] [%s]", address)
		user: Optional[User] = None
		try:
			async for envelopeEncoded in websocket:
				if not isinstance(envelopeEncoded, str):
					await closeAbnormally("Invalid envelope received.")
					continue
				try:
					envelope: dict[str, Any] = json.loads(envelopeEncoded)
				except:
					await closeAbnormally("Malformed JSON received.")
					continue
				if "type" not in envelope or "data" not in envelope:
					await closeAbnormally("Incomplete envelope received.")
					continue
				data = envelope["data"]
				if not user:
					logger.info("[IN] [%s] %s", address, envelopeEncoded)
					if envelope["type"] == "HANDSHAKE":
						if "name" not in data or "room" not in data:
							await closeAbnormally("Invalid name or room.")
							continue
						name = data["name"].strip()
						room = data["room"].strip()
						if not name or not room:
							await closeAbnormally("Invalid name or room.")
							continue
						existingUsers = [user for user in users if user.name == name and user.room == room]
						if len(existingUsers) > 0:
							await closeAbnormally("The specified name is already taken by another user in the room you're trying to join.")
							continue
						user = User(websocket, address, name, room)
						users.append(user)
						self.broadcast(user.room, { "type": "USER_JOINED", "data": { "name": user.name } }, user)
						await user.send({ "type": "HANDSHAKE", "data": None })
					continue
				logger.info("[IN] [%s] [%s - %s] %s", user.room, user.name, user.address, envelopeEncoded)
				match envelope["type"]:
					case "PONG":
						user.handlePong()
					case "USERS":
						await user.send({ "type": "USERS", "data": [{ "name": u.name } for u in users if u.room == user.room]})
					case "CONTROL_MEDIA":
						if self.pendingAction:
							continue # TODO: Send error message
						action = data["action"]
						self.lowestPosition = data["position"]
						totalOtherUsers = len(users) - 1
						if totalOtherUsers == 0:
							self.broadcast(user.room, { "type": "CONTROL_MEDIA", "data": { "action": action, "position": self.lowestPosition }})
						else:
							self.broadcast(user.room, { "type": "MEDIA_STATUS", "data": { "action": action, "requestingUser": { "name": user.name } }}, user)
							self.pendingResponses += totalOtherUsers # TODO: Track user-wise, add a timeout
							self.pendingAction = action
					case "MEDIA_STATUS":
						if not self.pendingAction:
							continue # TODO: Send error message
						self.pendingResponses -= 1
						if "error" in data:
							self.broadcastMessage(user.room, f"{user.name} is not connected to their media player", user)
						else:
							self.lowestPosition = min(self.lowestPosition, data["position"])
						if self.pendingResponses == 0:
							self.broadcast(user.room, { "type": "CONTROL_MEDIA", "data": { "action": self.pendingAction, "position": self.lowestPosition }})
							self.pendingAction = ""
		except ConnectionClosedError:
			if user and not websocket.close_sent:
				user.disconnectReason = "Connection Closed"
		except:
			traceback.print_exc()
			if user:
				user.disconnectReason = "Error"
			await websocket.close(1011)
		if user:
			user.cancelTimers()
			users.remove(user)
			logger.info("[DISCONNECT] [%s] [%s - %s] %s", user.room, user.name, user.address, user.disconnectReason)
			self.broadcast(user.room, { "type": "USER_LEFT", "data": { "name": user.name, "reason": user.disconnectReason } })
		else:
			logger.info("[DISCONNECT] [%s]", address)
