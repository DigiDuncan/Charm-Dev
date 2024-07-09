from __future__ import annotations
from typing import TYPE_CHECKING
from arcade import get_sprites_at_point
from charm.lib.generic.song import Note
if TYPE_CHECKING:
    from charm.lib.digiwindow import DigiWindow


from imgui_bundle import imgui, imgui_ctx

# -- VIEWS --
from charm.views.gameplay import GameView


def draw_game_view(win: DigiWindow, tab: DebugViewTab):
    view: GameView = win.current_view()
    m_x, m_y = imgui.get_mouse_pos_on_opening_current_popup()
    proj_pos = win.current_camera.unproject((m_x, win.height - m_y))
    if imgui.get_mouse_clicked_count(0) == 1:
        sprites = view._display.debug_fetch_note_sprites_at_point(proj_pos)
        draw_game_view.selected_note = None if not sprites else (sprites[0].note if sprites[0].note != draw_game_view.selected_note else sprites[-1].note)
    imgui.text(str(draw_game_view.selected_note))
    if draw_game_view.selected_note is None: return

    imgui.text(f"chart: {draw_game_view.selected_note.chart}")
    imgui.text(f"type: {draw_game_view.selected_note.type}")
    imgui.text(f"lane: {draw_game_view.selected_note.lane}")
    imgui.text(f"time: {draw_game_view.selected_note.time}")
    imgui.text(f"length: {draw_game_view.selected_note.length}")
    imgui.text(f"value: {draw_game_view.selected_note.value}")
    imgui.text(f"hit: {draw_game_view.selected_note.hit}")
    imgui.text(f"missed: {draw_game_view.selected_note.missed}")
    imgui.text(f"hit time: {draw_game_view.selected_note.hit_time}")
    imgui.text(f"extra: {draw_game_view.selected_note.extra_data}")

draw_game_view.selected_note = None

VIEW_MAP = {GameView: draw_game_view}


class DebugViewTab:

    def __init__(self, win: DigiWindow) -> None:
        self._win = win

    def draw(self):
        active_view_type = type(self._win.current_view())
        if active_view_type not in VIEW_MAP:
            return

        with imgui_ctx.begin_tab_item(active_view_type.__name__) as view_tab:
            VIEW_MAP[active_view_type](self._win, self)
            imgui.separator()
