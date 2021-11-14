from typing import Any, TypedDict

class WebSocketEnvelope(TypedDict):
	type: str
	data: Any
