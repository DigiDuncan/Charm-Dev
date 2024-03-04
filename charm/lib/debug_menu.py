import typing

import imgui

if typing.TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

def draw(window: "DigiWindow"):
    impl = window.impl
    impl.process_inputs()

    imgui.new_frame()
    imgui.set_next_window_size(550, 350, condition = imgui.FIRST_USE_EVER)

    imgui.begin("Charm Debug Menu", False)

    _, window.debug_settings["a_number"] = imgui.input_int("A Number", window.debug_settings["a_number"])

    imgui.end()
    imgui.render()
    impl.render(imgui.get_draw_data())
