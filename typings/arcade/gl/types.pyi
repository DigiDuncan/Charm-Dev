"""
This type stub file was generated by pyright.
"""

from typing import Dict, Iterable, Optional, Sequence, Tuple
from pyglet import gl
from .buffer import Buffer
from arcade.types import BufferProtocol

type BufferOrBufferProtocol = BufferProtocol | Buffer
type GLenumLike = gl.GLenum | int
type PyGLenum = int
type GLuintLike = gl.GLuint | int
type PyGLuint = int
type OpenGlFilter = tuple[PyGLenum, PyGLenum]
type BlendFunction = tuple[PyGLenum, PyGLenum] | tuple[PyGLenum, PyGLenum, PyGLenum, PyGLenum]
_float_base_format = ...
_int_base_format = ...
pixel_formats = ...
SHADER_TYPE_NAMES = ...
GL_NAMES = ...
def gl_name(gl_type: PyGLenum | None) -> str | PyGLenum | None: ...


class AttribFormat:
    __slots__ = ...
    def __init__(self, name: Optional[str], gl_type: Optional[PyGLenum], components: int, bytes_per_component: int, offset=..., location=...) -> None: ...
    @property
    def bytes_total(self) -> int: ...
    def __repr__(self) -> str: ...


class BufferDescription:
    """Buffer Object description used with :py:class:`arcade.gl.Geometry`.

    This class provides a Buffer object with a description of its content, allowing the
    a :py:class:`~arcade.gl.Geometry` object to correctly map shader attributes
    to a program/shader.

    The formats is a string providing the number and type of each attribute. Currently
    we only support f (float), i (integer) and B (unsigned byte).

    ``normalized`` enumerates the attributes which must have their values normalized.
    This is useful for instance for colors attributes given as unsigned byte and
    normalized to floats with values between 0.0 and 1.0.

    ``instanced`` allows this buffer to be used as instanced buffer. Each value will
    be used once for the whole geometry. The geometry will be repeated a number of
    times equal to the number of items in the Buffer.

    Example::

        # Describe my_buffer
        # It contains two floating point numbers being a 2d position
        # and two floating point numbers being texture coordinates.
        # We expect the shader using this buffer to have an in_pos and in_uv attribute (exact name)
        BufferDescription(
            my_buffer,
            '2f 2f',
            ['in_pos', 'in_uv'],
        )

    :param buffer: The buffer to describe
    :param formats: The format of each attribute
    :param attributes: List of attributes names (strings)
    :param normalized: list of attribute names that should be normalized
    :param instanced: ``True`` if this is per instance data
    """
    _formats: Dict[str, Tuple[Optional[PyGLenum], int]] = ...
    __slots__ = ...
    def __init__(self, buffer: Buffer, formats: str, attributes: Sequence[str], normalized: Optional[Iterable[str]] = ..., instanced: bool = ...) -> None:
        ...
    
    def __repr__(self) -> str:
        ...
    
    def __eq__(self, other) -> bool:
        ...
    


class TypeInfo:
    """
    Describes an opengl type

    :param name: the string representation of this type
    :param enum: The enum of this type
    :param gl_type: the base enum of this type
    :param gl_size: byte size if the gl_type
    :param components: Number of components for this enum
    """
    __slots__ = ...
    def __init__(self, name: str, enum: GLenumLike, gl_type: PyGLenum, gl_size: int, components: int) -> None:
        ...
    
    @property
    def size(self) -> int:
        ...
    
    def __repr__(self) -> str:
        ...
    


class GLTypes:
    """
    Get information about an attribute type.
    During introspection we often just get integers telling us what type is used.
    This can for example be `35664` telling us it's a `GL_FLOAT_VEC2`.
    We want to know this is a `gl.GLfloat` with 2 components so we can compare
    that to the types in the `BufferDescription`.
    These an also be used for uniform introspection.
    """
    types = ...
    @classmethod
    def get(cls, enum: int): # -> TypeInfo:
        ...
    


