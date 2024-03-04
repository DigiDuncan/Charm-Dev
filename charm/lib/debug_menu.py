import typing

import imgui
from array import array

if typing.TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

def draw(window: "DigiWindow"):
    impl = window.impl
    impl.process_inputs()

    imgui.new_frame()
    imgui.set_next_window_size(550, 350, condition = imgui.FIRST_USE_EVER)

    imgui.begin("Charm Debug Menu", False)

    imgui.text("Settings")
    # A Number
    _, window.debug_settings["a_number"] = imgui.slider_int("A Number", window.debug_settings["a_number"], 0, 100)

    imgui.spacing()

    imgui.text("Info")
    # FPS Graph
    imgui.plot_lines(
        label="FPS",
        values=array("f", window.fps_list),
        values_count=len(window.fps_list),
        scale_min = 120,
        scale_max = 240,
    )

    imgui.end()
    imgui.render()
    impl.render(imgui.get_draw_data())
