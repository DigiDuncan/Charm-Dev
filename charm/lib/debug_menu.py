import logging
import re
import typing
import arcade
import arrow

import imgui
from array import array

if typing.TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

class Filter:
    input_text_str = "Filter"
    input_text_size = 400
    regex_special_chars = {"^", "$", ".", "|", "?", "!", "\\", "*", "+", "-", "=", "[", "]", "(", ")", ":", "#", "<", ">"}

    def __init__(self):
        self._filter_str: str = ""
        self._reg_ex: re.Pattern | None = None

    def draw(self):
        imgui.push_item_width(Filter.input_text_size)
        changed, filter_str = imgui.input_text_with_hint(Filter.input_text_str, "+incl, -excl, or regex", self._filter_str)
        if changed:
            s: str = filter_str
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

    def get_filter_pattern(self) -> re.Pattern:
        return self._reg_ex

    def pass_filter(self, item: str):
        if self._reg_ex is None:
            return True

        return self._reg_ex.match(item)

class DebugMessage:
    def __init__(self, message: str, level: int = logging.INFO) -> None:
        self.message = message
        self.level = level
        self.time = arrow.now().format("HH:mm:ss")

    @property
    def color(self):
        match self.level:
            case logging.COMMENT:
                return arcade.color.LIGHT_GRAY.normalized
            case logging.COMMAND:
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
            case logging.COMMAND:
                return "$"
            case logging.COMMENT:
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
        if self.level not in [logging.COMMAND, logging.COMMENT]:
            imgui.push_style_color(imgui.COLOR_TEXT, *arcade.color.PURPLE.normalized)
            imgui.text_unformatted(self.time + " | ")
            imgui.pop_style_color()
            imgui.same_line()

        imgui.push_style_color(imgui.COLOR_TEXT, *self.color)
        imgui.text_unformatted(self.prefix + " ")
        imgui.pop_style_color()

        imgui.same_line()

        imgui.push_style_color(imgui.COLOR_TEXT, *self.color)
        imgui.text_unformatted(self.message)
        imgui.pop_style_color()

class Console:
    commands: dict[str, str] = {
        "HELP": "list all commands and their description",
        "CLEAR": "clear console of all logs",
        "HISTORY": "Show the command history",
        "SAVE": "Save the console to console_log.txt"
    }

    def __init__(self):
        self._input_string: str = ""
        self._items: list[DebugMessage] = []
        self.commands: list[str] = []
        self.history: list[str] = []
        self.text_filter: Filter = Filter()
        self.auto_scroll = True
        self.scroll_to_bottom = False

    def clear_log(self):
        self._items.clear()

    def add_log(self, item: DebugMessage | str):
        if isinstance(item, str):
            item = DebugMessage(item)
        self._items.append(item)

    def draw(self):
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

    def draw_floating(self):
        imgui.set_next_window_size(520, 600, imgui.FIRST_USE_EVER)
        if not imgui.begin("Console", True):
            imgui.end()
            return
        self.draw()
        imgui.end()

    def execute_command(self, command_line: str):
        self.add_log(DebugMessage(f"{command_line}", logging.COMMAND))

        self.history.append(command_line.upper())

        match command_line:
            case "HELP":
                self.add_log("Commands:")
                for command, desc in Console.commands.items():
                    self.add_log(f"| - {command}:-> {desc}")
            case "CLEAR":
                self.clear_log()
            case "HISTORY":
                self.add_log("Command History:")
                for command in self.history[-10:]:
                    self.add_log(DebugMessage(f"| {command}", logging.COMMAND))
            case "SAVE":
                with open("console_log.txt", "a") as file:
                    file.write(f"Appending to log @ {arrow.now().isoformat()}\n")
                    for item in self._items:
                        file.write(f"{item}\n")
                    file.write(f"Completed appending to log @ {arrow.now().isoformat()}\n\n")
                self.add_log(f"Finished saving to console_log.txt @ {arrow.now().isoformat()}")
            case _:
                self.add_log(DebugMessage(f"? Unrecognized command:\n\t{command_line}", logging.COMMENT))

        self.scroll_to_bottom = True

    def render(self):
        imgui.new_frame()
        self.draw()
        imgui.render()


cons = Console()


class ImGuiHandler(logging.Handler):
    def __init__(self, *args, showsource=False, **kwargs):
        self.showsource = showsource
        super().__init__(*args, **kwargs)

    def emit(self, record):
        debug_log = cons
        message = record.getMessage()
        if self.showsource:
            message = f"{record.name}: {message}"
        debug_message = DebugMessage(message, record.levelno)
        debug_log.add_log(debug_message)

def draw(window: "DigiWindow"):
    impl = window.impl
    impl.process_inputs()

    imgui.new_frame()
    imgui.set_next_window_size(550, 350, condition = imgui.FIRST_USE_EVER)

    imgui.begin("Charm Debug Menu", False)

    with imgui.begin_tab_bar("Options") as tab_bar:
        if tab_bar.opened:
            with imgui.begin_tab_item("Settings") as settings:
                if settings.selected:
                    imgui.text("Settings")
                    # Settings
                    _, window.debug_settings["show_fps"] = imgui.checkbox("Show FPS", window.debug_settings["show_fps"])
                    imgui.spacing()
                    imgui.separator()
            with imgui.begin_tab_item("Info") as info:
                if info.selected:
                    imgui.text("Info")
                    imgui.text(f"Local Time: {window.current_view.local_time:.3f}")
                    # FPS Graph
                    imgui.plot_lines(
                        label="FPS",
                        values=array("f", window.fps_list),
                        values_count = len(window.fps_list),
                        scale_min = 120,
                        scale_max = 240,
                    )
                    imgui.spacing()
                    imgui.separator()
            with imgui.begin_tab_item("Log") as log:
                if log.selected:
                    cons.draw()

    imgui.end()
    imgui.render()
    impl.render(imgui.get_draw_data())
