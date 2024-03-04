import imgui
from arcade_imgui import ArcadeRenderer

def draw(renderer: ArcadeRenderer):
    imgui.new_frame()
    imgui.show_demo_window(False)
    imgui.render()
    renderer.render(imgui.get_draw_data())
