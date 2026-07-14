"""
Reviewer Note
=============

Semantics
---------
1. The function clamps a numeric value into the closed interval [lo, hi].
2. If lo > hi, a ValueError is raised. The function deliberately refuses to
   silently swap the bounds because that would hide a caller bug.
3. A singleton interval (lo == hi) is valid. Every input clamps to that value.
4. Only int, float, and bool are accepted. Non-numeric inputs such as str,
   None, list, dict, and tuple raise TypeError. Bool is accepted because it is
   an int subclass.
5. When the value is already within the interval, its original type is
   preserved. Boundary results return lo or hi exactly as supplied by the
   caller.
6. The implementation intentionally uses max(lo, min(value, hi)) after input
   validation rather than hand-rolled comparisons.

Test gaps
---------
1. NaN handling is intentionally not guaranteed. float("nan") does not compare
   normally, making min() and max() order-dependent. Callers should filter NaN
   values before calling clamp().
"""

from typing import Union

Number = Union[int, float]


def clamp(value: Number, lo: Number, hi: Number) -> Number:
    """Clamp value into the closed interval [lo, hi].

    Returns lo when value < lo, hi when value > hi, value otherwise.

    Preserves the input type -- clamp(0.5, 0, 1) returns a float, clamp(5, 0, 10)
    returns an int.

    Raises ValueError if lo > hi (the interval is empty). Raises TypeError
    on non-numeric args (rejects str, None, list -- but accepts int, float, bool).
    """
    for arg in (value, lo, hi):
        if not isinstance(arg, (int, float)):
            raise TypeError("All arguments must be numeric.")
    if lo > hi:
        raise ValueError("lo must not be greater than hi.")
    return max(lo, min(value, hi))


if __name__ == "__main__":
    assert clamp(5, 0, 10) == 5
    assert clamp(-3, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10

    result = clamp(0.5, 0, 1)
    assert result == 0.5
    assert type(result) is float

    result = clamp(5, 0, 10)
    assert type(result) is int

    assert clamp(-5, -10, -1) == -5
    assert clamp(-15, -10, -1) == -10

    assert clamp(5, 3, 3) == 3
    assert clamp(3, 3, 3) == 3
    assert clamp(1, 3, 3) == 3

    try:
        clamp(5, 10, 3)
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    try:
        clamp("5", 0, 10)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    try:
        clamp(5, None, 10)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    try:
        clamp(5, 0, [10])
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    print("All tests passed.")