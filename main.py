from utils.logging import logger
from services import KeepAlive, WebSocketServer
import os

isHeroku = "PORT" in os.environ
port = int(os.environ["PORT"]) if isHeroku else 22334

if isHeroku:
	logger.info("Heroku detected, activating keep-alive mode")
	KeepAlive()

logger.info("Starting WebSocket server on port %s", port)
WebSocketServer(port)
