from controllers import WebSocketServer
from utils.logging import logger
import os

port = int(os.environ["PORT"]) if "PORT" in os.environ else 22334
logger.info("Starting WebSocket server on port %s", port)
WebSocketServer(port)
