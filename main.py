from controllers import WebSocketController
from utils.logging import logger
from websockets.server import serve
import asyncio
import os

version = "1.0.0"
bindAddress = os.environ.get("BIND_ADDRESS", "0.0.0.0")
bindPort = int(os.environ.get("BIND_PORT", "22334"))

async def main() -> None:
	server = await serve(WebSocketController().connectionHandler, bindAddress, bindPort, ping_interval = None, ping_timeout = None)
	await server.wait_closed()

logger.info(f"WatchAlong Server v{version}")
logger.info(f"Bind Address: http://{bindAddress}:{bindPort}")
asyncio.run(main())
