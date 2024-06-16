from __future__ import annotations

from pathlib import Path

import arrow
from imgui_bundle import imgui, ImVec2, imgui_ctx

from charm.lib import logging

from .filter import Filter
from .debugmessage import DebugMessage


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

    def add_log(self, msg: str, level: int = logging.INFO) -> None:
        self._items.append(DebugMessage(msg, level))

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
            self.add_log("Something went wrong!", logging.ERROR)
        imgui.same_line()
        if imgui.small_button("Clear"):
            self.clear_log()
        imgui.same_line()
        copy_to_clipboard = imgui.small_button("Copy")

        imgui.separator()

        # Options menu
        with imgui_ctx.begin_popup("Options") as popup:
            if popup:
                _, self.auto_scroll = imgui.checkbox("Auto-Scroll", self.auto_scroll)

        # Options, Filter
        if imgui.button("Options"):
            imgui.open_popup("Options")
        imgui.same_line()
        self.text_filter.draw()

        imgui.separator()

        self.draw_scrolling_region(copy_to_clipboard)

        imgui.separator()

        # Final stretch! this is the console input
        reclaim_focus = False
        # TODO: There is a missing flag? maybe make pr?
        # Also some of these flags are used to do stuff to the text (in particular the CALLBACK ones)
        input_text_flags = imgui.InputTextFlags_.enter_returns_true.value | imgui.InputTextFlags_.callback_completion.value | imgui.InputTextFlags_.callback_history.value
        with imgui_ctx.push_item_width(Filter.input_text_size):
            changed, self._input_string = imgui.input_text("Input", self._input_string, flags=input_text_flags)
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

    def draw_scrolling_region(self, copy_to_clipboard: bool) -> None:
        # Save space for a seperator and a text input field
        footer_height_to_reserve = imgui.get_style().item_spacing.y + imgui.get_frame_height_with_spacing()

        with imgui_ctx.begin_child("ScrollingRegion", ImVec2(0, -footer_height_to_reserve), imgui.ChildFlags_.none.value, imgui.WindowFlags_.horizontal_scrollbar.value) as child:
            if not child:
                return
            if imgui.begin_popup_context_window():
                if imgui.selectable("Clear", False):
                    self.clear_log()

            # Tighten spacing
            with imgui_ctx.push_style_var(imgui.StyleVar_.item_spacing.value, ImVec2(4, 1)):
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
                    if self.text_filter.is_shown(item.prefix + item.message):
                        item.draw()

                if copy_to_clipboard:
                    # Finishing logging all the printing
                    # This is where the copying actually gets done.
                    pass

                # Scroll to the bottom automatically. set_scroll_here_y uses a proportion so 1.0 is max.
                if self.scroll_to_bottom or (self.auto_scroll and imgui.get_scroll_y() >= imgui.get_scroll_max_y()):
                    imgui.set_scroll_here_y(1.0)
                self.scroll_to_bottom = False

    def draw_floating(self) -> None:
        imgui.set_next_window_size(ImVec2(520, 600), imgui.Cond_.first_use_ever.value)
        with imgui_ctx.begin("Console", True) as window:
            if not window:
                return
            self.draw()

    def execute_command(self, command_line: str) -> None:
        self.add_log(f"{command_line}", logging.COMMAND) # type: ignore

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
                    self.add_log(f"| {command}", logging.COMMAND) # type: ignore
            case "SAVE":
                with Path("console_log.txt").open("a") as file:
                    file.write(f"Appending to log @ {arrow.now().isoformat()}\n")
                    for item in self._items:
                        file.write(f"{item}\n")
                    file.write(f"Completed appending to log @ {arrow.now().isoformat()}\n\n")
                self.add_log(f"Finished saving to console_log.txt @ {arrow.now().isoformat()}")
            case _:
                self.add_log(f"? Unrecognized command:\n\t{command_line}", logging.COMMENT) # type: ignore

        self.scroll_to_bottom = True


cons = Console()
