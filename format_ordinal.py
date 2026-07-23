"""
Reviewer Note
=============

Module: format_ordinal.py

Semantic Decisions
------------------
1. Teens rule
   -----------
   The last two digits determine whether the suffix is "th".

   Numbers ending in 11, 12 or 13 always use "th", including:

       11 -> 11th
       12 -> 12th
       13 -> 13th
       111 -> 111th
       112 -> 112th
       113 -> 113th
       211 -> 211th

   This prevents the common bug of checking only the final digit.

2. Last-digit rule
   ----------------
   Outside the teens, the final digit determines the suffix.

       21 -> 21st
       22 -> 22nd
       23 -> 23rd
       24 -> 24th
       100 -> 100th
       101 -> 101st

3. Zero
   ----
   Zero formats as "0th".

4. Negative numbers
   ----------------
   Negative integers preserve their sign while determining the suffix
   from the absolute value.

       -1 -> -1st
       -11 -> -11th
       -22 -> -22nd

5. bool rejection
   --------------
   bool is intentionally rejected even though bool is a subclass of int.

   This prevents surprising output such as:

       True -> "1st"

6. Float rejection
   ----------------
   Floats are rejected because ordinals represent integer positions.

       1.0
       1.5

   both raise TypeError.

7. Large integers
   --------------
   Arbitrarily large integers are supported naturally by Python.

Test gaps
---------
1. Localization is intentionally out of scope. This helper formats
   English ordinals only.

2. Unicode digits are not supported because the function accepts only
   Python integers.

3. Formatting options such as commas or locale-aware separators belong
   in higher-level formatting utilities.
"""


def format_ordinal(n: int) -> str:
    """
    Format an integer as an English ordinal string.

    Raises:
        TypeError:
            If n is not an int or if n is a bool.
    """
    if isinstance(n, bool):
        raise TypeError("n must be an int, not bool")

    if not isinstance(n, int):
        raise TypeError("n must be an int")

    abs_n = abs(n)

    if abs_n % 100 in (11, 12, 13):
        suffix = "th"
    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(abs_n % 10, "th")

    return f"{n}{suffix}"


if __name__ == "__main__":

    # 1-4

    assert format_ordinal(1) == "1st"
    assert format_ordinal(2) == "2nd"
    assert format_ordinal(3) == "3rd"
    assert format_ordinal(4) == "4th"

    # 5-10

    for i in range(5, 11):
        assert format_ordinal(i) == f"{i}th"

    # Teens

    for i in range(11, 20):
        assert format_ordinal(i) == f"{i}th"

    # Twenties

    assert format_ordinal(20) == "20th"
    assert format_ordinal(21) == "21st"
    assert format_ordinal(22) == "22nd"
    assert format_ordinal(23) == "23rd"
    assert format_ordinal(24) == "24th"

    # Hundreds

    assert format_ordinal(100) == "100th"
    assert format_ordinal(101) == "101st"
    assert format_ordinal(102) == "102nd"
    assert format_ordinal(103) == "103rd"

    # Tail teens

    assert format_ordinal(111) == "111th"
    assert format_ordinal(112) == "112th"
    assert format_ordinal(113) == "113th"

    assert format_ordinal(211) == "211th"
    assert format_ordinal(212) == "212th"
    assert format_ordinal(213) == "213th"

    # Zero

    assert format_ordinal(0) == "0th"

    # Negatives

    assert format_ordinal(-1) == "-1st"
    assert format_ordinal(-11) == "-11th"
    assert format_ordinal(-22) == "-22nd"
    assert format_ordinal(-113) == "-113th"

    # Large numbers

    assert format_ordinal(10**18) == "1000000000000000000th"
    assert format_ordinal(10**18 + 1) == "1000000000000000001st"

    # bool rejection

    for value in (True, False):
        try:
            format_ordinal(value)
            raise AssertionError("Expected TypeError")
        except TypeError as exc:
            assert type(exc) is TypeError

    # Float rejection

    for value in (1.0, 1.5):
        try:
            format_ordinal(value)
            raise AssertionError("Expected TypeError")
        except TypeError as exc:
            assert type(exc) is TypeError

    # Non-numeric rejection

    for value in ("1", None, [1]):
        try:
            format_ordinal(value)
            raise AssertionError("Expected TypeError")
        except TypeError as exc:
            assert type(exc) is TypeError

    print("All tests passed.")