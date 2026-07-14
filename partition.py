"""
Reviewer Note
=============
This module provides a single-pass helper for splitting an iterable into
matching and non-matching items according to a predicate.

Semantic decisions
------------------
1. Returns two eager lists, not lazy iterators.
   This implementation intentionally returns a tuple of two lists:
   (matches, non_matches). While itertools.tee() could be used to produce
   lazy iterators, tee() may require unbounded buffering if the two
   iterators are consumed at different rates. Returning eager lists provides
   predictable memory behaviour and matches the common "split into two
   collections" use case.

2. Original order is preserved.
   Both the matching and non-matching lists preserve the original order
   of items from the input iterable.

3. Predicate evaluated exactly once per item.
   Each element is visited once, and pred(item) is called exactly once.

4. Truthiness determines membership.
   Any truthy predicate result places an item into the matching list;
   the result is not compared using == True.

5. Empty iterables return two empty lists.

6. The iterable is consumed exactly once, making generator inputs
   fully supported.

7. A non-callable predicate raises TypeError.

8. Exceptions raised by the predicate propagate unchanged.

9. Implementation uses a single loop with one append per item for clarity
   and efficiency.

Test gaps
---------
1. Very large iterables were not performance benchmarked.
2. Custom iterable classes with unusual iteration behaviour were not tested.
3. Thread-safety was not evaluated because the function maintains no shared
   state.
"""

from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


def partition(
    pred: Callable[[T], bool],
    iterable: Iterable[T],
) -> tuple[list[T], list[T]]:
    """
    Split iterable into two lists based on pred.

    Returns (matches, non_matches) where the first list contains items
    whose predicate value is truthy and the second contains those whose
    predicate value is falsy. Each item is visited exactly once and the
    predicate is called exactly once per item.

    Raises:
        TypeError: If pred is not callable.
    """
    if not callable(pred):
        raise TypeError("pred must be callable")

    matches: list[T] = []
    non_matches: list[T] = []

    for item in iterable:
        (matches if pred(item) else non_matches).append(item)

    return matches, non_matches


if __name__ == "__main__":

    # Basic
    assert partition(lambda x: x > 5, [3, 8, 1, 9, 4, 7]) == (
        [8, 9, 7],
        [3, 1, 4],
    )

    # Order preserved
    m, n = partition(lambda x: x % 2 == 0, [6, 1, 4, 3, 2, 5])
    assert m == [6, 4, 2]
    assert n == [1, 3, 5]

    # All match
    assert partition(lambda x: True, [1, 2, 3]) == ([1, 2, 3], [])

    # None match
    assert partition(lambda x: False, [1, 2, 3]) == ([], [1, 2, 3])

    # Empty iterable
    assert partition(lambda x: x > 0, []) == ([], [])

    # String iterable
    assert partition(str.isdigit, "a1b2c3") == (
        ["1", "2", "3"],
        ["a", "b", "c"],
    )

    # Truthy return
    assert partition(lambda x: x % 2, [1, 2, 3, 4]) == (
        [1, 3],
        [2, 4],
    )

    # Returns exactly a 2-tuple
    t = partition(lambda x: x > 0, [1, -1])
    assert type(t) is tuple
    assert len(t) == 2

    # Both halves are lists
    assert type(t[0]) is list
    assert type(t[1]) is list

    # Predicate called exactly once per item
    count = 0

    def counting_pred(x: int) -> bool:
        nonlocal_count[0] += 1
        return x > 0

    nonlocal_count = [0]
    partition(counting_pred, range(6))
    assert nonlocal_count[0] == 6

    # Non-callable predicate
    for bad in (None, 5):
        try:
            partition(bad, [1, 2, 3])  # type: ignore[arg-type]
            assert False
        except Exception as exc:
            assert type(exc) is TypeError

    # Predicate exception propagates unchanged
    try:
        partition(lambda x: 1 / 0, [1, 2, 3])
        assert False
    except Exception as exc:
        assert type(exc) is ZeroDivisionError

    # Generator input (single pass)
    visits = [0]

    def generator():
        for i in range(5):
            visits[0] += 1
            yield i

    result = partition(lambda x: x < 3, generator())
    assert result == ([0, 1, 2], [3, 4])
    assert visits[0] == 5

    print("All tests passed.")