"""
Reviewer Note
=============

This module provides a small lazy helper for yielding the first `n`
items from an iterable.

Semantics
---------
1. Returns an iterator, not a list.
   - The function is lazy. Callers who want eager materialisation
     should wrap it with `list(...)`.

2. `n == 0` is valid.
   - Produces an empty iterator without error.

3. `n < 0` raises ValueError.
   - Negative requests are considered malformed input.

4. Non-integer `n` raises TypeError.
   - Rejects floats, strings, None, etc., rather than silently
     coercing values.

5. Short iterables are not an error.
   - If fewer than `n` items exist, every available item is yielded.

6. Generator-safe and single-pass.
   - Consumes only the requested number of items (or the whole
     iterable if it ends first). Remaining generator items are left
     available.

Test gaps
---------
1. Boolean values were not tested.
   - `bool` is a subclass of `int`. Behaviour follows normal Python
     integer semantics but is not tested explicitly.

2. Custom iterable classes were not tested.
   - Tests cover built-in iterable types and generators only.

3. Exception-raising iterators were not tested.
   - No test verifies propagation of exceptions originating from the
     source iterable.
"""

from itertools import islice
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def take(iterable: Iterable[T], n: int) -> Iterator[T]:
    """
    Yield the first n items from an iterable.

    Args:
        iterable: Source iterable.
        n: Number of items to yield.

    Returns:
        A lazy iterator yielding at most n items.

    Raises:
        TypeError: If n is not an integer.
        ValueError: If n is negative.
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")

    if n < 0:
        raise ValueError("n must be non-negative")

    yield from islice(iterable, n)


if __name__ == "__main__":
    # Basic
    assert list(take([1, 2, 3, 4, 5], 3)) == [1, 2, 3]

    # n == 0
    assert list(take([1, 2, 3], 0)) == []

    # n > length
    assert list(take([1, 2, 3], 10)) == [1, 2, 3]

    # Empty iterable
    assert list(take([], 5)) == []

    # String iterable
    assert list(take("hello", 3)) == ["h", "e", "l"]

    # Negative n
    try:
        list(take([1, 2, 3], -1))
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Non-integer n
    try:
        list(take([1, 2, 3], 1.5))
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    # Generator consumption and remaining items
    class Counter:
        """Simple mutable counter used for generator tests."""

        def __init__(self) -> None:
            self.count = 0

    counter = Counter()

    def counted():
        for i in range(5):
            counter.count += 1
            yield i

    gen = counted()

    assert list(take(gen, 3)) == [0, 1, 2]
    assert counter.count == 3

    # Generator should still have remaining items
    assert next(gen) == 3

    # Returns an iterator, not a list
    assert not isinstance(take([1, 2], 1), list)

    # Infinite generator
    def infinite():
        while True:
            yield 1

    assert list(take(infinite(), 5)) == [1, 1, 1, 1, 1]

    print("All tests passed.")