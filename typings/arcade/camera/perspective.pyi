"""
This type stub file was generated by pyright.
"""

from typing import Generator, Optional, TYPE_CHECKING
from typing_extensions import Self
from contextlib import contextmanager
from pyglet.math import Mat4, Vec2, Vec3
from arcade.camera.data_types import CameraData, PerspectiveProjectionData, Projector
from arcade.types import Point, Rect
from arcade import Window

if TYPE_CHECKING:
    ...
__all__ = ("PerspectiveProjector", )
class PerspectiveProjector(Projector):
    """
    The simplest from of a perspective camera.
    Using ViewData and PerspectiveProjectionData PoDs (Pack of Data)
    it generates the correct projection and view matrices. It also
    provides methods and a context manager for using the matrices in
    glsl shaders.

    This class provides no methods for manipulating the PoDs.

    The current implementation will recreate the view and
    projection matrices every time the camera is used.
    If used every frame or multiple times per frame this may
    be inefficient. If you suspect this is causing slowdowns
    profile before optimizing with a dirty value check.

    Initialize a Projector which produces a perspective projection matrix using
    a CameraData and PerspectiveProjectionData PoDs.

    :param window: The window to bind the camera to. Defaults to the currently active camera.
    :param view: The CameraData PoD. contains the viewport, position, up, forward, and zoom.
    :param projection: The PerspectiveProjectionData PoD.
                contains the field of view, aspect ratio, and then near and far planes.
    """
    def __init__(self, *, window: Optional[Window] = ..., view: Optional[CameraData] = ..., projection: Optional[PerspectiveProjectionData] = ..., viewport: Optional[Rect] = ..., scissor: Optional[Rect] = ...) -> None:
        ...
    
    @property
    def view(self) -> CameraData:
        """
        The CameraData. Is a read only property.
        """
        ...
    
    @property
    def projection(self) -> PerspectiveProjectionData:
        """
        The OrthographicProjectionData. Is a read only property.
        """
        ...
    
    def generate_projection_matrix(self) -> Mat4:
        """
        alias of arcade.camera.get_perspective_matrix method
        """
        ...
    
    def generate_view_matrix(self) -> Mat4:
        """
        alias of arcade.camera.get_view_matrix method
        """
        ...
    
    @contextmanager
    def activate(self) -> Generator[Self, None, None]:
        """Set this camera as the current one, then undo it after.

        This method is a :external:ref:`context manager <context-managers>`
        you can use inside ``with`` blocks. Using it this way guarantees
        that the old camera and its settings will be restored, even if an
        exception occurs:

        .. code-block:: python

           # Despite an Exception, the previous camera and its settings
           # will be restored at the end of the with block below:
           with projector_instance.activate():
                sprite_list.draw()
                _ = 1 / 0  # Guaranteed ZeroDivisionError

        """
        ...
    
    def use(self) -> None:
        """
        Sets the active camera to this object.
        Then generates the view and projection matrices.
        Finally, the gl context viewport is set, as well as the projection and view matrices.
        """
        ...
    
    def project(self, world_coordinate: Point) -> Vec2:
        """
        Take a Vec2 or Vec3 of coordinates and return the related screen coordinate
        """
        ...
    
    def unproject(self, screen_coordinate: Point) -> Vec3:
        """
        Take in a pixel coordinate from within
        the range of the window size and returns
        the world space coordinates.

        Essentially reverses the effects of the projector.

        # TODO: UPDATE
        Args:
            screen_coordinate: A 2D position in pixels from the bottom left of the screen.
                               This should ALWAYS be in the range of 0.0 - screen size.
        Returns:
            A 3D vector in world space.
        """
        ...
    


