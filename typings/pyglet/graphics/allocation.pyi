"""
This type stub file was generated by pyright.
"""

"""Memory allocation algorithm for vertex arrays and buffers.

The region allocator is used to allocate vertex indices within a vertex
domain's  multiple buffers.  ("Buffer" refers to any abstract buffer presented
by :py:mod:`pyglet.graphics.vertexbuffer`.
 
The allocator will at times request more space from the buffers. The current
policy is to double the buffer size when there is not enough room to fulfil an
allocation.  The buffer is never resized smaller.

The allocator maintains references to free space only; it is the caller's
responsibility to maintain the allocated regions.
"""
class AllocatorMemoryException(Exception):
    """The buffer is not large enough to fulfil an allocation.

    Raised by `Allocator` methods when the operation failed due to
    lack of buffer space.  The buffer should be increased to at least
    requested_capacity and then the operation retried (guaranteed to
    pass second time).
    """
    def __init__(self, requested_capacity) -> None:
        ...
    


class Allocator:
    """Buffer space allocation implementation."""
    __slots__ = ...
    def __init__(self, capacity) -> None:
        """Create an allocator for a buffer of the specified capacity.

        :Parameters:
            `capacity` : int
                Maximum size of the buffer.

        """
        ...
    
    def set_capacity(self, size): # -> None:
        """Resize the maximum buffer size.
        
        The capaity cannot be reduced.

        :Parameters:
            `size` : int
                New maximum size of the buffer.

        """
        ...
    
    def alloc(self, size): # -> Literal[0]:
        """Allocate memory in the buffer.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        :Parameters:
            `size` : int
                Size of region to allocate.
               
        :rtype: int
        :return: Starting index of the allocated region.
        """
        ...
    
    def realloc(self, start, size, new_size): # -> Literal[0]:
        """Reallocate a region of the buffer.

        This is more efficient than separate `dealloc` and `alloc` calls, as
        the region can often be resized in-place.

        Raises `AllocatorMemoryException` if the allocation cannot be
        fulfilled.

        :Parameters:
            `start` : int
                Current starting index of the region.
            `size` : int
                Current size of the region.
            `new_size` : int
                New size of the region.

        """
        ...
    
    def dealloc(self, start, size): # -> None:
        """Free a region of the buffer.

        :Parameters:
            `start` : int
                Starting index of the region.
            `size` : int
                Size of the region.

        """
        ...
    
    def get_allocated_regions(self): # -> tuple[list[Any], list[Any]]:
        """Get a list of (aggregate) allocated regions.

        The result of this method is ``(starts, sizes)``, where ``starts`` is
        a list of starting indices of the regions and ``sizes`` their
        corresponding lengths.

        :rtype: (list, list)
        """
        ...
    
    def get_fragmented_free_size(self): # -> Literal[0]:
        """Returns the amount of space unused, not including the final
        free block.

        :rtype: int
        """
        ...
    
    def get_free_size(self): # -> Any:
        """Return the amount of space unused.
        
        :rtype: int
        """
        ...
    
    def get_usage(self):
        """Return fraction of capacity currently allocated.
        
        :rtype: float
        """
        ...
    
    def get_fragmentation(self): # -> float:
        """Return fraction of free space that is not expandable.
        
        :rtype: float
        """
        ...
    
    def __str__(self) -> str:
        ...
    
    def __repr__(self): # -> str:
        ...
    

