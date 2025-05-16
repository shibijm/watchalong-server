from .WebSocketEnvelope import WebSocketEnvelope
from typing import Optional
from utils import AsyncTimer
from utils.logging import logger
from websockets.legacy.server import WebSocketServerProtocol
import json

class User:

	pingInterval = 30
	pingTimeoutDelay = 15

	def __init__(self, websocket: WebSocketServerProtocol, address: str, name: str, room: str):
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
		await self.send({ "type": "PING", "data": None })
		self.pingTimeoutTimer = AsyncTimer(self.pingTimeoutDelay, self.pingTimeout)

	async def pingTimeout(self) -> None:
		self.disconnectReason = "Ping Timeout"
		await self.websocket.close(1002, "Ping response not received in time.")

	def handlePong(self) -> None:
		assert self.pingTimeoutTimer
		self.pingTimeoutTimer.cancel()
		self.pingTimer = AsyncTimer(self.pingInterval, self.ping)

	async def send(self, envelope: WebSocketEnvelope) -> None:
		envelopeEncoded = json.dumps(envelope, separators = (",", ":"))
		if envelope["type"] != "PING":
			logger.info("[OUT] [%s] [%s - %s] %s", self.room, self.name, self.address, envelopeEncoded)
		await self.websocket.send(envelopeEncoded)
