"""
Reviewer Note
=============

Provides a lazy sliding-window helper over any iterable.

Semantic notes
--------------
1. Returns an iterator, not a list. Windows are produced lazily so large or
   infinite iterables are handled without materialising all results.
2. Each yielded window is a tuple, not a list. Windows represent immutable
   snapshots of consecutive values rather than mutable batches.
3. Every yielded window has length exactly ``size``. Partial trailing windows
   are never yielded.
4. Iterables shorter than ``size`` yield nothing. A partial first window is
   discarded rather than returned.
5. Generator-safe and single-pass. Items are consumed exactly once using a
   rolling ``collections.deque`` buffer.
6. ``step`` controls the stride between window start positions.
   * ``step=1`` yields fully overlapping windows.
   * ``step=size`` yields non-overlapping windows.
   * ``step>size`` skips items entirely between windows. Those skipped items
     are never included in any yielded window.
7. ``size < 1`` and ``step < 1`` are invalid and raise ``ValueError``.

Test gaps
---------
- Did not benchmark performance or memory usage on extremely large iterables.
- Did not test every possible iterable type (for example file objects or
  custom iterator classes), since the implementation only depends on the
  standard iterator protocol.
- Did not exhaustively test every combination of ``size`` and ``step`` beyond
  the documented semantics and representative edge cases.
"""

from collections import deque
from itertools import islice
from typing import Deque, Iterable, Iterator, Tuple, TypeVar

T = TypeVar("T")


def window(
    iterable: Iterable[T],
    size: int,
    step: int = 1,
) -> Iterator[Tuple[T, ...]]:
    """
    Yield successive sliding windows of exactly ``size`` consecutive items.

    Each yielded value is a tuple of length exactly ``size``. The ``step``
    argument controls the distance between window start positions.

    Args:
        iterable: Source iterable.
        size: Number of consecutive items per window. Must be at least 1.
        step: Distance between window starts. Must be at least 1.

    Yields:
        Tuples containing exactly ``size`` consecutive items.

    Raises:
        ValueError: If ``size`` or ``step`` is less than 1.
    """
    if size < 1:
        raise ValueError("size must be at least 1")
    if step < 1:
        raise ValueError("step must be at least 1")

    it = iter(iterable)
    buffer: Deque[T] = deque(maxlen=size)

    try:
        for _ in range(size):
            buffer.append(next(it))
    except StopIteration:
        return

    while True:
        yield tuple(buffer)

        if step <= size:
            advance = step
            keep = size - advance

            if keep:
                retained = list(islice(buffer, advance, size))
            else:
                retained = []

            buffer.clear()
            buffer.extend(retained)

            try:
                while len(buffer) < size:
                    buffer.append(next(it))
            except StopIteration:
                return

        else:
            skip = step - size

            try:
                for _ in range(skip):
                    next(it)
            except StopIteration:
                return

            buffer.clear()

            try:
                for _ in range(size):
                    buffer.append(next(it))
            except StopIteration:
                return


if __name__ == "__main__":
    # Basic step=1
    assert list(window([1, 2, 3, 4, 5], 3)) == [
        (1, 2, 3),
        (2, 3, 4),
        (3, 4, 5),
    ]

    # Windows are tuples
    assert isinstance(next(window([1, 2, 3], 2)), tuple)

    # Iterable shorter than size
    assert list(window([1, 2], 3)) == []

    # Iterable exactly equal to size
    assert list(window([1, 2, 3], 3)) == [(1, 2, 3)]

    # Empty input
    assert list(window([], 3)) == []

    # step=2
    assert list(window([1, 2, 3, 4, 5, 6], 3, step=2)) == [
        (1, 2, 3),
        (3, 4, 5),
    ]

    # step=size
    assert list(window([1, 2, 3, 4, 5, 6], 3, step=3)) == [
        (1, 2, 3),
        (4, 5, 6),
    ]

    # step>size
    assert list(window([1, 2, 3, 4, 5, 6, 7, 8], 2, step=3)) == [
        (1, 2),
        (4, 5),
        (7, 8),
    ]

    # Generator-safe single-pass
    counter = {"count": 0}

    def counted():
        for i in range(5):
            counter["count"] += 1
            yield i

    gen = counted()
    assert list(window(gen, 3)) == [
        (0, 1, 2),
        (1, 2, 3),
        (2, 3, 4),
    ]
    assert counter["count"] == 5

    # Generator stays exhausted
    assert next(gen, None) is None

    # size < 1
    try:
        list(window([1, 2, 3], 0))
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # step < 1
    try:
        list(window([1, 2, 3], 2, step=0))
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # Lazy iteration with infinite generator
    def infinite():
        n = 0
        while True:
            yield n
            n += 1

    first_three = list(islice(window(infinite(), 3), 3))
    assert first_three == [
        (0, 1, 2),
        (1, 2, 3),
        (2, 3, 4),
    ]

    print("All tests passed.")