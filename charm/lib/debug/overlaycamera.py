from __future__ import annotations

from arcade import Camera2D, Vec2


class OverlayCamera(Camera2D):
    def on_resize(self, width: int, height: int) -> None:
        self.match_screen(and_projection=True)
        self.position = Vec2(width // 2, height // 2)
