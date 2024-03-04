import typing

import imgui

if typing.TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow

def draw(window: "DigiWindow"):
    impl = window.impl
    impl.process_inputs()

    imgui.new_frame()

    imgui.begin("Charm Debug Menu", False)

    imgui.end()
    imgui.render()
    impl.render(imgui.get_draw_data())
