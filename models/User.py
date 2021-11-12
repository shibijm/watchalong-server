from helpers import AsyncTimer
from helpers.logging import logger
from typing import Any, Optional
from websockets.legacy.server import WebSocketServerProtocol
import json

class User:

	pingInterval = 30
	pingTimeoutDelay = 15

	def __init__(self, websocket: WebSocketServerProtocol, address: str, name: str, room: str) -> None:
		self.websocket = websocket
		self.address = address
		self.name = name
		self.room = room
		self.disconnectReason = "Connection Closed"
		self.pingTimer = AsyncTimer(1, self.ping)
		self.pingTimeoutTimer: Optional[AsyncTimer] = None

	def cancelTimers(self) -> None:
		if self.pingTimer.active:
			self.pingTimer.cancel()
		if self.pingTimeoutTimer and self.pingTimeoutTimer.active:
			self.pingTimeoutTimer.cancel()

	async def disconnect(self, reason: str) -> None:
		self.cancelTimers()
		self.disconnectReason = reason
		await self.websocket.close()

	async def ping(self) -> None:
		await self.send({ "event": "PING", "payload": None })
		self.pingTimeoutTimer = AsyncTimer(self.pingTimeoutDelay, self.pingTimeout)

	async def pingTimeout(self) -> None:
		await self.disconnect("Ping Timeout")

	def handlePong(self) -> None:
		assert self.pingTimeoutTimer
		self.pingTimeoutTimer.cancel()
		self.pingTimer = AsyncTimer(self.pingInterval, self.ping)

	async def send(self, data: dict[str, Any]) -> None:
		dataEncoded = json.dumps(data, separators = (",", ":"))
		logger.info("[OUT] [%s] [%s - %s] %s", self.room, self.name, self.address, dataEncoded)
		await self.websocket.send(dataEncoded)

	async def sendMessage(self, message: str) -> None:
		await self.send({ "event": "MESSAGE", "payload": message })
