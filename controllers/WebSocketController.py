from models import User, WebSocketEnvelope
from typing import Optional
from utils.logging import logger
from websockets.exceptions import ConnectionClosedError
from websockets.legacy.protocol import broadcast
from websockets.server import WebSocketServerProtocol
import functools
import json
import traceback

class WebSocketController:

	def __init__(self, users: list[User]) -> None:
		self.users = users

	def broadcast(self, room: str, envelope: WebSocketEnvelope, excludedUser: Optional[User] = None) -> None:
		userWebSockets = [user.websocket for user in self.getUsersInRoom(room) if user != excludedUser]
		if (len(userWebSockets) > 0):
			envelopeEncoded = json.dumps(envelope, separators = (",", ":"))
			logger.info("[BROADCAST] [%s] %s", room, envelopeEncoded)
			broadcast(userWebSockets, envelopeEncoded)

	async def closeAbnormally(self, errorMessage: str, websocket: WebSocketServerProtocol, address: str) -> None:
		logger.info("[OUT] [%s] Abnormal Close: %s", address, errorMessage)
		await websocket.close(1002, errorMessage)

	def getUsersInRoom(self, room: str) -> list[User]:
		return [user for user in self.users if user.room == room]

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
					envelope: WebSocketEnvelope = json.loads(envelopeEncoded)
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
						existingUsers = [user for user in self.getUsersInRoom(room) if user.name == name]
						if len(existingUsers) > 0:
							await closeAbnormally("The specified name is already taken by another user in the room you're trying to join.")
							continue
						user = User(websocket, address, name, room)
						self.users.append(user)
						self.broadcast(user.room, { "type": "USER_JOINED", "data": { "name": user.name } }, user)
						await user.send({ "type": "HANDSHAKE", "data": None })
					continue
				if (envelope["type"] == "PONG"):
					user.handlePong()
					continue
				logger.info("[IN] [%s] [%s - %s] %s", user.room, user.name, user.address, envelopeEncoded)
				match envelope["type"]:
					case "USERS":
						await user.send({ "type": "USERS", "data": [{ "name": user.name } for user in self.getUsersInRoom(user.room)]})
					case "CONTROL_MEDIA":
						self.broadcast(user.room, { "type": "CONTROL_MEDIA", "data": { "requestingUser": { "name": user.name }, "action": data["action"], "position": data["position"] } }, user)
					case "MEDIA_STATE":
						self.broadcast(user.room, { "type": "MEDIA_STATE", "data": { "user": { "name": user.name }, "state": data["state"], "position": data["position"] } }, user)
					case _:
						pass
		except ConnectionClosedError:
			if user and not websocket.close_sent:
				user.disconnectReason = "Connection Closed"
		except:
			logger.error(traceback.format_exc().strip())
			if user:
				user.disconnectReason = "Error"
			await websocket.close(1011)
		if user:
			user.cancelTimers()
			self.users.remove(user)
			logger.info("[DISCONNECT] [%s] [%s - %s] %s", user.room, user.name, user.address, user.disconnectReason)
			self.broadcast(user.room, { "type": "USER_LEFT", "data": { "name": user.name, "reason": user.disconnectReason } })
		else:
			logger.info("[DISCONNECT] [%s]", address)
