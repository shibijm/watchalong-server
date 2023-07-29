from controllers import WebSocketController
from models import User
from utils import KeepAlive
from utils.logging import logger
from websockets.server import serve
import asyncio
import os

port = int(os.environ["PORT"]) if "PORT" in os.environ else 22334
users: list[User] = []
webSocketController = WebSocketController(users)
keepAliveUrl = os.environ.get("KEEPALIVE_URL")
if keepAliveUrl:
	KeepAlive(keepAliveUrl, users)
async def run() -> None:
	server = await serve(webSocketController.connectionHandler, None, port, ping_interval = None, ping_timeout = None)
	await server.wait_closed()
logger.info("Starting WebSocket server on port %s", port)
asyncio.run(run())
