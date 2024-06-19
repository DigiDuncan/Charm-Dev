import asyncio
from types import FunctionType
from typing import Any
from .payloads import Payload

class BaseClient:
    def __init__(self, client_id: str, pipe: str | None = None, loop: asyncio.AbstractEventLoop | None = None, handler: FunctionType | None = None, isasync: bool = False) -> None: ...
    def update_event_loop(self, loop: asyncio.AbstractEventLoop) -> None: ...
    async def read_output(self) -> dict[str, Any]: ...
    def send_data(self, op: int, payload: dict[str, Any] | Payload) -> None: ...
    async def handshake(self) -> None: ...