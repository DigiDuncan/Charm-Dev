from .baseclient import BaseClient
from .client import AioClient, Client
from .exceptions import (
    PyPresenceException,
    DiscordNotFound,
    InvalidID,
    InvalidPipe,
    InvalidArgument,
    ServerError,
    DiscordError,
    ArgumentError,
    EventNotFound
)
from .presence import AioPresence, Presence

__all__ = (
    "BaseClient",
    "AioClient",
    "Client",
    "PyPresenceException",
    "DiscordNotFound",
    "InvalidID",
    "InvalidPipe",
    "InvalidArgument",
    "ServerError",
    "DiscordError",
    "ArgumentError",
    "EventNotFound",
    "AioPresence",
    "Presence"
)

__title__: str = ...
__author__: str = ...
__copyright__: str = ...
__license__: str = ...
__version__: str = ...
