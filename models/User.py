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
		self.disconnectReason = "Quit"
		self.pingTimer = AsyncTimer(1, self.ping)
		self.pingTimeoutTimer: Optional[AsyncTimer] = None

	def cancelTimers(self) -> None:
		if self.pingTimer.active:
			self.pingTimer.cancel()
		if self.pingTimeoutTimer and self.pingTimeoutTimer.active:
			self.pingTimeoutTimer.cancel()

	async def ping(self) -> None:
		await self.send({ "type": "PING", "payload": None })
		self.pingTimeoutTimer = AsyncTimer(self.pingTimeoutDelay, self.pingTimeout)

	async def pingTimeout(self) -> None:
		self.disconnectReason = "Ping Timeout"
		await self.websocket.close()

	def handlePong(self) -> None:
		assert self.pingTimeoutTimer
		self.pingTimeoutTimer.cancel()
		self.pingTimer = AsyncTimer(self.pingInterval, self.ping)

	async def send(self, data: dict[str, Any]) -> None:
		dataEncoded = json.dumps(data, separators = (",", ":"))
		logger.info("[OUT] [%s] [%s - %s] %s", self.room, self.name, self.address, dataEncoded)
		await self.websocket.send(dataEncoded)

	async def sendMessage(self, message: str) -> None:
		await self.send({ "type": "MESSAGE", "payload": message })
