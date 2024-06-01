import importlib.resources as pkg_resources
import logging
import math
from math import ceil
from typing import List

import arcade
from arcade import Sprite, SpriteList, Texture, Text
from pyglet.graphics import Batch

import charm.data.images
from charm.lib.anim import EasingFunction, ease_linear, ease_quadinout
from charm.lib.charm import CharmColors, generate_gum_wrapper, move_gum_wrapper
from charm.lib.digiview import DigiView, shows_errors, ignore_imgui
from charm.lib.types import Seconds
from charm.lib.utils import clamp


logger = logging.getLogger("charm")


class IndexShifter:
    def __init__(self, min_: float, max_: float, width: float, height: float, offset: float, shift: float, screen_size: tuple[int, int]):
        self.min = min_
        self.max = max_
        self.width = width
        self.height = height
        self.screen_width, self.screen_height = screen_size
        self.offset = offset
        self.shift = shift

    def from_adjusted_y(self, adjusted_y: float) -> float:
        # Because the y value is already adjusted we don't need to use the screen height.
        # However, it may make more sense to adjust it within this function call.

        # Take a y value mapped to the range -0.5 to 0.5 and map it based on the width we want the peak's base to be.
        angle = min(0.5, max(-0.5, (adjusted_y + self.shift) / self.height))

        # Take the calculated angle and calculate how far (as a percentage) it should be from the left edge
        x_position = self.width * (0.5 * math.cos(2.0 * math.pi * angle) + 0.5) + self.offset

        # Take this percentage and ensure it is capped at our min and max and scaled base on the width.
        return self.screen_width * min(self.max, max(self.min, x_position))


class ListCycle:
    def __init__(self, texture: Texture, content: List[str], ease: EasingFunction = ease_linear,
                 height: int | None = None, width: int | None = None,
                 sprite_scale: float = 1.0,
                 shift_time: Seconds = 0.25,
                 extra_x_peak_percent: float = 0.2, index_offset: int = 0,
                 minimum_x_percent: float = 0.0, maximum_x_percent: float = 1.0,
                 peak_x_percent: float = 0.2, peak_width_percent: float = 0.8,
                 x_offset: float = 0.1, peak_y_offset: float = 0.0):
        # window properties
        self.win = arcade.get_window()
        self.bounds_width = width or self.win.width
        self.bounds_height = height or self.win.height

        # easing function for the scrolling animation
        self.easing_func = ease

        # Actual shifter object, could probably actually be merged with this class (unless you had other uses for it?)
        self.shifter = IndexShifter(
            minimum_x_percent, maximum_x_percent,
            peak_x_percent, peak_width_percent,
            x_offset, peak_y_offset,
            self.win.get_size()
        )

        # The extra amount the selected sprite should be adjusted
        self.selected_offset = extra_x_peak_percent

        # Unused offset that would move the target sprite up or down (haven't worked this one out)
        self.index_offset = index_offset

        # The strings used as the "content" of each sprite
        # can be replaced by whatever you actually want shown
        self.content: List[str] = content
        self.content_index: int = 0
        self.content_count: int = len(content)

        # Calculate the actual number of sprites to "show" plus two extra to ensure the user never sees any popping
        self.shown_count: int = ceil(self.bounds_height / (texture.height * sprite_scale)) + 2
        self.shown_count += 1 if self.shown_count % 2 else 0  # Ensure that the count is always odd
        self.half_count: int = self.shown_count // 2

        # Sprite properties
        self.sprite_scale: float = sprite_scale
        self.texture = texture
        self.buffer = 0.0

        # Drawables. replace the label batch with whatever you actually want to show
        self.sprite_list = SpriteList()
        self.label_batch = Batch()

        # Create a number of sprites and labels equal to the shown count not the content count
        self.sprite_list.extend(Sprite(texture, scale=sprite_scale) for _ in range(self.shown_count))
        self.labels = list(Text("", 0, 0, align="right", anchor_x="right", anchor_y="center", batch=self.label_batch)
                           for _ in range(self.shown_count))

        # for speed scrolling see 'ListCycle.speed_scroll'
        self.speed_scrolling = False
        self.speed_scroll_velocity: float = 0.0
        self.speed_scroll_max_velocity: float = 100.0
        self.speed_scroll_drag_coefficient: float = 0.95
        self.speed_scroll_threshold: float = 0.1
        self.speed_scroll_acceleration: float = 1 / shift_time

        # Time button pressed
        self.wait_for_long_scroll = 1.0
        self.key_speed = 1.0
        self.up_pressed = False
        self.down_pressed = False
        self.time_up_pressed = 0.0
        self.time_down_pressed = 0.0

        # The offset used to calculate the current index, and how the curve should affect the sprites
        self.total_offset: float = 0.0

        # Where the cycle is scrolling towards
        self.start_offset: float = 0.0
        self.target_offset: float = 0.0
        self.progress: float = 0.0
        self.duration: float = 0.0

        self.shift_time: float = shift_time

        self.do_layout: bool = True

        self.trigger_layout()

    def on_key(self, up: bool, pressed: bool) -> None:
        match (up, pressed):
            case (False, False):
                if self.time_down_pressed > self.wait_for_long_scroll:
                    self.scroll(0)
                self.down_pressed = False
                self.time_down_pressed = 0.0
            case (True, False):
                if self.time_up_pressed > self.wait_for_long_scroll:
                    self.scroll(0)
                self.up_pressed = False
                self.time_up_pressed = 0.0
            case (False, True):
                self.down_pressed = True
            case (True, True):
                self.up_pressed = True

    def scroll(self, dist: float) -> None:
        # Start scrolling to the next target location based on how far we are told to scroll
        self.speed_scrolling = False
        self.speed_scroll_velocity = 0.0

        self.start_offset = self.total_offset
        self.target_offset = clamp(0, self.content_count-1, round(self.total_offset + dist))

        self.progress = 0.0
        self.duration = max(0.5, abs(self.target_offset - self.start_offset)) * self.shift_time

    def speed_scroll(self, dist: float) -> None:
        # If the time since the last speed scroll is small enough then we want to massively boost the scroll
        # distance.

        self.speed_scroll_velocity = clamp(
            -self.speed_scroll_max_velocity, self.speed_scroll_max_velocity,
            self.speed_scroll_velocity + dist * self.speed_scroll_acceleration
        )

        # If the speed scroll was small enough then just scroll since it is neater and looks better
        if abs(self.speed_scroll_velocity) <= 1.0 * self.speed_scroll_acceleration:
            self.scroll(dist)
            return

        # If the scroll is in the other direction then lets stop right away
        if (self.speed_scroll_velocity / abs(self.speed_scroll_velocity)) != (dist / abs(dist)):
            self.scroll(dist)
            return

        self.speed_scrolling = True

    def trigger_layout(self) -> None:
        self.do_layout = True

    def layout(self) -> None:
        self.do_layout = False
        # Find where each sprite should be based on the total offset and the center of the screen
        center = self.bounds_height // 2

        self.content_index = int(self.total_offset)
        remainder = self.total_offset % 1.0

        for i in range(self.shown_count):
            # center the indexes around 0
            n = i - self.half_count + self.index_offset
            # find the actual indexes of the content we care about
            c = self.content_index - n
            sprite = self.sprite_list[i]
            text = self.labels[i]

            # Check to see that this particular sprite has related content
            # If it doesn't we want to hide it.
            sprite.visible = False
            text.text = ""
            if not (c < 0 or self.content_count <= c):
                sprite.visible = True
                text.text = f"{c}: {n}"

            # Calc the y position. This is actually very similar to the original.
            # The difference is where we calculate it from
            # By doing it from the center it makes it far more reliable when resizing the screen
            y = (n + remainder) * (sprite.height + self.buffer)
            x = self.shifter.from_adjusted_y(y / self.bounds_height)

            # Extra offset for the selected sprite. Does not work properly
            if n == 0:
                x += self.selected_offset * self.bounds_width * (1 - remainder)
            elif n + 1 == 0:
                x += self.selected_offset * self.bounds_width * remainder

            # Set the position, this is where you would also position other content
            sprite.center_y = text.y = center + y - self.index_offset * (sprite.height + self.buffer)
            sprite.right = x
            text.x = x - 10

    def update(self, delta_time: float) -> None:
        if self.up_pressed:
            self.time_up_pressed += delta_time
        if self.down_pressed:
            self.time_down_pressed += delta_time

        if self.time_down_pressed > self.wait_for_long_scroll:
            self.speed_scroll(100)
        elif self.time_up_pressed > self.wait_for_long_scroll:
            self.speed_scroll(-100)

        if self.speed_scrolling:
            # We multiply by the abs of the velocity, so we can square it while keeping the sign of the velocity :p
            deacceleration = (
                self.speed_scroll_drag_coefficient * 15.0 * (self.speed_scroll_velocity / abs(self.speed_scroll_velocity))
            )

            new_scroll_velocity = self.speed_scroll_velocity - deacceleration * delta_time
            if new_scroll_velocity / abs(new_scroll_velocity) != self.speed_scroll_velocity / abs(self.speed_scroll_velocity):
                new_scroll_velocity = 0.0
            self.speed_scroll_velocity = new_scroll_velocity
            new_offset = clamp(0.0, self.content_count-1, self.total_offset + self.speed_scroll_velocity * delta_time)

            if new_offset == self.total_offset:
                self.speed_scroll_velocity = 0.0

            self.total_offset = new_offset
            if abs(self.speed_scroll_velocity) < self.speed_scroll_threshold:
                target = clamp(0.0, self.content_count-1, round(new_offset))
                dist = target - new_offset
                self.scroll(dist)

            self.trigger_layout()
        else:
            if self.duration == 0.0:
                return

            finished = False
            new_progress = self.progress + delta_time
            if new_progress >= self.duration:
                new_progress = self.duration
                finished = True

            self.total_offset = self.easing_func(
                self.start_offset, self.target_offset,
                0.0, self.duration,
                new_progress
            )
            self.trigger_layout()

            self.progress = new_progress
            if finished:
                self.start_offset = self.target_offset
                self.duration = 0.0
                self.progress = 0.0

    def update_width(self, new_width: int) -> None:
        if new_width == self.bounds_width:
            return

        self.bounds_width = new_width
        self.shifter.screen_width = new_width

        self.trigger_layout()

    def update_height(self, new_height: int) -> None:
        if new_height == self.bounds_height:
            return

        self.bounds_height = new_height
        self.shifter.screen_height = new_height

        # We should also add / remove sprites and labels by redoing what we did in the init function
        # kinda hard cause batches don't provide methods for removing children (WHY!?)

        self.trigger_layout()

    def draw(self) -> None:
        if self.do_layout:
            self.layout()
        self.sprite_list.draw()
        self.label_batch.draw()


class CycleView(DigiView):
    def __init__(self, back: DigiView):
        super().__init__(fade_in=1, bg_color=CharmColors.FADED_GREEN, back=back)
        self.cycler: ListCycle | None = None

    @shows_errors
    def setup(self) -> None:
        super().setup()

        with pkg_resources.path(charm.data.images, "menu_card.png") as p:
            tex = arcade.load_texture(p)

        self.cycler = ListCycle(texture=tex, content=["a"] * 1000,
                                ease=ease_quadinout,
                                shift_time=0.25,
                                sprite_scale=0.4,
                                )

        # Generate "gum wrapper" background
        self.logo_width, self.small_logos_forward, self.small_logos_backward = generate_gum_wrapper(self.size)

    def on_show_view(self) -> None:
        self.window.theme_song.volume = 0

    @shows_errors
    @ignore_imgui
    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.BACKSPACE:
                self.back.setup()
                self.window.show_view(self.back)
                arcade.play_sound(self.window.sounds["back"])
            case arcade.key.UP:
                self.cycler.scroll(-1.0)
                self.cycler.on_key(True, True)
                arcade.play_sound(self.window.sounds["select"])
            case arcade.key.DOWN:
                self.cycler.scroll(1.0)
                self.cycler.on_key(False, True)
                arcade.play_sound(self.window.sounds["select"])

        super().on_key_press(symbol, modifiers)

    @shows_errors
    @ignore_imgui
    def on_key_release(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.UP:
                self.cycler.on_key(True, False)
            case arcade.key.DOWN:
                self.cycler.on_key(False, False)

        super().on_key_press(symbol, modifiers)

    def calculate_positions(self) -> None:
        if self.cycler is not None:
            self.cycler.update_width(self.window.width)
            self.cycler.update_height(self.window.height)
        super().calculate_positions()

    @shows_errors
    @ignore_imgui
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        # the scroll_y is negative because we are going from top down.
        self.cycler.speed_scroll(-scroll_y)
        arcade.play_sound(self.window.sounds["select"])

    @shows_errors
    def on_update(self, delta_time) -> None:
        super().on_update(delta_time)
        if self.cycler is None:
            return
        self.cycler.update(delta_time)

        move_gum_wrapper(self.logo_width, self.small_logos_forward, self.small_logos_backward, delta_time)

    @shows_errors
    def on_draw(self) -> None:
        self.window.camera.use()
        self.clear()

        if self.cycler is None:
            return

        # Charm BG
        self.small_logos_forward.draw()
        self.small_logos_backward.draw()

        self.cycler.draw()
        super().on_draw()
