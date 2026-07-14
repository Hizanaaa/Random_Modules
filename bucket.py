"""
Reviewer Note
    - Implemented bucket() as a single-pass iterable grouping helper that 
        consumes the input exactly once, making it safe for generators and 
        other streaming iterables.
    - Returns a regular dict rather than a defaultdict, preventing unexpected
        mutation when accessing missing keys.
    - Preserves item order within each bucket by appending elements in 
        encounter order.
    - Preserves key insertion order, relying on Python 3.7+ dictionary 
        ordering guarantees, so keys appear in the order they are first encountered.
    - Does not perform custom validation on keys; any unhashable key naturally 
        raises Python's built-in TypeError.
    - Exceptions raised by the supplied key callable are intentionally allowed 
        to propagate unchanged, matching normal Python behavior.

Test Gaps
    - Performance on extremely large datasets (millions of elements) was not benchmarked.
    - No concurrency or thread-safety tests were included, as the function is intended 
        for normal sequential iteration.
    - Custom hashable object keys were not explicitly tested, although they are handled 
        by standard dictionary semantics.
    - Infinite generators were not tested because the function necessarily consumes 
        the iterable until exhaustion.
    - Memory usage under very large buckets was not measured beyond normal functional 
        correctness.
"""

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K")


def bucket(
    iterable: Iterable[T],
    key: Callable[[T], K],
) -> dict[K, list[T]]:
    """
    Group items from iterable into buckets keyed by key(item).

    Returns a regular dict mapping each distinct key value to a list
    of items that produced it, in first-encountered order. Keys appear
    in the order their first item was seen. The iterable is consumed
    exactly once (single-pass, generator-safe). Empty iterable yields
    an empty dict.
    """
    result: dict[K, list[T]] = {}

    for item in iterable:
        k = key(item)
        result.setdefault(k, []).append(item)

    return result


if __name__ == "__main__":

    # Basic odd/even
    assert bucket([1, 2, 3, 4, 5], lambda x: x % 2) == {
        1: [1, 3, 5],
        0: [2, 4],
    }

    # First-encountered order within bucket
    assert bucket(
        [3, 1, 4, 1, 5, 9, 2, 6, 5, 3],
        lambda x: x % 2,
    ) == {
        1: [3, 1, 1, 5, 9, 5, 3],
        0: [4, 2, 6],
    }

    # First-seen key ordering
    result = bucket([2, 1, 2, 1], lambda x: x)
    assert list(result.keys()) == [2, 1]

    # String key
    assert bucket(
        ["apple", "ant", "banana", "cherry"],
        lambda s: s[0],
    ) == {
        "a": ["apple", "ant"],
        "b": ["banana"],
        "c": ["cherry"],
    }

    # Empty input
    assert bucket([], lambda x: x) == {}

    # All items in one bucket
    assert bucket(
        [2, 4, 6, 8],
        lambda x: "even",
    ) == {
        "even": [2, 4, 6, 8]
    }

    # Result type is plain dict
    assert type(bucket([1], lambda x: x)) is dict

    # Generator single-pass
    consumed = {"count": 0}

    def counting_generator():
        for i in range(5):
            consumed["count"] += 1
            yield i

    g = counting_generator()
    bucket(g, lambda x: x % 2)
    assert consumed["count"] == 5

    # Generator stays exhausted
    assert next(g, None) is None

    # Key callable exception propagates
    class BoomError(Exception):
        pass

    def boom_key(x):
        if x == 2:
            raise BoomError("boom")
        return x

    try:
        bucket([0, 1, 2, 3], boom_key)
        assert False
    except BoomError:
        pass

    # Unhashable key raises TypeError
    try:
        bucket([[1, 2], [3, 4]], lambda x: x)
        assert False
    except TypeError:
        pass

    print("All tests passed.")