"""
A Pool object which uses a shifting index to mark which items are free and which aren't

The idea is that swapping two items in the list is faster than popping and appending them.

the `get()` method is super simple give then next free and increase the idx by one, so we don't
give the same item twice

the 'give()' method's special trick is that we swap the returned item with the last given item
this means that an item that can't be given is safely tucked away while the freed item becomes exposed

The weakness here is that if the number of used items stays small with small variations the same items
will be used over and over again, but that isn't really an issue.

the slowest part is getting the item's index, so we could speed it up with some dictionaries, but
that adds complexity and memory that probably isn't worth it. Also using the idx methods exclude that step
so if you need the speed that is the way to use the Pool.
"""
from typing import Callable


class Pool[T]:

    def __init__(self, items: list[T]):
        self._source: list[T] = items
        self._size: int = len(self._source)
        self._free_idx: int = 0

    @classmethod
    def from_callback(cls, size: int, callback: Callable[[int], T]):
        return cls(list((callback(idx) for idx in range(size))))

    @property
    def source(self):
        return self._source

    @property
    def given_items(self) -> tuple[T, ...]:
        return tuple(self._source[:self._free_idx])

    @property
    def free_items(self) -> tuple[T, ...]:
        return tuple(self._source[self._free_idx:])

    @property
    def size(self):
        return self._size

    @property
    def next_idx(self):
        return self._free_idx

    def has_free_slot(self):
        return self._free_idx < self._size

    def get(self) -> T:
        if self._free_idx >= self._size:
            raise IndexError('No free items to return')

        item = self._source[self._free_idx]
        self._free_idx += 1
        return item

    def give(self, item: T):
        idx = self._source.index(item)
        if idx >= self._free_idx:
            return ValueError('trying to return an item which was already returned')

        self._free_idx -= 1
        self._source[self._free_idx], self._source[idx] = item, self._source[self._free_idx]
