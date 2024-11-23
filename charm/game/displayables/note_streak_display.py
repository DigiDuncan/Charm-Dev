from __future__ import annotations

from dataclasses import dataclass

from arcade import Text
import arcade

from charm.lib.types import NEVER
from charm.lib.utils import clamp, map_range

from charm.game.generic import BaseEngine

@dataclass
class MilestoneSet:
    gap: int
    additional: set[int]

DEFAULT_MILESTONE_SET = MilestoneSet(100, {25, 50})

class NoteStreakDisplay:
    def __init__(self, engine: BaseEngine, x: float, y: float,
                 milestones: MilestoneSet = DEFAULT_MILESTONE_SET, suffix = "Note Streak!") -> None:
        self.engine = engine
        self.milestones = milestones
        self.suffix = suffix

        self.last_streak = 0

        self.latest_popup_time: float = NEVER
        self.latest_milestone: int = 0

        self.x = x
        self.y = y

        self.current_time = 0.0

        self.popup_time = 1.0
        self.fade_out_time = 1.0

        self.popup_text = Text("OH NO", x, y, arcade.color.BLACK, 48, font_name = "bananaslip plus", align = "center", anchor_x = "center", anchor_y = "center")

    def update(self, song_time: float) -> None:
        self.current_time = song_time
        if self.engine.streak != self.last_streak:
            if self.engine.streak != 0 and (self.engine.streak in self.milestones.additional or self.engine.streak % self.milestones.gap == 0):
                self.latest_popup_time = song_time
                self.latest_milestone = self.engine.streak
                self.popup_text.text = str(self.latest_milestone) if not self.suffix else f"{self.latest_milestone} {self.suffix}"

            self.last_streak = self.engine.streak

    def draw(self) -> None:
        if self.latest_popup_time <= self.current_time <= self.latest_popup_time + self.popup_time + self.fade_out_time:
            new_a = clamp(0, int(map_range(self.current_time, self.latest_popup_time + self.popup_time, self.latest_popup_time + self.popup_time + self.fade_out_time, 255, 0)), 255)
            self.popup_text.color = self.popup_text.color.replace(a = new_a)
            self.popup_text.draw()
