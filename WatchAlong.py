from packages.models import Client
from packages.modules import KeepAlive, SocketServer, WebSocketServer
from SimpleWebSocketServer import SimpleWebSocketServer
import os

clients = []
Client.clients = clients
KeepAlive.clients = clients
SocketServer.clients = clients
WebSocketServer.clients = clients

if ("PORT" in os.environ):
	keepAlive = KeepAlive()
	keepAlive.daemon = True
	keepAlive.start()
server = SimpleWebSocketServer("", WebSocketServer.port, WebSocketServer)
print("Websocket Server Running on Port " + str(WebSocketServer.port))
server.serveforever()
