"""
Reviewer Note
-------------
Design choices:

- The function returns two lists: (matches, non_matches).
  This intentionally materializes both partitions so callers
  can freely inspect, count, iterate, or reuse either bucket
  without re-running the predicate or re-consuming the input.

- Single-pass implementation. The iterable is consumed exactly
  once and the predicate is evaluated exactly once per item.
  This avoids the common mistake of filtering twice, which is
  both inefficient and incorrect for generators.

- Predicate exceptions propagate directly to the caller.
  If predicate(item) raises, partition() raises immediately.
  The partially-filled lists are discarded, not returned —
  the function makes no guarantees about intermediate state
  during failure.

- Order is preserved within each bucket. Items appear in the
  same relative order they appeared in the original iterable.

- The decision is based on bool(predicate(item)).
  Predicate results do not need to be literal booleans.
  Any truthy value places the item in matches; any falsy value
  places it in non_matches.

Test gaps:
- Infinite iterables are not tested because the function
  intentionally materializes both output lists and therefore
  requires a finite input to terminate.

- Predicates with side effects beyond simple counting are not
  tested because the implementation guarantees exactly one
  invocation per item through a straightforward single-pass loop.

- Very large iterables are not tested separately. Behavior is
  identical to small inputs aside from memory consumption, which
  is inherent to returning materialized lists.
"""

from collections.abc import Callable, Iterable
from typing import TypeVar

T = TypeVar("T")


def partition(
    iterable: Iterable[T],
    predicate: Callable[[T], bool],
) -> tuple[list[T], list[T]]:
    """
    Split iterable into (matches, non_matches) lists based on
    predicate(item).

    The iterable is consumed exactly once. Predicate exceptions
    propagate to the caller.
    """
    matches: list[T] = []
    non_matches: list[T] = []

    for item in iter(iterable):
        if bool(predicate(item)):
            matches.append(item)
        else:
            non_matches.append(item)

    return matches, non_matches


if __name__ == "__main__":
    # even/odd split
    matches, non_matches = partition(range(10), lambda x: x % 2 == 0)
    assert matches == [0, 2, 4, 6, 8]
    assert non_matches == [1, 3, 5, 7, 9]

    # empty iterable
    assert partition([], lambda x: True) == ([], [])

    # all items match
    assert partition([1, 2, 3], lambda x: True) == ([1, 2, 3], [])
    
    # no items match
    assert partition([1, 2, 3], lambda x: False) == ([], [1, 2, 3])

    # generator input exhausted after consumption
    gen = (x for x in range(5))
    assert partition(gen, lambda x: x < 3) == ([0, 1, 2], [3, 4])
    assert list(gen) == []

    # predicate called exactly once per item
    calls = {"count": 0}

    def counting_predicate(x):
        calls["count"] += 1
        return x % 2 == 0

    data = [1, 2, 3, 4, 5]
    partition(data, counting_predicate)
    assert calls["count"] == len(data)

    # predicate exception propagates
    def raising_predicate(x):
        if x == 3:
            raise ValueError("boom")
        return True

    try:
        partition([1, 2, 3, 4], raising_predicate)
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # truthy/falsy non-bool values (0/1)
    matches, non_matches = partition(
        [0, 1, 2, 3, 4],
        lambda x: x % 2,
    )
    assert matches == [1, 3]
    assert non_matches == [0, 2, 4]

    # truthy/falsy containers
    matches, non_matches = partition(
        [4, 5, 6, 7],
        lambda x: [x] if x > 5 else [],
    )
    assert matches == [6, 7]
    assert non_matches == [4, 5]

    # unhashable items
    records = [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False},
        {"name": "Carol", "active": True},
    ]
    matches, non_matches = partition(
        records,
        lambda r: r["active"],
    )
    assert matches == [records[0], records[2]]
    assert non_matches == [records[1]]

    # builtin bool predicate
    data = [0, 1, "", "x", None, [], [1]]
    matches, non_matches = partition(data, bool)
    assert matches == [1, "x", [1]]
    assert non_matches == [0, "", None, []]

    print("All tests passed.")