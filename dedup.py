"""
Reviewer Note
=============
Semantics
---------
1. Returns an iterator, not a list.
   The function is implemented as a generator so it can process
   iterables lazily without materialising the entire input. Callers
   may wrap it in list(...) when eager evaluation is desired.

2. First-seen order is preserved.
   The first occurrence of every unique key is yielded. Later
   duplicates are skipped while maintaining the original order.

3. key=None uses each item as its own key.
   Items must therefore be hashable. Unhashable items naturally
   raise TypeError from the underlying set implementation.

4. key=callable deduplicates by the returned hashable key but yields
   the ORIGINAL item, not the key. The first occurrence always wins.

5. Unhashable keys raise TypeError.
   The exception is intentionally not caught or replaced.

6. Single-pass and generator-safe.
   Every input item is consumed exactly once, making the function
   suitable for generators, iterators, and infinite sequences.

7. Exceptions raised by the key callable propagate unchanged.

Test Gaps
---------
1. Very large datasets were not benchmarked for memory or speed.
2. Custom hash implementations with unusual behaviour were not tested.
3. Infinite iterators were only verified by consuming the first value,
   not through extended iteration.
"""

from collections.abc import Callable, Hashable, Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def dedup(
    iterable: Iterable[T],
    key: Callable[[T], Hashable] | None = None,
) -> Iterator[T]:
    """
    Yield items from iterable in first-seen order, dropping later items
    whose key has already been seen.

    Args:
        iterable: Input iterable.
        key: Optional callable returning a hashable key.

    Yields:
        Original items with duplicates removed while preserving order.

    Raises:
        TypeError:
            If an item (or key result) is unhashable.
    """
    seen: set[Hashable] = set()

    for item in iterable:
        k = item if key is None else key(item)
        if k not in seen:
            seen.add(k)
            yield item


if __name__ == "__main__":
    # 1
    assert list(dedup([3, 1, 4, 1, 5, 9, 2, 6, 5, 3])) == [
        3, 1, 4, 5, 9, 2, 6
    ]

    # 2
    assert list(dedup([1, 2, 3])) == [1, 2, 3]

    # 3
    assert list(dedup([7, 7, 7, 7])) == [7]

    # 4
    assert list(dedup([])) == []

    # 5
    assert list(dedup("mississippi")) == ["m", "i", "s", "p"]

    # 6
    assert list(dedup([5, 1, 5, 2, 1, 3])) == [5, 1, 2, 3]

    # 7 & 8
    data = [
        {"id": 1, "v": "a"},
        {"id": 2, "v": "b"},
        {"id": 1, "v": "c"},
    ]
    result = list(dedup(data, key=lambda d: d["id"]))
    assert result == [
        {"id": 1, "v": "a"},
        {"id": 2, "v": "b"},
    ]
    assert result[0]["v"] == "a"

    # 9
    assert list(
        dedup(
            ["Hello", "HELLO", "hello", "World"],
            key=str.lower,
        )
    ) == ["Hello", "World"]

    # 10
    try:
        list(dedup([[1], [2]]))
        raise AssertionError("Expected TypeError")
    except TypeError as exc:
        assert type(exc) is TypeError

    # 11
    try:
        list(dedup([1, 2, 3], key=lambda x: [x]))
        raise AssertionError("Expected TypeError")
    except TypeError as exc:
        assert type(exc) is TypeError

    # 12
    counter = {"count": 0}

    def counted_gen():
        for value in [1, 2, 2, 3, 1]:
            counter["count"] += 1
            yield value

    assert list(dedup(counted_gen())) == [1, 2, 3]
    assert counter["count"] == 5

    # 13
    assert not isinstance(dedup([1, 2]), list)

    # 14
    def infinite():
        while True:
            yield 1

    assert next(dedup(infinite())) == 1

    # 15
    try:
        list(dedup([1, 2, 3], key=lambda x: 1 / 0))
        raise AssertionError("Expected ZeroDivisionError")
    except ZeroDivisionError as exc:
        assert type(exc) is ZeroDivisionError

    print("All tests passed.")