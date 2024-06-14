"""
This type stub file was generated by pyright.
"""

import arcade
from typing import Iterable, Optional, Tuple, Type, TypeVar, Union
from pyglet.event import EventDispatcher
from arcade.gui.widgets import GUIRect, UIWidget
from arcade.types import Point

"""
The better gui for arcade

- Improved events, now fully typed
- UIElements are now called Widgets (like everywhere else)
- Widgets render into a FrameBuffer, which supports in memory drawings with less memory usage
- Support for animated widgets
- Texts are now rendered with pyglet, open easier support for text areas with scrolling
- TextArea with scroll support
"""
W = TypeVar("W", bound=UIWidget)
class UIManager(EventDispatcher):
    """
    UIManager is the central component within Arcade's GUI system.
    Handles window events, layout process and rendering.

    To process window events, :py:meth:`UIManager.enable()` has to be called,
    which will inject event callbacks for all window events and redirects them through the widget tree.

    If used within a view :py:meth:`UIManager.enable()` should be called from :py:meth:`View.on_show_view()` and
    :py:meth:`UIManager.disable()` should be called from :py:meth:`View.on_hide_view()`

    Supports `size_hint` to grow/shrink direct children dependent on window size.
    Supports `size_hint_min` to ensure size of direct children (e.g. UIBoxLayout).
    Supports `size_hint_max` to ensure size of direct children (e.g. UIBoxLayout).

    .. code:: py

        class MyView(arcade.View):
            def __init__():
                super().__init__()
                manager = UIManager()

                manager.add(Dummy())

            def on_show_view(self):
                # Set background color
                self.window.background_color = arcade.color.DARK_BLUE_GRAY

                # Enable UIManager when view is shown to catch window events
                self.ui.enable()

            def on_hide_view(self):
                # Disable UIManager when view gets inactive
                self.ui.disable()

            def on_draw():
                self.clear()

                ...

                manager.draw() # draws the UI on screen

    """
    _enabled = ...
    OVERLAY_LAYER = ...
    def __init__(self, window: Optional[arcade.Window] = ...) -> None:
        ...
    
    def add(self, widget: W, *, index=..., layer=...) -> W:
        """
        Add a widget to the :class:`UIManager`.
        Added widgets will receive ui events and be rendered.

        By default the latest added widget will receive ui events first and will be rendered on top of others.

        The UIManager supports layered setups, widgets added to a higher layer are drawn above lower layers
        and receive events first.
        The layer 10 is reserved for overlaying components like dropdowns or tooltips.

        :param widget: widget to add
        :param index: position a widget is added, None has the highest priority
        :param layer: layer which the widget should be added to, higher layer are above
        :return: the widget
        """
        ...
    
    def remove(self, child: UIWidget): # -> None:
        """
        Removes the given widget from UIManager.

        :param child: widget to remove
        """
        ...
    
    def walk_widgets(self, *, root: Optional[UIWidget] = ..., layer=...) -> Iterable[UIWidget]:
        """
        walks through widget tree, in reverse draw order (most top drawn widget first)

        :param root: root widget to start from, if None, the layer is used
        :param layer: layer to search, None will search through all layers
        """
        ...
    
    def clear(self): # -> None:
        """
        Remove all widgets from UIManager
        """
        ...
    
    def get_widgets_at(self, pos: Point, cls: Type[W] = ..., layer=...) -> Iterable[W]:
        """
        Yields all widgets containing a position, returns first top laying widgets which is instance of cls.

        :param pos: Pos within the widget bounds
        :param cls: class which the widget should be an instance of
        :param layer: layer to search, None will search through all layers
        :return: iterator of widgets of given type at position
        """
        ...
    
    def trigger_render(self): # -> None:
        """
        Request rendering of all widgets before next draw
        """
        ...
    
    def execute_layout(self): # -> None:
        """
        Execute layout process for all widgets.

        This is automatically called during :py:meth:`UIManager.draw()`.
        """
        ...
    
    def enable(self) -> None:
        """
        Registers handler functions (`on_...`) to :py:attr:`arcade.gui.UIElement`

        on_draw is not registered, to provide full control about draw order,
        so it has to be called by the devs themselves.

        Within a view, this method should be called from :py:meth:`arcade.View.on_show_view()`.
        """
        ...
    
    def disable(self) -> None:
        """
        Remove handler functions (`on_...`) from :py:attr:`arcade.Window`

        If every :py:class:`arcade.View` uses its own :py:class:`arcade.gui.UIManager`,
        this method should be called in :py:meth:`arcade.View.on_hide_view()`.
        """
        ...
    
    def on_update(self, time_delta):
        ...
    
    def draw(self) -> None:
        ...
    
    def adjust_mouse_coordinates(self, x: float, y: float) -> Tuple[float, float]:
        """
        This method is used, to translate mouse coordinates to coordinates
        respecting the viewport and projection of cameras.

        It uses the internal camera's map_coordinate methods, and should work with
        all transformations possible with the basic orthographic camera.
        """
        ...
    
    def on_event(self, event) -> Union[bool, None]:
        ...
    
    def dispatch_ui_event(self, event):
        ...
    
    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ...
    
    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        ...
    
    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int):
        ...
    
    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        ...
    
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        ...
    
    def on_key_press(self, symbol: int, modifiers: int):
        ...
    
    def on_key_release(self, symbol: int, modifiers: int):
        ...
    
    def on_text(self, text):
        ...
    
    def on_text_motion(self, motion):
        ...
    
    def on_text_motion_select(self, motion):
        ...
    
    def on_resize(self, width, height): # -> None:
        ...
    
    @property
    def rect(self) -> GUIRect:
        ...
    
    def debug(self): # -> None:
        """Walks through all widgets of a UIManager and prints out the rect"""
        ...
    


