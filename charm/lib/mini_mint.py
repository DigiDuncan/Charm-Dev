"""
A temporary stop gap between the old menu system and Mint.
"""
from __future__ import annotations
from typing import NamedTuple
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from arcade import Rect, Vec2, LRBT, LBWH, XYWH, draw_rect_filled, color, draw_text
from arcade.math import clamp
from arcade.clock import GLOBAL_CLOCK, GLOBAL_FIXED_CLOCK

from charm.lib.anim import EasingFunction, ease_linear, perc, smerp
from charm.lib.procedural_animators import ProceduralAnimator, SecondOrderAnimatorBase, Animatable
from charm.lib.pool import Pool

DRAGON_PEACH = color.Color(255, 140, 120)

class Padding(NamedTuple):
    left: float
    right: float
    bottom: float
    top: float


def padded_rect(rect: Rect, padding: Padding) -> Rect:
    return LRBT(rect.left - padding.left, rect.right + padding.right, rect.bottom - padding.bottom, rect.top + padding.top)

def padded_sub_rect(rect: Rect, padding: Padding) -> Rect:
    return LRBT(rect.left + padding.left, rect.right - padding.right, rect.bottom + padding.bottom, rect.top - padding.top)


# An alias for Vec2 which generally denotes a vector within the range 0.0 -> 1.0
Anchor = Vec2

@dataclass(eq=True)
class Animation:
    callback: Callable[[float, float]]
    duration: float
    start_time: float
    elapsed: float = 0.0
    delay: float = 0.0
    inset: float = 0.0
    cutoff: float = 0.0
    function: EasingFunction = ease_linear
    cleanup: Callable[[Animation]] | None = None

@dataclass(eq=True)
class ProceduralAnimation[A: Animatable]:
    callback: Callable[[float, float]]
    target_x: A
    target_dx: A
    initial_x: A
    initial_y: A
    initial_dy: A
    frequency: float = 1.0
    damping: float = 0.75
    response: float = 1.0
    start_time: float = 0.0
    elapsed: float = 0.0
    settling: bool = False  # Whether the procedural animator will stop once the target_x and target_dx have been reached.
    cleanup: Callable[[ProceduralAnimation]] | None = None

    def __hash__(self) -> int:
        return hash((self.callback, self.start_time, self.frequency, self.response, self.damping, self.settling))

class Animator:
    """
    A generic animator able to animate properties of gui over time.
    Used to give the UI logic over time.
    """

    def __init__(self) -> None:
        self.animations: list[Animation] = []
        self.procedural_animations: list[ProceduralAnimation] = []
        self.active_procedural_animators: dict[ProceduralAnimation, SecondOrderAnimatorBase] = {}

    def update(self, delta_time: float) -> None:
        time = GLOBAL_CLOCK.time
        for animation in self.animations[:]:
            if time < animation.start_time:
                continue

            elapsed = animation.elapsed = GLOBAL_CLOCK.time_since(animation.start_time)
            fraction = animation.function(0.0, 1.0, perc(0.0, animation.duration, elapsed))

            animation.callback(fraction, elapsed)

            if animation.duration <= elapsed:
                self.animations.remove(animation)
                if animation.cleanup is not None:
                    animation.cleanup(animation)

        for animation in self.procedural_animations[:]:
            if time < animation.start_time:
                continue

            elapsed = animation.elapsed = GLOBAL_CLOCK.time_since(animation.start_time)

            if animation not in self.active_procedural_animators:
                animator = ProceduralAnimator(animation.frequency, animation.damping, animation.response, animation.initial_x, animation.initial_y, animation.initial_dy)
                self.active_procedural_animators[animation] = animator
                continue
            animator = self.active_procedural_animators[animation]
            nx = animator.update(delta_time, animation.target_x)
            ndx = animator.dy
            animation.callback(nx, ndx)

            if nx == animation.target_x and ndx == animation.target_dx and animation.settling:
                if animation.cleanup is not None:
                    animation.cleanup(animation)
                self.active_procedural_animators.pop(animation)
                self.procedural_animations.remove(animation)

    def fixed_update(self, delta_time: float) -> None:
        pass

    def kill_animation(self, animation: Animation, *, do_final_callback: bool = True, do_cleanup: bool = True):
        if animation not in self.animations:
            return

        if animation.start_time < GLOBAL_CLOCK.time and do_final_callback:
            elapsed = animation.elapsed = GLOBAL_CLOCK.time_since(animation.start_time)
            fraction = animation.function(0.0, 1.0, perc(0.0, animation.duration, elapsed))
            animation.callback(fraction, GLOBAL_CLOCK.delta_time)

        self.animations.remove(animation)

        if do_cleanup and animation.cleanup is not None:
            animation.cleanup(animation)

    def kill_procedural_animation(self, animation: ProceduralAnimation, *, do_final_callback: bool = True, do_cleanup: bool = True):
        if animation not in self.procedural_animations:
            return
        self.procedural_animations.remove(animation)

        if animation not in self.active_procedural_animators:
            return

        animator = self.active_procedural_animators[animation]
        if do_final_callback:
            animation.callback(animator.y, animator.dy)

        if do_cleanup and animation.cleanup is not None:
            animation.cleanup(animation)
        self.active_procedural_animators.pop(animation)

    def start_animation(self, callback: Callable[[float, float]], duration: float, *,
                        elapsed: float = 0.0, delay: float = 0.0, inset: float = 0.0, cutoff: float = 0.0,
                        function: EasingFunction = ease_linear, cleanup: Callable[[Animation]] | None = None) -> Animation:
        new_animation = Animation(callback, duration, GLOBAL_CLOCK.time + delay, elapsed, inset, delay, cutoff, function, cleanup)
        self.animations.append(new_animation)
        return new_animation

    def start_procedural_animation[A: Animatable](self, callback: Callable[[float, float]], target_x: A,target_dx: A, initial_x: A, initial_y: A, initial_dy: A, frequency: float = 1.0, damping: float = 0.75, response: float = 1.0, start_time: float = 0.0, settling: bool = False, cleanup: Callable[[ProceduralAnimation]] | None = None) -> ProceduralAnimation:
        new_animation = ProceduralAnimation(callback, target_x, target_dx, initial_x, initial_y, initial_dy, frequency, response, damping, start_time, 0.0, settling, cleanup)
        self.procedural_animations.append(new_animation)
        return new_animation

    # TODO: add fixed update logic

class Element[C: Element]:
    Animator: Animator = None

    def __init__(self, min_size: Vec2 = Vec2(0.0, 0.0)):
        # The area the Element takes up. Not necessarily the area that an Element's children will work within
        # see PaddingElement, but a parent will work on an element based on its bounds. The area an Element draws
        # to is also not depended on the bounds, but they should mostly match to get correct behaviour.
        self._bounds: Rect = LBWH(0.0, 0.0, min_size.x, min_size.y)

        self._minimum_size: Vec2 = min_size

        self.children: list[C] = []

        self._has_outdated_layout: bool = True
        self._visible: bool = True

    @staticmethod
    def start_animation(callback: Callable[[float, float]], duration: float, *,
                        elapsed: float = 0.0, delay: float = 0.0, inset: float = 0.0, cutoff: float = 0.0,
                        function: EasingFunction = ease_linear, cleanup: Callable[[Animation]] | None = None) -> Animation:
        return Element.Animator.start_animation(callback, duration, elapsed=elapsed, delay=delay, inset=inset, cutoff=cutoff, function=function, cleanup=cleanup)

    def add_child(self, child: C) -> None:
        self.children.append(child)
        self.invalidate_layout()

    def insert_child(self, child: C, idx: int = -1) -> None:
        self.children.insert(idx, child)
        self.invalidate_layout()

    def swap_children(self, child_a: C, child_b: C) -> None:
        idx_a, idx_b = self.children.index(child_a), self.children.index(child_b)
        self.children[idx_a], self.children[idx_b] = self.children[idx_b], self.children[idx_a]
        self.invalidate_layout()

    def remove_child(self, child: C) -> None:
        self.children.remove(child)
        self.invalidate_layout()

    def get_child_idx(self, child: C) -> int:
        return self.children.index(child)

    def empty(self, *, recursive: bool = False) -> None:
        children = self.children[:]
        self.children = []
        for child in children:
            if recursive:
                child.empty(recursive=recursive)
                continue
            child.invalidate_layout()
        self.invalidate_layout()

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, is_visible: bool) -> None:
        self._visible = is_visible
        self._visibility_changed()

    def _visibility_changed(self) -> None:
        """
        Overridable property allowing element subclasses
        to have more complicated visibility behaviour
        such as setting an internal sprite's visibility
        """
        pass

    @property
    def minimum_size(self) -> Vec2:
        return self._minimum_size

    @minimum_size.setter
    def minimum_size(self, new_min: Vec2) -> None:
        if new_min == self._minimum_size:
            return
        self._minimum_size = new_min
        self.invalidate_layout()

    @property
    def bounds(self) -> Rect:
        return self._bounds

    @bounds.setter
    def bounds(self, new_bounds: Rect) -> None:
        if self._bounds == new_bounds:
            return

        self._bounds = new_bounds.min_size(
            self._minimum_size.x,
            self._minimum_size.y,
        )

        self.invalidate_layout()

    @property
    def has_outdated_layout(self) -> bool:
        return self._has_outdated_layout or any(child.has_outdated_layout for child in self.children)

    @has_outdated_layout.setter
    def has_outdated_layout(self, outdated: bool) -> None:
        self._has_outdated_layout = outdated

    def _display(self) -> None:
        return

    def _calc_layout(self) -> None:
        pass

    def draw(self) -> None:
        if self.has_outdated_layout:
            # We don't propogate here because we already propogate draw calls
            self._calc_layout()
            self.has_outdated_layout = False

        if not self._visible:
            return

        self._display()
        for child in self.children:
            child.draw()

    def layout(self, *, force: bool = False, recursive: bool = True) -> None:
        if not self.has_outdated_layout and not force:
            return

        self._calc_layout()
        self.has_outdated_layout = False

        if not recursive:
            return

        for child in self.children:
            child.layout(force=force, recursive=recursive)

    def invalidate_layout(self) -> None:
        self._has_outdated_layout = True


class RegionElement(Element):

    def __init__(self, region: Rect = None):
        super().__init__()
        self._region: Rect = region if region is not None else LRBT(0.0, 1.0, 0.0, 1.0)
        self._sub_bounds: Rect = self._bounds

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, new_region: Rect):
        self._region = new_region
        self.invalidate_layout()

    @property
    def sub_bounds(self) -> Rect:
        return self._sub_bounds

    def pixel_rect(self, left = None, right = None, bottom = None, top = None) -> Rect:
        left = (left - self.bounds.left) / self.bounds.width if left is not None else self.region.left
        right = (right - self.bounds.left) / self.bounds.width if right is not None else self.region.right
        bottom = (bottom - self.bounds.bottom) / self.bounds.height if bottom is not None else self.region.bottom
        top = (top - self.bounds.bottom) / self.bounds.height if top is not None else self.region.top
        return LRBT(left, right, bottom, top)

    def _calc_layout(self):
        window_rect = self.bounds
        region_bottom_left = self.region.left, self.region.bottom
        region_top_right = self.region.right, self.region.top
        left, bottom = window_rect.uv_to_position(region_bottom_left)
        right, top = window_rect.uv_to_position(region_top_right)

        self._sub_bounds = LRBT(left, right, bottom, top)
        for child in self.children:
            child.bounds = self._sub_bounds


class PaddingElement(Element):

    def __init__(self, padding: Padding, *, children: list[Element] = None, min_size: Vec2 = Vec2(0, 0)):
        super().__init__(min_size)
        self._padding: Padding = padding
        self._sub_region: Rect = None

        if not children:
            return
        for child in children:
            self.add_child(child)

    @property
    def padding(self) -> Padding:
        return self._padding

    @padding.setter
    def padding(self, new_padding: Padding) -> None:
        self._padding = new_padding
        self.invalidate_layout()

    @property
    def sub_region(self) -> Rect:
        return self._sub_region

    def _calc_layout(self):
        self._sub_region = padded_sub_rect(self._bounds, self._padding)
        for child in self.children:
            child.bounds = self._sub_region


class BoxElement(Element):

    def __init__(
            self,
            colour: color.Color,
            min_size: Vec2 = Vec2(0.0, 0.0), text: str = None
    ):
        super().__init__(min_size=min_size)
        self.colour: color.Color = colour
        self.text = text

    def _display(self):
        draw_rect_filled(self._bounds, self.colour)
        if self.text is not None:
            draw_text(self.text, self.bounds.x, self.bounds.y, anchor_x='center', anchor_y='center')


class AxisAnchor(Enum):
    BEGINNING = 0
    LEFT = 0
    TOP = 0

    CENTER = 1
    MIDDLE = 1

    BOTTOM = 2
    RIGHT = 2
    END = 2


class VerticalElementList[C: Element](Element[C]):
    # TODO: allow for varying priority in the children. Current they are all equally scaled based on the available size

    def __init__(self, anchor_axis: AxisAnchor = AxisAnchor.TOP, strict: bool = True, *, min_size: Vec2 = Vec2()):
        super().__init__(min_size=min_size)
        self._strict: bool = strict
        self._anchor_axis: AxisAnchor = anchor_axis

    @property
    def anchor_axis(self) -> AxisAnchor:
        return self._anchor_axis

    @anchor_axis.setter
    def anchor_axis(self, new_anchor: AxisAnchor) -> None:
        self._anchor_axis = new_anchor
        self.invalidate_layout()

    def _calc_layout(self) -> None:
        # Todo make this smarter I got lazy

        if not self.children:
            return

        heights = [child.minimum_size.y or 1.0 for child in self.children]
        height = sum(heights)

        free_height = self._bounds.height

        if not self._strict:
            free_height = max(free_height, height)

        if height <= free_height:
            fraction = free_height / height
            offset = 0.0
        else:
            fraction = 1.0
            offset = 0.0 if len(self.children) <= 1 else (free_height - height) / (len(self.children) - 1)

        heights = [fraction * h for h in heights]
        left, width = self._bounds.left, self._bounds.width
        match self._anchor_axis:
            case AxisAnchor.TOP:
                top = self._bounds.top
                start_height = heights[0]
                self.children[0].bounds = LBWH(left, top - start_height, width, start_height)
                next_top = self.children[0].bounds.bottom
                for idx in range(1, len(self.children)):
                    next_height = heights[idx]
                    child = self.children[idx]
                    child.bounds = LBWH(left, next_top - next_height - offset, width, next_height)
                    next_top = child.bounds.bottom


            case AxisAnchor.CENTER:
                pass
            case AxisAnchor.BOTTOM:
                pass
