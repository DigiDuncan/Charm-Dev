from typing import Any, Self

class Payload:
    def __init__(self, data: dict[str, Any], clear_none: bool = ...) -> None: ...
    @staticmethod
    def time() -> float: ...
    @classmethod
    def set_activity(cls, pid: int = ..., state: str = ..., details: str = ..., start: int = ..., end: int = ..., large_image: str = ..., large_text: str = ..., small_image: str = ..., small_text: str = ..., party_id: str = ..., party_size: list[Any] = ..., join: str = ..., spectate: str = ..., match: str = ..., buttons: list[Any] = ..., instance: bool = ..., activity: bool | None = ..., _rn: bool = ...) -> Self: ...
    @classmethod
    def authorize(cls, client_id: str, scopes: list[str]) -> Self: ...
    @classmethod
    def authenticate(cls, token: str) -> Self: ...
    @classmethod
    def get_guilds(cls) -> Self: ...
    @classmethod
    def get_guild(cls, guild_id: str) -> Self: ...
    @classmethod
    def get_channels(cls, guild_id: str) -> Self: ...
    @classmethod
    def get_channel(cls, channel_id: str) -> Self: ...
    @classmethod
    def set_user_voice_settings(cls, user_id: str, pan_left: float = ..., pan_right: float = ..., volume: int = ..., mute: bool = ...) -> Self: ...
    @classmethod
    def select_voice_channel(cls, channel_id: str) -> Self: ...
    @classmethod
    def get_selected_voice_channel(cls) -> Self: ...
    @classmethod
    def select_text_channel(cls, channel_id: str) -> Self: ...
    @classmethod
    def subscribe(cls, event: str, args: dict[str, Any] | None = ...) -> Self: ...
    @classmethod
    def unsubscribe(cls, event: str, args: dict[str, Any] | None = ...) -> Self: ...
    @classmethod
    def get_voice_settings(cls) -> Self: ...
    @classmethod
    def set_voice_settings(cls, _input: dict[str, Any] = ..., output: dict[str, Any] = ..., mode: dict[str, Any] = ..., automatic_gain_control: bool = ..., echo_cancellation: bool = ..., noise_suppression: bool = ..., qos: bool = ..., silence_warning: bool = ..., deaf: bool = ..., mute: bool = ...) -> Self: ...
    @classmethod
    def capture_shortcut(cls, action: str) -> Self: ...
    @classmethod
    def send_activity_join_invite(cls, user_id: str) -> Self: ...
    @classmethod
    def close_activity_request(cls, user_id: str) -> Self: ...

