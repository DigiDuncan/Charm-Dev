import logging

from pypresence import Presence, DiscordNotFound, DiscordError


logger = logging.getLogger("charm")

SECONDS_BETWEEN_CALLS = 1


class PresenceManager:
    def __init__(self) -> None:
        self.presence: Presence | None = None
        self.curr_state: str = ""
        self.new_state: str = ""
        self.time: float = 0
        self.wait_until: float = 0

    def connect(self, clientid: str) -> None:
        if self.presence is not None:
            return

        self.curr_state = ""
        self.new_state = ""
        self.wait_until = 0

        try:
            self.presence = Presence(clientid)
        except DiscordNotFound:
            logger.warn("Couldn't make a Discord RPC object!")
            return

        try:
            self.presence.connect()
        except DiscordError:
            self.presence = None
            logger.warn("Discord could not connect the rich presence.")

    def set(self, value: str) -> None:
        self.new_state = value

    def on_update(self, delta_time: float) -> None:
        self.time += delta_time
        self.send_update()

    def send_update(self) -> None:
        # Not connected
        if self.presence is None:
            return
        # No need to update
        if self.curr_state == self.new_state:
            return
        # Waiting to update
        if self.time < self.wait_until:
            return
        self.presence.update(state=self.new_state, large_image="charm-icon-square", large_text="Charm Logo") # type: ignore reportUnknownMemberType
        self.wait_until = self.time + SECONDS_BETWEEN_CALLS
        self.curr_state = self.new_state
