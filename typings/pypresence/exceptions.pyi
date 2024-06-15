__all__ = (
    "PyPresenceException",
    "DiscordNotFound",
    "InvalidID",
    "InvalidPipe",
    "InvalidArgument",
    "ServerError",
    "DiscordError",
    "ArgumentError",
    "EventNotFound"
)

class PyPresenceException(Exception):
    def __init__(self, message: str = ...) -> None: ...
class DiscordNotFound(PyPresenceException):
    def __init__(self) -> None: ...
class InvalidID(PyPresenceException):
    def __init__(self) -> None: ...
class InvalidPipe(PyPresenceException):
    def __init__(self) -> None: ...
class InvalidArgument(PyPresenceException):
    def __init__(self, expected: str, received: str, description: str = ...) -> None: ...
class ServerError(PyPresenceException):
    def __init__(self, message: str) -> None: ...
class DiscordError(PyPresenceException):
    def __init__(self, code: int, message: str) -> None: ...
class ArgumentError(PyPresenceException):
    def __init__(self) -> None: ...
class EventNotFound(PyPresenceException):
    def __init__(self, event: str) -> None: ...
