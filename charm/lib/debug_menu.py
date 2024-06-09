from collections import deque
import logging
from pathlib import Path
import re
import statistics
from types import TracebackType
from typing import Self, TypedDict
import arcade
import arrow

from imgui_bundle.python_backends.pyglet_backend import create_renderer, PygletProgrammablePipelineRenderer # type: ignore
from imgui_bundle import imgui, ImVec2

import numpy as np
import pyglet

from charm.lib.digiwindow import DigiWindow


class Filter:
    input_text_str = "Filter"
    input_text_size = 400
    regex_special_chars = {"^", "$", ".", "|", "?", "!", "\\", "*", "+", "-", "=", "[", "]", "(", ")", ":", "#", "<", ">"}

    def __init__(self):
        self._filter_str: str = ""
        self._reg_ex: re.Pattern[str] | None = None

    def draw(self):
        imgui.push_item_width(Filter.input_text_size)
        changed, filter_str = imgui.input_text_with_hint(Filter.input_text_str, "+incl, -excl, or regex", self._filter_str)
        if changed:
            s = filter_str
            if s.startswith("+"):
                # This crazy method means that if any regex characters are used
                # in the query they are treated like normal characters
                s = "".join(""f"\\{char}" if char in Filter.regex_special_chars else char for char in s[1:])
                s = r"^.*"+s
            elif s.startswith("-"):
                # This crazy method means that if any regex characters are used
                # in the query they are treated like normal characters
                s = "".join(""f"\\{char}" if char in Filter.regex_special_chars else char for char in s[1:])
                s = r"^((?!.*" + s + ".*).)*$"
            self.set_filter(s, filter_str)

    def set_filter(self, regex_str: str, raw_str: str):
        self._filter_str = raw_str
        try:
            _reg_ex = re.compile(regex_str)
        except re.error:
            _reg_ex = self._reg_ex
        self._reg_ex = _reg_ex

    def get_filter(self) -> str:
        return self._filter_str

    def get_filter_pattern(self) -> re.Pattern[str] | None:
        return self._reg_ex

    def pass_filter(self, item: str) -> bool:
        if self._reg_ex is None:
            return True

        return self._reg_ex.match(item) is not None


class DebugMessage:
    def __init__(self, message: str, level: int = logging.INFO) -> None:
        self.message = message
        self.level = level
        self.time = arrow.now().format("HH:mm:ss")

    @property
    def color(self):
        match self.level:
            case logging.COMMENT: # type: ignore
                return arcade.color.LIGHT_GRAY.normalized
            case logging.COMMAND: # type: ignore
                return arcade.color.PASTEL_YELLOW.normalized
            case logging.DEBUG:
                return arcade.color.BABY_BLUE.normalized
            case logging.INFO:
                return arcade.color.WHITE.normalized
            case logging.WARN:
                return arcade.color.YELLOW.normalized
            case logging.ERROR:
                return arcade.color.RED.normalized
            case logging.FATAL:
                return arcade.color.MAGENTA.normalized
            case _:
                return arcade.color.GREEN.normalized

    @property
    def prefix(self):
        match self.level:
            case logging.COMMAND: # type: ignore
                return "$"
            case logging.COMMENT: # type: ignore
                return "#"
            case logging.DEBUG:
                return "DBG"
            case logging.INFO:
                return "INF"
            case logging.WARN:
                return "WRN"
            case logging.ERROR:
                return "ERR"
            case logging.FATAL:
                return "!!!"
            case _:
                return "???"

    def render(self) -> None:
        if self.level not in [logging.COMMAND, logging.COMMENT]: # type: ignore
            imgui.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*arcade.color.PURPLE.normalized))
            imgui.text_unformatted(self.time + " | ")
            imgui.pop_style_color()
            imgui.same_line()

        imgui.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*self.color))
        imgui.text_unformatted(self.prefix + " ")
        imgui.pop_style_color()

        imgui.same_line()

        imgui.push_style_color(imgui.Col_.text.value, imgui.ImVec4(*self.color))
        imgui.text_unformatted(self.message)
        imgui.pop_style_color()


class Console:
    def __init__(self):
        self._input_string: str = ""
        self._items: list[DebugMessage] = []
        self.commands: dict[str, str] = {
            "HELP": "list all commands and their description",
            "CLEAR": "clear console of all logs",
            "HISTORY": "Show the command history",
            "SAVE": "Save the console to console_log.txt"
        }
        self.history: list[str] = []
        self.text_filter: Filter = Filter()
        self.auto_scroll = True
        self.scroll_to_bottom = False

    def clear_log(self) -> None:
        self._items.clear()

    def add_log(self, item: DebugMessage | str) -> None:
        if isinstance(item, str):
            item = DebugMessage(item)
        self._items.append(item)

    def draw(self) -> None:
        # Standard console text (not strictly necessary)
        imgui.text_wrapped("Debug Console")
        imgui.text_wrapped("Enter 'HELP' for help")

        # Buttons on top of the console area
        if imgui.small_button("Test Log"):
            self.add_log(f"{len(self._items)} some text")
            self.add_log("some more text")
            self.add_log("display a very important message here!")
        imgui.same_line()
        if imgui.small_button("Test Error"):
            self.add_log(DebugMessage("Something went wrong!", logging.ERROR))
        imgui.same_line()
        if imgui.small_button("Clear"):
            self.clear_log()
        imgui.same_line()
        copy_to_clipboard = imgui.small_button("Copy")

        imgui.separator()

        # Options menu
        if imgui.begin_popup("Options"):
            _, self.auto_scroll = imgui.checkbox("Auto-Scroll", self.auto_scroll)
            imgui.end_popup()

        # Options, Filter
        if imgui.button("Options"):
            imgui.open_popup("Options")
        imgui.same_line()
        self.text_filter.draw()

        imgui.separator()

        # Save space for a seperator and a text input field
        footer_height_to_reserve = imgui.get_style().item_spacing.y + imgui.get_frame_height_with_spacing()
        if imgui.begin_child("ScrollingRegion", 0, -footer_height_to_reserve, imgui.NONE, imgui.WINDOW_HORIZONTAL_SCROLLING_BAR):

            if imgui.begin_popup_context_window():
                if imgui.selectable("Clear"):
                    self.clear_log()
                imgui.end_popup()

            # Tighten spacing
            imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (4, 1))

            if copy_to_clipboard:
                # Start logging all the printing that gets done.
                # The method used by imgui seems to be missing,
                # so we are going to have to make out own
                pass

            # Every line is created individually for colouring, and styling.
            # To do multiple colours on a single line requires using `imgui.same_line()`
            # so it's a difficult ask for dynamic scenarios, but could be used to change
            # the colour of the message type, or the time-stamp

            for item in self._items:
                if self.text_filter.pass_filter(item.prefix + item.message):
                    item.render()

            if copy_to_clipboard:
                # Finishing logging all the printing
                # This is where the copying actually gets done.
                pass

            # Scroll to the bottom automatically. set_scroll_here_y uses a proportion so 1.0 is max.
            if self.scroll_to_bottom or (self.auto_scroll and imgui.get_scroll_y() >= imgui.get_scroll_max_y()):
                imgui.set_scroll_here_y(1.0)
            self.scroll_to_bottom = False

            imgui.pop_style_var()
        imgui.end_child()

        imgui.separator()

        # Final stretch! this is the console input
        reclaim_focus = False
        # TODO: There is a missing flag? maybe make pr?
        # Also some of these flags are used to do stuff to the text (in particular the CALLBACK ones)
        input_text_flags = imgui.INPUT_TEXT_ENTER_RETURNS_TRUE | imgui.INPUT_TEXT_CALLBACK_COMPLETION | imgui.INPUT_TEXT_CALLBACK_HISTORY
        imgui.push_item_width(Filter.input_text_size)
        changed, self._input_string = imgui.input_text("Input", self._input_string, flags=input_text_flags)
        imgui.pop_item_width()
        if changed:
            s: str = self._input_string
            s = s.strip()
            if len(s):
                self.execute_command(s)
            reclaim_focus = True
            self._input_string = ""

        imgui.set_item_default_focus()
        if reclaim_focus:
            imgui.set_keyboard_focus_here(-1)

    def draw_floating(self) -> None:
        imgui.set_next_window_size(520, 600, imgui.FIRST_USE_EVER)
        if not imgui.begin("Console", True):
            imgui.end()
            return
        self.draw()
        imgui.end()

    def execute_command(self, command_line: str) -> None:
        self.add_log(DebugMessage(f"{command_line}", logging.COMMAND)) # type: ignore

        self.history.append(command_line.upper())

        match command_line:
            case "HELP":
                self.add_log("Commands:")
                for command, desc in self.commands.items():
                    self.add_log(f"| - {command}:-> {desc}")
            case "CLEAR":
                self.clear_log()
            case "HISTORY":
                self.add_log("Command History:")
                for command in self.history[-10:]:
                    self.add_log(DebugMessage(f"| {command}", logging.COMMAND)) # type: ignore
            case "SAVE":
                with Path("console_log.txt").open("a") as file:
                    file.write(f"Appending to log @ {arrow.now().isoformat()}\n")
                    for item in self._items:
                        file.write(f"{item}\n")
                    file.write(f"Completed appending to log @ {arrow.now().isoformat()}\n\n")
                self.add_log(f"Finished saving to console_log.txt @ {arrow.now().isoformat()}")
            case _:
                self.add_log(DebugMessage(f"? Unrecognized command:\n\t{command_line}", logging.COMMENT)) # type: ignore

        self.scroll_to_bottom = True

    def render(self) -> None:
        imgui.new_frame()
        self.draw()
        imgui.render()


cons = Console()


class ImGuiHandler(logging.Handler):
    def __init__(self, level: int | str = logging.NOTSET, *, showsource: bool = False):
        self.showsource = showsource
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        debug_log = cons
        message = record.getMessage()
        if self.showsource:
            message = f"{record.name}: {message}"
        debug_message = DebugMessage(message, record.levelno)
        debug_log.add_log(debug_message)


class DebugSettings(TypedDict):
    show_fps: bool


class imgui_tab_bar:  # noqa: N801
    def __init__(self, str_id: str, flags: imgui.TabBarFlags = 0):
        self._str_id = str_id
        self._flags = flags
        self.opened: bool

    def __enter__(self) -> Self:
        self.opened = imgui.begin_tab_bar(self._str_id, self._flags)
        return self

    def __exit__(self, typ: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        imgui.end_tab_bar()


class imgui_tab_item:  # noqa: N801
    def __init__(self, str_id: str, p_open: bool | None = None, flags: imgui.TabItemFlags = 0):
        self._str_id = str_id
        self._p_open = p_open
        self._flags = flags
        self.selected: bool

    def __enter__(self) -> Self:
        self.selected, _ = imgui.begin_tab_item(self._str_id, self._p_open, self._flags)
        return self

    def __exit__(self, typ: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None) -> None:
        imgui.end_tab_item()


class DebugMenu:
    def __init__(self, window: DigiWindow) -> None:
        self.camera = OverlayCamera()
        self.enabled = False
        imgui.create_context()
        imgui.get_io().display_size = imgui.ImVec2(100, 100)
        imgui.font_atlas_get_tex_data_as_rgba32(imgui.get_io().fonts) # type: ignore
        self.impl: PygletProgrammablePipelineRenderer = create_renderer(self) # type: ignore
        self.settings_tab = DebugSettingsTab(window)
        self.info_tab = DebugInfoTab(window)
        self.log_tab = DebugLogTab()
        self.fps_counter = FPSCounter()
        self.debug_label = pyglet.text.Label(
            "DEBUG",
            font_name='bananaslip plus',
            font_size=12,
            multiline=True, width=window.width,
            anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 0xFF)
        )
        self.alpha_label = pyglet.text.Label(
            "ALPHA",
            font_name='bananaslip plus',
            font_size=16,
            anchor_x='right', anchor_y='bottom',
            color=(0, 0, 0, 32)
        )

    @property
    def show_fps(self) -> bool:
        return self.settings_tab.show_fps or self.enabled

    def on_update(self, delta_time: float) -> None:
        self.settings_tab.on_update(delta_time)
        self.info_tab.on_update(delta_time)
        self.log_tab.on_update(delta_time)
        self.fps_counter.enabled = self.show_fps
        self.fps_counter.on_update(delta_time)

    def on_resize(self, width: int, height: int) -> None:
        self.fps_counter.on_resize(width, height)
        self.debug_label.position = (0, height - self.fps_counter.fps_label.content_height - 5, 0)
        self.alpha_label.position = (width - 5, 5, 0)

    def draw(self) -> None:
        with self.camera.activate():
            self.fps_counter.draw()
            self.alpha_label.draw()
            if not self.enabled:
                return
            self.debug_label.draw()
            self.impl.process_inputs()

            imgui.new_frame()
            imgui.set_next_window_size(ImVec2(550, 350), imgui.Cond_.first_use_ever.value)

            imgui.begin("Charm Debug Menu", False)

            self.draw_tab_bar()

            imgui.end()
            imgui.render()
            self.impl.render(imgui.get_draw_data())

    def draw_tab_bar(self) -> None:
        with imgui_tab_bar("Options") as tab_bar:
            if not tab_bar.opened:
                return
            self.settings_tab.draw()
            self.info_tab.draw()
            self.log_tab.draw()


class DebugSettingsTab:
    def __init__(self, window: DigiWindow) -> None:
        self.show_fps = False
        self.window = window

    def on_update(self, delta_time: float) -> None:
        pass

    def draw(self) -> None:
        with imgui_tab_item("Settings") as settings:
            if not settings.selected:
                return
            imgui.text("Settings")
            # Settings
            _, self.show_fps = imgui.checkbox("Show FPS", self.show_fps)
            imgui.spacing()
            imgui.separator()
            imgui.text("Tools")
            # Tools
            if imgui.button("Save atlas..."):
                self.window.save_atlas()
            imgui.spacing()
            imgui.separator()


class DebugInfoTab:
    def __init__(self, window: DigiWindow) -> None:
        self.window = window
        self.beat_list = deque[float]()
        self.fps_list = deque[float]()
        self.local_time: float = 0.0

    def on_update(self, delta_time: float) -> None:
        # Beat Graph
        self.beat_list.append(self.window.theme_song.beat_factor)
        if len(self.beat_list) > 240:
            self.beat_list.popleft()

        # FPS Graph
        curr_fps = 1 / delta_time
        self.fps_list.append(curr_fps)
        if len(self.fps_list) > 240:
            self.fps_list.popleft()

        # localtime
        cv = self.window.current_view()
        self.localtime = cv.local_time if cv is not None else 0.0

    def draw(self) -> None:
        with imgui_tab_item("Info") as info:
            if not info.selected:
                return
            imgui.text("Info")
            imgui.text(f"Current Resolution: {self.window.size}")
            imgui.text(f"Egg Roll: {self.window.egg_roll}")
            imgui.text(f"Current BPM: {self.window.theme_song.current_bpm}")
            # Beat Graph
            imgui.plot_lines( # type: ignore
                label="Beat",
                values=np.array(self.beat_list),
                scale_min = 0,
                scale_max = 1,
            )
            imgui.text(f"Local Time: {self.localtime:.3f}")
            imgui.text(f"Song Time: {self.window.theme_song.time:.3f}")
            # FPS Graph
            imgui.plot_lines( # type: ignore
                label="FPS",
                values=np.array(self.fps_list),
                scale_min = 120,
                scale_max = 240,
            )
            imgui.spacing()
            imgui.separator()
            imgui.text(f"{self.window.ctx.limits.RENDERER}")


class DebugLogTab:
    def __init__(self) -> None:
        pass

    def on_update(self, delta_time: float) -> None:
        pass

    def draw(self) -> None:
        with imgui_tab_item("Log") as log:
            if not log.selected:
                return
            cons.draw()


class FPSCounter:
    def __init__(self):
        self.enabled = False
        self.frames: int = 0
        self.fps_averages: list[float] = []
        self.fps_label = pyglet.text.Label(
            "???.? FPS",
            font_name='bananaslip plus',
            font_size=12,
            anchor_x='left', anchor_y='top',
            color=(0, 0, 0, 0xFF)
        )
        self.fps_shadow_label = pyglet.text.Label(
            "???.? FPS",
            font_name='bananaslip plus',
            font_size=12,
            anchor_x='left', anchor_y='top',
            color=(0xAA, 0xAA, 0xAA, 0xFF)
        )

    def on_update(self, delta_time: float) -> None:
        self.frames += 1
        curr_fps = 1 / delta_time
        # FPS Counter
        if self.frames % 30 == 0:
            average = statistics.mean(self.fps_averages)
            self.fps_label.color = arcade.color.BLACK if average >= 120 else arcade.color.RED
            self.fps_label.text = self.fps_shadow_label.text = f"{average:.1f} FPS"
            self.fps_averages.clear()
        else:
            self.fps_averages.append(curr_fps)

    def on_resize(self, width: int, height: int) -> None:
        self.fps_label.position = (0, height, 0)
        self.fps_shadow_label.position = (1, height - 1, 0)

    def draw(self) -> None:
        if not self.enabled:
            return
        self.fps_shadow_label.draw()
        self.fps_label.draw()


class OverlayCamera(arcade.camera.Camera2D):
    def on_resize(self, width: int, height: int) -> None:
        self.match_screen(and_projection=True)
        self.position = arcade.Vec2(width // 2, height // 2)
