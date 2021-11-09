from models import Client
from modules import KeepAlive, WebSocketServer
from SimpleWebSocketServer import SimpleWebSocketServer
import os

clients = []
Client.clients = clients
KeepAlive.clients = clients
WebSocketServer.clients = clients

isHeroku = "PORT" in os.environ
if (isHeroku):
	keepAlive = KeepAlive()
	keepAlive.daemon = True
	keepAlive.start()
server = SimpleWebSocketServer("", WebSocketServer.port, WebSocketServer)
print("Websocket Server Running on Port " + str(WebSocketServer.port))
server.serveforever()
