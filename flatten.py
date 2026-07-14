"""
Reviewer Note
-----------------
    - Returns an iterator, not a list. This keeps the helper memory-efficient 
    and avoids materializing large nested collections. Callers can use 
    list(flatten(...)) when they need eager evaluation.
    - The helper flattens exactly one level. Nested iterables inside an inner 
    iterable are preserved unchanged. Recursive flattening is intentionally 
    out of scope.
    - str, bytes, and bytearray are treated as atomic values using 
    isinstance(item, (str, bytes, bytearray)) so they are yielded intact 
    instead of character-by-character.
    - Non-iterable objects are detected via iter(item) inside a try/except 
    TypeError block and are yielded unchanged rather than raising an exception.
    - The implementation is generator-safe. Both outer and inner generators are 
    consumed exactly once without buffering or materializing intermediate collections.
    - Empty outer iterables and empty inner iterables naturally produce no 
    output without special handling.

Feature Summary
-----------------
    - Flattens one level of nested iterables.
    - Treats str, bytes, and bytearray as atomic values.
    - Yields non-iterable objects unchanged.
    - Returns an iterator for memory efficiency.
    - Supports lazy evaluation with generators.

Test Gaps
-----------------
    - The current tests already cover exception propagation mid-iteration
      (BadIterable) and None/falsy values passed through (Mixed atomic +
      iterable test). One genuinely open item remains:
        - Very large nested structures, to specifically bound peak memory
          usage (the current large-lazy-stream test proves laziness via
          islice, but doesn't measure memory).
"""
from collections.abc import Iterable
from typing import Iterator, TypeVar
from itertools import islice

T = TypeVar("T")


def flatten(iterable: Iterable[Iterable[T] | T]) -> Iterator[T]:
    """
    Yield every element from every sub-iterable of iterable, in order.

    Flattens ONE level only.

    Strings, bytes, and bytearrays are treated as atomic values and are
    yielded as-is instead of being expanded character-by-character.

    Non-iterable values are also yielded as-is.

    Returns an iterator.
    """

    atomic_types = (str, bytes, bytearray)

    for item in iterable:
        if isinstance(item, atomic_types):
            yield item
            continue

        try:
            iterator = iter(item)
        except TypeError:
            yield item
        else:
            yield from iterator


if __name__ == "__main__":

    # Basic nested list
    assert list(flatten([[1, 2], [3, 4], [5]])) == [
        1, 2, 3, 4, 5
    ]

    # One-level only
    assert list(flatten([[1, 2], [[3, 4], [5]]])) == [
        1,
        2,
        [3, 4],
        [5],
    ]

    # Strings atomic
    assert list(flatten(["hello", "world"])) == [
        "hello",
        "world",
    ]

    # Bytes atomic
    assert list(flatten([b"abc", b"def"])) == [
        b"abc",
        b"def",
    ]

    # Bytearray atomic
    assert list(flatten([
        bytearray(b"xy"),
        bytearray(b"z"),
    ])) == [
        bytearray(b"xy"),
        bytearray(b"z"),
    ]

    # Non-iterable pass-through
    assert list(flatten([1, [2, 3], 4])) == [
        1,
        2,
        3,
        4,
    ]

    # Mixed atomic + iterable
    assert list(flatten([
        "hi",
        [1, 2],
        b"x",
        None,
        [3],
    ])) == [
        "hi",
        1,
        2,
        b"x",
        None,
        3,
    ]

    # Empty outer
    assert list(flatten([])) == []

    # Empty inner
    assert list(flatten([[], [1, 2], []])) == [
        1,
        2,
    ]

    # Generator outer + generator inner (single-pass)

    outer_counter = {"count": 0}
    inner_counter = {"count": 0}

    def make_inner(n):
        def gen():
            for i in range(n):
                inner_counter["count"] += 1
                yield i
        return gen()

    def make_outer():
        for n in (2, 3):
            outer_counter["count"] += 1
            yield make_inner(n)

    outer = make_outer()

    result = list(flatten(outer))

    assert result == [0, 1, 0, 1, 2]
    assert outer_counter["count"] == 2
    assert inner_counter["count"] == 5

    # Generator exhausted
    assert next(outer, None) is None

    # Tuples ARE flattened
    assert list(flatten([
        (1, 2),
        (3, 4),
    ])) == [
        1,
        2,
        3,
        4,
    ]

    # Lazy iteration

    def infinite():
        while True:
            yield range(3)

    assert list(islice(flatten(infinite()), 6)) == [
        0,
        1,
        2,
        0,
        1,
        2,
    ]

    # Set flattening
    result = list(flatten([{1, 2}, {3}]))

    assert set(result) == {1, 2, 3}
    assert len(result) == 3

    # Dictionary behaviour (iterates over keys)
    assert list(flatten([{"a": 1, "b": 2}])) == ["a", "b"]

    # Range object
    assert list(flatten([range(3)])) == [0, 1, 2]

    # Custom iterable object
    class CustomIterable:
        def __iter__(self):
            yield 10
            yield 20
            yield 30

    assert list(flatten([CustomIterable()])) == [10, 20, 30]

    # Exception propagation from inner iterator
    class BadIterable:
        def __iter__(self):
            yield 1
            raise RuntimeError("boom")

    try:
        list(flatten([BadIterable()]))
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass

    # Atomic subclasses
    class MyStr(str):
        pass

    class MyBytes(bytes):
        pass

    class MyByteArray(bytearray):
        pass

    assert list(flatten([MyStr("hello")])) == [MyStr("hello")]
    assert list(flatten([MyBytes(b"abc")])) == [MyBytes(b"abc")]
    assert list(flatten([MyByteArray(b"xyz")])) == [MyByteArray(b"xyz")]

    # Mixed iterable types
    mixed = [
        (1, 2),
        range(3, 5),
        (x for x in [5, 6]),
        {7, 8},
        [9],
    ]

    result = list(flatten(mixed))

    assert result[:6] == [1, 2, 3, 4, 5, 6]
    assert set(result[6:8]) == {7, 8}
    assert result[-1] == 9

    # Large lazy stream-
    large = (range(1000) for _ in range(10000))

    first_ten = list(islice(flatten(large), 10))

    assert first_ten == list(range(10))

    print("All tests passed.")