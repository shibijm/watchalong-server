from controllers import WebSocketServer
from utils import KeepAlive
from utils.logging import logger
import os

isHeroku = "PORT" in os.environ
port = int(os.environ["PORT"]) if isHeroku else 22334

if isHeroku:
	logger.info("Heroku detected, activating keep-alive mode")
	KeepAlive()

logger.info("Starting WebSocket server on port %s", port)
WebSocketServer(port)
