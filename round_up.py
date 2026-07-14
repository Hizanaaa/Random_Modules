"""
Reviewer Note
=============

Semantics
---------
1. Rounding is performed toward positive infinity. This is the key design
   decision. For example, round_up(-3, 5) == 0 rather than -5. The
   implementation uses ceiling-division logic so negative values are handled
   correctly.

2. Exact multiples pass through unchanged.
   Examples:
       round_up(20, 5) == 20
       round_up(-10, 5) == -10
       round_up(0, 5) == 0

3. A step less than or equal to zero is rejected by raising ValueError.
   This is a deliberate design choice because rounding to a non-positive
   multiple is undefined for this helper.

4. Both arguments must be integers. Non-int values raise TypeError.
   This avoids ambiguity with floating-point inputs.

5. The return type is always int. Since bool is a subclass of int, bool
   inputs are accepted naturally without special handling.

6. No special-case optimization exists for step == 1. The mathematical
   formula already returns the correct result without extra branches.

   
Features
--------
1. Rounds integers upward to the nearest multiple of a positive step.
2. Correctly handles both positive and negative integers using ceiling division.
3. Preserves exact multiples without modification.
4. Performs input validation with explicit TypeError and ValueError exceptions.
5. Supports arbitrarily large integers using Python's built-in integer arithmetic.
6. Returns an integer for all valid inputs.
7. Uses only the Python standard library.
8. Includes comprehensive inline assertion-based tests covering normal, 
    boundary, and error cases.

Test Gaps
---------
1. Bool behaviour was not explicitly tested.
   Since bool is an int subclass, True and False are accepted naturally.

2. Extremely large negative values beyond the provided arbitrary-precision
   test were not exhaustively exercised because Python integers already
   support arbitrary precision.

3. Randomized property-based testing was not performed. The supplied tests
   cover the required edge cases and representative inputs.
"""


def round_up(value: int, step: int) -> int:
    """
    Round value UP to the nearest multiple of step.

    Rounding is "toward positive infinity" -- for negatives, this means
    toward zero (e.g. round_up(-3, 5) == 0, not -5). If value is
    already an exact multiple of step, it's returned unchanged.

    Raises:
        TypeError: If either argument is not an int.
        ValueError: If step is less than or equal to zero.
    """
    if not isinstance(value, int):
        raise TypeError("value must be an int")

    if not isinstance(step, int):
        raise TypeError("step must be an int")

    if step <= 0:
        raise ValueError("step must be greater than zero")

    return -(-value // step) * step


if __name__ == "__main__":
    # Basic positive
    assert round_up(23, 5) == 25

    # Exact multiple positive
    assert round_up(20, 5) == 20

    # Zero
    assert round_up(0, 5) == 0

    # Negative rounds toward zero
    assert round_up(-3, 5) == 0
    assert round_up(-3, 5) != -5

    # Negative exact multiple
    assert round_up(-10, 5) == -10

    # Negative past a multiple
    assert round_up(-7, 5) == -5

    # Large step, small value
    assert round_up(3, 100) == 100

    # Step of 1
    assert round_up(42, 1) == 42

    # step == 0
    try:
        round_up(10, 0)
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # step < 0
    try:
        round_up(10, -5)
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Non-int value
    try:
        round_up(1.5, 5)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    # Non-int step
    try:
        round_up(10, 2.5)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    # Very large value
    assert round_up(10**20 + 7, 100) == 10**20 + 100

    print("All tests passed.")