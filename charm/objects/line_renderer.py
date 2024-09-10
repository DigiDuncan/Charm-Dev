from collections.abc import Hashable
from enum import IntEnum
from typing import cast

import arcade
from arcade import Camera2D, Sprite, SpriteList, Texture
from arcade.types import Color


from charm.lib.types import Point, TuplePoint
from charm.objects.lyric_animator import Seconds
from charm.lib.errors import InvalidNoteLengthError


class NoteStruckState(IntEnum):
    UNTOUCHED = 0
    HIT = 1
    MISSED = 2


class LongNoteRenderer:
    def __init__(self,
                 cap_texture: Texture, body_texture: Texture, tail_texture: Texture,
                 width: float, length: float, x: float, y: float,
                 cap_missed: Texture = None, body_missed: Texture = None, tail_missed: Texture = None,
                 cap_hit: Texture = None, body_hit: Texture = None, tail_hit: Texture = None
    ):
        self._cap_textures: tuple[Texture, ...] = (cap_texture, cap_hit or cap_texture, cap_missed or cap_texture)
        self._body_textures: tuple[Texture, ...] = (body_texture, body_hit or body_texture, body_missed or body_texture)
        self._tail_textures: tuple[Texture, ...] = (tail_texture, tail_hit or tail_texture, tail_missed or tail_texture)

        self._note_state: NoteStruckState = NoteStruckState.UNTOUCHED

        cap_inv_aspect = self._cap_textures[self._note_state].height / self._cap_textures[self._note_state].width
        cap_width, cap_height = width, cap_inv_aspect * width

        tail_inv_aspect = self._body_textures[self._note_state].height / self._body_textures[self._note_state].width
        tail_width, tail_height = width, tail_inv_aspect * width

        body_width, body_height = width, length - cap_height - tail_height / 2.0

        if body_height < 0.0:
            raise InvalidNoteLengthError(length, body_height)

        self._cap = Sprite(self._cap_textures[self._note_state], center_x=x, center_y=y + body_height + (tail_height + cap_height)/2.0)
        self._cap.width, self._cap.height = cap_width, cap_height
        self._body = Sprite(self._body_textures[self._note_state], center_x=x, center_y=y + (tail_height + body_height)/2.0)
        self._body.width, self._body.height = body_width, body_height
        self._tail = Sprite(self._tail_textures[self._note_state], center_x=x, center_y=y)
        self._tail.width, self._tail.height = tail_width, tail_height

    def get_sprites(self) -> None:
        return self._cap, self._body, self._tail

    def miss(self) -> None:
        self._note_state = NoteStruckState.MISSED

        self._cap.texture = self._cap_textures[self._note_state]
        self._body.texture = self._body_textures[self._note_state]
        self._tail.texture = self._tail_textures[self._note_state]

    def hit(self) -> None:
        self._note_state = NoteStruckState.HIT

        self._cap.texture = self._cap_textures[self._note_state]
        self._body.texture = self._body_textures[self._note_state]
        self._tail.texture = self._tail_textures[self._note_state]


class LineRenderer:
    def __init__(self, points: list[Point], color: Color, width: float):
        self.points: list[Point] = points
        self.color = color
        self.width = width

    def move(self, x: float, y: float) -> None:
        for p in self.points:
            p.move(x, y)

    @property
    def point_tuples(self) -> list[tuple[float, float]]:
        return [p.xy for p in self.points]

    def update(self, delta_time: float) -> None:
        self.current_time += delta_time

    def draw(self) -> None:
        arcade.draw_line_strip(self.point_tuples, self.color, self.width)


class MultiLineRenderer:
    def __init__(self, line_renderers: dict[Hashable, LineRenderer] | None = None):
        if line_renderers is None:
            line_renderers = {}
        self.line_renderers = line_renderers

    def add_renderer(self, id: Hashable, renderer: LineRenderer) -> None:
        if id in self.line_renderers:
            raise ValueError(f"ID {id} already in multi-line renderer!")
        self.line_renderers[id] = renderer

    def remove_renderer(self, id: Hashable) -> None:
        self.line_renderers.pop(id)

    def remove_renderers_with_prefix(self, prefix: Hashable) -> None:
        p = str(prefix)
        for id in self.line_renderers.keys():
            if str(id).startswith(p):
                self.line_renderers.pop(id)

    def move(self, x: float, y: float) -> None:
        for lr in self.line_renderers.values():
            lr.move(x, y)

    def draw(self) -> None:
        for lr in self.line_renderers.values():
            lr.draw()


class NoteTrail(MultiLineRenderer):
    def __init__(self, note_id: Hashable, note_center: Point, time_start: Seconds, length: Seconds,
                 px_per_s: float, color: Color, point_depth: float = 50, width: float = 100,
                 *, resolution: int = 5, thickness: int = 3, upscroll: bool = False,
                 fill_color: Color | None = None, curve: bool = False):

        self.note_id = note_id
        self.note_center = note_center
        self.width = width
        self.resolution = resolution
        self.upscroll = upscroll
        self.fill_color = fill_color
        self.point_depth = point_depth
        self.color = color
        self.thickness = thickness
        self.curve = curve

        points1: list[TuplePoint] = []
        points2: list[TuplePoint] = []

        self._trail_length = int(length * px_per_s) - self.point_depth

        y = note_center[1]
        self.left_x = note_center[0] - (width / 2)
        self.right_x = note_center[0] + (width / 2)

        if upscroll:
            self._trail_end = y - self._trail_length
            self._point_tip = self._trail_end - self.point_depth
            self.end_y = int(-(length * px_per_s))
            resolution = -resolution
        else:
            self._trail_end = y + self._trail_length
            self._point_tip = self._trail_end + self.point_depth
            self.end_y = int(length * px_per_s)

        # top of line
        points1.append((self.left_x + self.thickness, y))
        points2.append((self.right_x - self.thickness, y))
        # bottom of line
        points1.append((self.left_x + self.thickness, self._trail_end))
        points2.append((self.right_x - self.thickness, self._trail_end))
        if not self.curve:
            points1.append((self.note_center[0], self._point_tip))
            points2.append((self.note_center[0], self._point_tip))

        self.line_renderer1 = LineRenderer([Point(p) for p in points1], self.color, self.thickness)
        self.line_renderer2 = LineRenderer([Point(p) for p in points2], self.color, self.thickness)

        self.rectangles = arcade.shape_list.ShapeElementList()
        self.curve_cap = None
        self.texture = None
        self.sprite = None
        if self.curve:
            self.texture = Texture.create_empty(f"_line_renderer_{self.color}_{self.fill_color}_{self.width}_{self.point_depth}", (self.width, self.point_depth))
            if self.upscroll:
                self.texture = self.texture.flip_vertically()
            self.sprite = Sprite(self.texture)
            offset = -self.point_depth / 2 if self.upscroll else self.point_depth / 2
            self.sprite.position = (self.note_center[0], self._trail_end + offset)
            self.curve_cap = SpriteList()
            self.curve_cap.program = self.curve_cap.ctx.sprite_list_program_no_cull
            self.curve_cap.append(self.sprite)
        self.generate_fill()

        nid = str(note_id)

        super().__init__({f"{nid}_left": self.line_renderer1, f"{nid}_right": self.line_renderer2})

    def generate_fill(self) -> None:
        self.rectangles = arcade.shape_list.ShapeElementList()
        if self.fill_color:
            mid_point_x = (self.left_x + self.right_x) / 2
            mid_point_y = (self.note_center[1] + self._trail_end) / 2
            rect = arcade.shape_list.create_rectangle_filled(mid_point_x, mid_point_y, self.width - self.thickness, self._trail_length, self.fill_color)
            self.rectangles.append(rect)
            if not self.curve:
                tri_left = (self.left_x + self.thickness, self._trail_end)
                tri_right = (self.right_x - self.thickness, self._trail_end)
                tri_bottom = (self.note_center[0], self._point_tip)
                self.rectangles.append(arcade.shape_list.create_polygon([tri_left, tri_right, tri_bottom], self.fill_color))
        if self.curve:
            window = arcade.get_window()
            ctx = window.ctx
            ctx.blend_func = ctx.BLEND_ADDITIVE
            with self.curve_cap.atlas.render_into(self.texture) as fbo:
                l, b, w, h = cast("tuple[int, int, int, int]", fbo.viewport)
                temp_cam = Camera2D(
                    viewport=(l, b, w, h),
                    projection=(0, w, h, 0),
                    position=(0.0, 0.0),
                    render_target=fbo
                )
                with temp_cam.activate():
                    fbo.clear()
                    if self.fill_color:
                        arcade.draw_arc_filled(self.width / 2, 0, self.width - self.thickness * 2,
                                               self.point_depth - self.thickness, self.fill_color, 0, 180)
                    arcade.draw_arc_outline(self.width / 2, 0, self.width - self.thickness * 2,
                                            self.point_depth - self.thickness, self.color, 0, 180, self.thickness * 2)
            ctx.blend_func = ctx.BLEND_DEFAULT

    def move(self, x: float, y: float) -> None:
        for lr in self.line_renderers.values():
            lr.move(x, y)
        self.rectangles.move(x, y)
        if self.curve_cap:
            self.curve_cap.move(x, y)
        self.note_center = (self.note_center[0] + x, self.note_center[1] + y)

    def set_position(self, x: float, y: float) -> None:
        ox, oy = self.note_center
        mx = x - ox
        my = y - oy
        self.move(mx, my)

    def draw(self) -> None:
        if self.rectangles:
            self.rectangles.draw()
        for lr in self.line_renderers.values():
            lr.draw()
        if self.curve_cap:
            self.curve_cap.draw()


class TaikoNoteTrail:
    def __init__(self, note_center: Point, length: Seconds, width: int, px_per_s: float, color: Color, fill_color: Color):
        self.note_center = note_center
        self.length = length
        self.width = width
        self.px_per_s = px_per_s
        self.color = color
        self.fill_color = fill_color

        self.thickness = 3

        self.line_renderers: list[LineRenderer] = []
        self.rectangles = arcade.shape_list.ShapeElementList()

        self._left = note_center[0]
        self._right = self._left + int(px_per_s * length) - (self.width // 2)
        self._px_length = self._right - self._left
        self._top = note_center[1] + (width / 2)
        self._bottom = note_center[1] - (width / 2)

        line_renderer1 = LineRenderer([Point((self._left, self._bottom)), Point((self._right, self._bottom))], self.color, self.thickness)
        self.line_renderers.append(line_renderer1)
        line_renderer2 = LineRenderer([Point((self._left, self._top)), Point((self._right, self._top))], self.color, self.thickness)
        self.line_renderers.append(line_renderer2)

        self.sprite = None
        self.texture = Texture.create_empty(f"_taikonotetrail_{self.color}_{self.fill_color}_{self.width}", (self.width // 2, self.width))
        self.sprite = Sprite(self.texture)
        offset = self.width / 4
        self.sprite.position = (self._right + offset - 1, self.note_center[0])
        self.curve_cap = SpriteList()
        self.curve_cap.append(self.sprite)

        self.generate_fill()

    def generate_fill(self) -> None:
        self.rectangles = arcade.shape_list.ShapeElementList()
        mid_point_x = self._left + (self._px_length // 2)
        rect = arcade.shape_list.create_rectangle_filled(mid_point_x, self.note_center[1], self._px_length, self.width - self.thickness, self.fill_color)
        self.rectangles.append(rect)

        # Deal with the curve
        window = arcade.get_window()
        ctx = window.ctx
        ctx.blend_func = ctx.BLEND_ADDITIVE
        with self.curve_cap.atlas.render_into(self.texture) as fbo:
            fbo.clear()
            if self.fill_color:
                arcade.draw_arc_filled(0, self.width / 2, self.width, self.width - self.thickness, self.fill_color, -90, 90)
            arcade.draw_arc_outline(0, self.width / 2, self.width, self.width - self.thickness, self.color, -90, 90, self.thickness * 2)
        ctx.blend_func = ctx.BLEND_DEFAULT

    def move(self, x: float, y: float) -> None:
        for lr in self.line_renderers:
            lr.move(x, y)
        self.rectangles.move(x, y)
        if self.curve_cap:
            self.curve_cap.move(x, y)
        self.note_center = (self.note_center[0] + x, self.note_center[1] + y)

    def set_position(self, x: float, y: float) -> None:
        ox, oy = self.note_center
        mx = x - ox
        my = y - oy
        self.move(mx, my)

    def draw(self) -> None:
        self.rectangles.draw()
        for lr in self.line_renderers:
            lr.draw()
        self.curve_cap.draw()
