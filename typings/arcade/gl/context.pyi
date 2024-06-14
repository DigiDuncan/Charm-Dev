from collections.abc import Generator
import pyglet
from contextlib import contextmanager
from typing import Any, Literal, overload
from collections.abc import Iterable, Sequence
from pyglet.window import Window
from .buffer import Buffer
from .compute_shader import ComputeShader
from .framebuffer import Framebuffer
from .program import Program
from .query import Query
from .texture import Texture2D
from .types import BufferDescription, GLenumLike, PyGLenum
from ..types import BufferProtocol

LOG = ...
class Context:
    active: Context | None = ...
    gl_api: str = ...
    NEAREST: int = ...
    LINEAR: int = ...
    NEAREST_MIPMAP_NEAREST: int = ...
    LINEAR_MIPMAP_NEAREST: int = ...
    NEAREST_MIPMAP_LINEAR: int = ...
    LINEAR_MIPMAP_LINEAR: int = ...
    REPEAT: int = ...
    CLAMP_TO_EDGE: int = ...
    CLAMP_TO_BORDER: int = ...
    MIRRORED_REPEAT: int = ...
    BLEND: int = ...
    DEPTH_TEST: int = ...
    CULL_FACE: int = ...
    PROGRAM_POINT_SIZE: int = ...
    ZERO: int = ...
    ONE: int = ...
    SRC_COLOR: int = ...
    ONE_MINUS_SRC_COLOR: int = ...
    SRC_ALPHA: int = ...
    ONE_MINUS_SRC_ALPHA: int = ...
    DST_ALPHA: int = ...
    ONE_MINUS_DST_ALPHA: int = ...
    DST_COLOR: int = ...
    ONE_MINUS_DST_COLOR: int = ...
    FUNC_ADD: int = ...
    FUNC_SUBTRACT: int = ...
    FUNC_REVERSE_SUBTRACT: int = ...
    MIN: int = ...
    MAX: int = ...
    BLEND_DEFAULT: tuple[int, int] = ...
    BLEND_ADDITIVE: tuple[int, int] = ...
    BLEND_PREMULTIPLIED_ALPHA: tuple[int, int] = ...
    POINTS: int = ...
    LINES: int = ...
    LINE_LOOP: int = ...
    LINE_STRIP: int = ...
    TRIANGLES: int = ...
    TRIANGLE_STRIP: int = ...
    TRIANGLE_FAN: int = ...
    LINES_ADJACENCY: int = ...
    LINE_STRIP_ADJACENCY: int = ...
    TRIANGLES_ADJACENCY: int = ...
    TRIANGLE_STRIP_ADJACENCY: int = ...
    PATCHES: int = ...
    _errors: dict[int, str] = ...
    _valid_apis: tuple[str, ...] = ...
    def __init__(self, window: pyglet.window.Window, gc_mode: str = ..., gl_api: str = ...) -> None: ...
    @property
    def info(self) -> Limits: ...
    @property
    def limits(self) -> Limits: ...
    @property
    def stats(self) -> ContextStats: ...
    @property
    def window(self) -> Window: ...
    @property
    def screen(self) -> Framebuffer: ...
    @property
    def fbo(self) -> Framebuffer: ...
    @property
    def gl_version(self) -> tuple[int, int]: ...
    def gc(self) -> int: ...
    @property
    def gc_mode(self) -> str: ...
    @gc_mode.setter
    def gc_mode(self, value: str) -> None: ...
    @property
    def error(self) -> str | None: ...
    @classmethod
    def activate(cls, ctx: Context) -> None: ...
    def enable(self, *flags: int) -> None: ...
    def enable_only(self, *args: int) -> None: ...
    @contextmanager
    def enabled(self, *flags: int) -> Generator[None, Any, None]: ...
    @contextmanager
    def enabled_only(self, *flags: int) -> Generator[None, Any, None]: ...
    def disable(self, *args: int) -> None: ...
    def is_enabled(self, flag: int) -> bool: ...
    @property
    def viewport(self) -> tuple[int, int, int, int]: ...
    @viewport.setter
    def viewport(self, value: tuple[int, int, int, int]) -> None: ...
    @property
    def scissor(self) -> tuple[int, int, int, int] | None: ...
    @scissor.setter
    def scissor(self, value) -> None: ...
    @property
    def blend_func(self) -> tuple[int, int] | tuple[int, int, int, int]: ...
    @blend_func.setter
    def blend_func(self, value: tuple[int, int] | tuple[int, int, int, int]) -> None: ...
    @property
    def front_face(self) -> str: ...
    @front_face.setter
    def front_face(self, value: str) -> None: ...
    @property
    def cull_face(self) -> str: ...
    @cull_face.setter
    def cull_face(self, value) -> None: ...
    @property
    def wireframe(self) -> bool: ...
    @wireframe.setter
    def wireframe(self, value: bool) -> None: ...
    @property
    def patch_vertices(self) -> int: ...
    @patch_vertices.setter
    def patch_vertices(self, value: int) -> None: ...
    @property
    def point_size(self) -> float: ...
    @point_size.setter
    def point_size(self, value: float) -> None: ...
    @property
    def primitive_restart_index(self) -> int: ...    
    @primitive_restart_index.setter
    def primitive_restart_index(self, value: int) -> None: ...
    def finish(self) -> None: ...
    def flush(self) -> None:
        """
        A suggestion to the driver to execute all the queued
        drawing calls even if the queue is not full yet.
        This is not a blocking call and only a suggestion.
        This can potentially be used for speedups when
        we don't have anything else to render.
        """
        ...
    
    def copy_framebuffer(self, src: Framebuffer, dst: Framebuffer, src_attachment_index: int = ..., depth: bool = ...) -> None:
        """
        Copies/blits a framebuffer to another one.
        We can select one color attachment to copy plus
        an optional depth attachment.

        This operation has many restrictions to ensure it works across
        different platforms and drivers:

        * The source and destination framebuffer must be the same size
        * The formats of the attachments must be the same
        * Only the source framebuffer can be multisampled
        * Framebuffers cannot have integer attachments

        :param src: The framebuffer to copy from
        :param dst: The framebuffer we copy to
        :param src_attachment_index: The color attachment to copy from
        :param depth: Also copy depth attachment if present
        """
        ...
    
    def buffer(self, *, data: BufferProtocol | None = ..., reserve: int = ..., usage: str = ...) -> Buffer:
        """
        Create an OpenGL Buffer object. The buffer will contain all zero-bytes if no data is supplied.

        Examples::

            # Create 1024 byte buffer
            ctx.buffer(reserve=1024)
            # Create a buffer with 1000 float values using python's array.array
            from array import array
            ctx.buffer(data=array('f', [i for in in range(1000)])
            # Create a buffer with 1000 random 32 bit floats using numpy
            self.ctx.buffer(data=np.random.random(1000).astype("f4"))


        The ``data`` parameter can be anything that implements the
        `Buffer Protocol <https://docs.python.org/3/c-api/buffer.html>`_.

        This includes ``bytes``, ``bytearray``, ``array.array``, and
        more. You may need to use typing workarounds for non-builtin
        types. See :ref:`prog-guide-gl-buffer-protocol-typing` for more
        information.

        The ``usage`` parameter enables the GL implementation to make more intelligent
        decisions that may impact buffer object performance. It does not add any restrictions.
        If in doubt, skip this parameter and revisit when optimizing. The result
        are likely to be different between vendors/drivers or may not have any effect.

        The available values mean the following::

            stream
                The data contents will be modified once and used at most a few times.
            static
                The data contents will be modified once and used many times.
            dynamic
                The data contents will be modified repeatedly and used many times.

        :param data: The buffer data. This can be a ``bytes`` instance or any
                                    any other object supporting the buffer protocol.
        :param reserve: The number of bytes to reserve
        :param usage: Buffer usage. 'static', 'dynamic' or 'stream'
        """
        ...
    
    def framebuffer(self, *, color_attachments: Texture2D | list[Texture2D] | None = ..., depth_attachment: Texture2D | None = ...) -> Framebuffer:
        """Create a Framebuffer.

        :param color_attachments: List of textures we want to render into
        :param depth_attachment: Depth texture
        """
        ...
    
    def texture(self, size: tuple[int, int], *, components: int = ..., dtype: str = ..., data: BufferProtocol | None = ..., wrap_x: PyGLenum | None = ..., wrap_y: PyGLenum | None = ..., filter: tuple[PyGLenum, PyGLenum] | None = ..., samples: int = ..., immutable: bool = ..., internal_format: PyGLenum | None = ..., compressed: bool = ..., compressed_data: bool = ...) -> Texture2D:
        """
        Create a 2D Texture.

        Example::

            # Create a 1024 x 1024 RGBA texture
            image = PIL.Image.open("my_texture.png")
            ctx.texture(size=(1024, 1024), components=4, data=image.tobytes())

            # Create and compress a texture. The compression format is set by the internal_format
            image = PIL.Image.open("my_texture.png")
            ctx.texture(
                size=(1024, 1024),
                components=4,
                compressed=True,
                internal_format=gl.GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
                data=image.tobytes(),
            )

            # Create a compressed texture from raw compressed data. This is an extremely
            # fast way to load a large number of textures.
            image_bytes = "<raw compressed data from some source>"
            ctx.texture(
                size=(1024, 1024),
                components=4,
                internal_format=gl.GL_COMPRESSED_RGBA_S3TC_DXT1_EXT,
                compressed_data=True,
                data=image_bytes,
            )

        Wrap modes: ``GL_REPEAT``, ``GL_MIRRORED_REPEAT``, ``GL_CLAMP_TO_EDGE``, ``GL_CLAMP_TO_BORDER``

        Minifying filters: ``GL_NEAREST``, ``GL_LINEAR``, ``GL_NEAREST_MIPMAP_NEAREST``, ``GL_LINEAR_MIPMAP_NEAREST``
        ``GL_NEAREST_MIPMAP_LINEAR``, ``GL_LINEAR_MIPMAP_LINEAR``

        Magnifying filters: ``GL_NEAREST``, ``GL_LINEAR``

        :param Tuple[int, int] size: The size of the texture
        :param components: Number of components (1: R, 2: RG, 3: RGB, 4: RGBA)
        :param dtype: The data type of each component: f1, f2, f4 / i1, i2, i4 / u1, u2, u4
        :param data: The texture data (optional). Can be ``bytes``
                                    or any object supporting the buffer protocol.
        :param wrap_x: How the texture wraps in x direction
        :param wrap_y: How the texture wraps in y direction
        :param filter: Minification and magnification filter
        :param samples: Creates a multisampled texture for values > 0
        :param immutable: Make the storage (not the contents) immutable. This can sometimes be
                               required when using textures with compute shaders.
        :param internal_format: The internal format of the texture. This can be used to
                                enable sRGB or texture compression.
        :param compressed: Set to True if you want the texture to be compressed.
                           This assumes you have set a internal_format to a compressed format.
        :param compressed_data: Set to True if you are passing in raw compressed pixel data.
                                This implies ``compressed=True``.
        """
        ...
    
    def depth_texture(self, size: tuple[int, int], *, data: BufferProtocol | None = ...) -> Texture2D:
        """
        Create a 2D depth texture. Can be used as a depth attachment
        in a :py:class:`~arcade.gl.Framebuffer`.

        :param Tuple[int, int] size: The size of the texture
        :param data: The texture data (optional). Can be
                                    ``bytes`` or any object supporting
                                    the buffer protocol.
        """
        ...
    
    def geometry(self, content: Sequence[BufferDescription] | None = ..., index_buffer: Buffer | None = ..., mode: int | None = ..., index_element_size: int = ...) -> Geometry:
        """
        Create a Geometry instance. This is Arcade's version of a vertex array adding
        a lot of convenience for the user. Geometry objects are fairly light. They are
        mainly responsible for automatically map buffer inputs to your shader(s)
        and provide various methods for rendering or processing this geometry,

        The same geometry can be rendered with different
        programs as long as your shader is using one or more of the input attribute.
        This means geometry with positions and colors can be rendered with a program
        only using the positions. We will automatically map what is necessary and
        cache these mappings internally for performace.

        In short, the geometry object is a light object that describes what buffers
        contains and automatically negotiate with shaders/programs. This is a very
        complex field in OpenGL so the Geometry object provides substantial time
        savings and greatly reduces the complexity of your code.

        Geometry also provide rendering methods supporting the following:

        * Rendering geometry with and without index buffer
        * Rendering your geometry using instancing. Per instance buffers can be provided
          or the current instance can be looked up using ``gl_InstanceID`` in shaders.
        * Running transform feedback shaders that writes to buffers instead the screen.
          This can write to one or multiple buffer.
        * Render your geometry with indirect rendering. This means packing
          multiple meshes into the same buffer(s) and batch drawing them.

        Examples::

            # Single buffer geometry with a vec2 vertex position attribute
            ctx.geometry([BufferDescription(buffer, '2f', ["in_vert"])], mode=ctx.TRIANGLES)

            # Single interlaved buffer with two attributes. A vec2 position and vec2 velocity
            ctx.geometry([
                    BufferDescription(buffer, '2f 2f', ["in_vert", "in_velocity"])
                ],
                mode=ctx.POINTS,
            )

            # Geometry with index buffer
            ctx.geometry(
                [BufferDescription(buffer, '2f', ["in_vert"])],
                index_buffer=ibo,
                mode=ctx.TRIANGLES,
            )

            # Separate buffers
            ctx.geometry([
                    BufferDescription(buffer_pos, '2f', ["in_vert"])
                    BufferDescription(buffer_vel, '2f', ["in_velocity"])
                ],
                mode=ctx.POINTS,
            )

            # Providing per-instance data for instancing
            ctx.geometry([
                    BufferDescription(buffer_pos, '2f', ["in_vert"])
                    BufferDescription(buffer_instance_pos, '2f', ["in_offset"], instanced=True)
                ],
                mode=ctx.POINTS,
            )

        :param content: List of :py:class:`~arcade.gl.BufferDescription` (optional)
        :param index_buffer: Index/element buffer (optional)
        :param mode: The default draw mode (optional)
        :param mode: The default draw mode (optional)
        :param index_element_size: Byte size of a single index/element in the index buffer.
                                       In other words, the index buffer can be 8, 16 or 32 bit integers.
                                       Can be 1, 2 or 4 (8, 16 or 32 bit unsigned integer)
        """
        ...
    
    def program(self, *, vertex_shader: str, fragment_shader: str | None = ..., geometry_shader: str | None = ..., tess_control_shader: str | None = ..., tess_evaluation_shader: str | None = ..., common: list[str] | None = ..., defines: dict[str, str] | None = ..., varyings: Sequence[str] | None = ..., varyings_capture_mode: str = ...) -> Program:
        """Create a :py:class:`~arcade.gl.Program` given the vertex, fragment and geometry shader.

        :param vertex_shader: vertex shader source
        :param fragment_shader: fragment shader source (optional)
        :param geometry_shader: geometry shader source (optional)
        :param tess_control_shader: tessellation control shader source (optional)
        :param tess_evaluation_shader: tessellation evaluation shader source (optional)
        :param common: Common shader sources injected into all shaders
        :param defines: Substitute #defines values in the source (optional)
        :param varyings: The name of the out attributes in a transform shader.
                                                 This is normally not necessary since we auto detect them,
                                                 but some more complex out structures we can't detect.
        :param varyings_capture_mode: The capture mode for transforms.
                                          ``"interleaved"`` means all out attribute will be written to a single buffer.
                                          ``"separate"`` means each out attribute will be written separate buffers.
                                          Based on these settings the `transform()` method will accept a single
                                          buffer or a list of buffer.
        """
        ...
    
    def query(self, *, samples=..., time=..., primitives=...) -> Query:
        """
        Create a query object for measuring rendering calls in opengl.

        :param samples: Collect written samples
        :param time: Measure rendering duration
        :param primitives: Collect the number of primitives emitted

        """
        ...
    
    def compute_shader(self, *, source: str, common: Iterable[str] = ...) -> ComputeShader:
        """
        Create a compute shader.

        :param source: The glsl source
        :param common: Common / library source injected into compute shader
        """
        ...


class ContextStats:
    def __init__(self, warn_threshold=...) -> None:
        ...
    
    def incr(self, key: str) -> None:
        """
        Increments a counter.

        :param key: The attribute name / counter to increment.
        """
        ...
    
    def decr(self, key) -> None:
        """
        Decrement a counter.

        :param key: The attribute name / counter to decrement.
        """
        ...


class Limits:
    def __init__(self, ctx) -> None:
        ...
    
    @overload
    def get_int_tuple(self, enum: GLenumLike, length: Literal[2]) -> tuple[int, int]:
        ...
    
    @overload
    def get_int_tuple(self, enum: GLenumLike, length: int) -> tuple[int, ...]:
        ...
    
    def get_int_tuple(self, enum: GLenumLike, length: int) -> tuple[Any, ...] | tuple[int, ...]:
        """Get an enum as an int tuple"""
        ...
    
    def get(self, enum: GLenumLike, default=...) -> int:
        """Get an integer limit"""
        ...
    
    def get_float(self, enum: GLenumLike, default=...) -> float:
        """Get a float limit"""
        ...
    
    def get_str(self, enum: GLenumLike) -> str:
        """Get a string limit"""
        ...
