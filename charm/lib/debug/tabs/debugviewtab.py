from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from charm.core.digiwindow import DigiWindow


from imgui_bundle import imgui, imgui_ctx

# TODO!: FIX

# -- VIEWS --
#from charm.refactor.gameplay import GameView
#
#
#def draw_game_view(win: DigiWindow, tab: DebugViewTab):
#    imgui.columns(2)
#
#    view: GameView = win.current_view()
#    m_x, m_y = imgui.get_mouse_pos_on_opening_current_popup()
#    proj_pos = win.current_camera.unproject((m_x, win.height - m_y))
#    if imgui.get_mouse_clicked_count(0) == 1 and not imgui.get_io().want_capture_mouse:
#        sprites = view._display.debug_fetch_note_sprites_at_point(proj_pos)
#        draw_game_view.selected_sprite = None if not sprites else (sprites[0] if sprites[0] != draw_game_view.selected_sprite else sprites[-1])
#    imgui.text(str(draw_game_view.selected_sprite))
#    if draw_game_view.selected_sprite is None:
#        return
#    note = draw_game_view.selected_sprite.note
#
#    imgui.text(f"Chart: {note.chart}")
#    imgui.text(f"Type: {note.type}")
#    imgui.text(f"Lane: {note.lane}")
#    imgui.text(f"Time: {note.time}")
#    imgui.text(f"Length: {note.length}")
#    imgui.next_column()
#    area = win.ctx.default_atlas.get_texture_region_info(draw_game_view.selected_sprite.texture.atlas_name)
#    coords = area.texture_coordinates
#    uv_1 = coords[0], coords[1]
#    uv_2 = coords[-2], coords[-1]
#    imgui.image(win.ctx.default_atlas.texture.glo.value, imgui.ImVec2(128, 128), uv0=uv_1, uv1=uv_2)
#    imgui.next_column()
#    imgui.text(f"Hit: {note.hit}")
#    imgui.text(f"Missed: {note.missed}")
#    imgui.text(f"Hit Time: {note.hit_time}")
#    imgui.text(f"Extra: {note.extra_data}")
#
# draw_game_view.selected_sprite = None

VIEW_MAP = {} # {GameView: draw_game_view}


class DebugViewTab:

    def __init__(self, win: DigiWindow) -> None:
        self._win = win

    def draw(self) -> None:
        active_view_type = type(self._win.current_view())
        if active_view_type not in VIEW_MAP:
            return

        with imgui_ctx.begin_tab_item(active_view_type.__name__):
            VIEW_MAP[active_view_type](self._win, self)
            imgui.separator()
