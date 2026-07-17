"""
Reviewer Note
=============

Module: format_number.py

Purpose
-------
Format integers and floating-point numbers using a configurable thousands
separator while supporting fixed decimal precision for display.

Semantic Decisions
------------------
1. decimals=0 produces an integer-looking result with no decimal point.
   Floating-point inputs are rounded using Python's built-in round()
   before formatting.

2. decimals>0 always renders exactly that many decimal places, including
   trailing zeros. This is intended for display and column alignment.

3. Values requiring rounding use Python's default rounding behaviour via
   standard formatting.

4. Negative numbers always use a leading minus sign.

5. bool values are explicitly rejected even though bool is a subclass of
   int. Displaying True as "1" or False as "0" is considered a semantic
   error for this helper.

6. The thousands separator must be a single non-empty character.

7. Negative zero is normalised to 0 so user-facing output never displays
   "-0" or "-0.00". This normalisation is applied AFTER rounding to the
   requested precision, since a value that is not exactly 0 (e.g. -0.001)
   can still round to zero at a given number of decimals (e.g. -0.001
   rounded to 2 decimals is 0.00, not -0.00).

8. Very large integers are supported through Python's arbitrary-precision
   integer implementation.

9. decimals=0 rounds using Python's built-in round(), which uses
   round-half-to-even ("banker's rounding") rather than round-half-up.
   For example, round(2.5) == 2 and round(1234.5) == 1234. This is
   standard Python behaviour, not a bug, but callers expecting
   round-half-up on exact .5 values should be aware of it.

Test Gaps
---------
1. Locale-specific formatting (decimal separators other than ".") is not
   supported.

2. Scientific notation inputs are not explicitly tested.

3. Extremely large floating-point values depend on Python's formatter.

4. Round-half-to-even behaviour on exact .5 values (see Semantic Decision 9)
   is not exhaustively tested; only cases that happen to round in the
   "intuitive" direction are covered.
"""


def format_number(
    n: int | float,
    decimals: int = 0,
    sep: str = ",",
) -> str:
    """
    Format a number with a thousands separator.

    Args:
        n: Integer or floating-point number.
        decimals: Number of decimal places to display.
        sep: Thousands separator character.

    Returns:
        A formatted string.

    Raises:
        TypeError:
            If n is not an int or float.
            If n is bool.
            If decimals is not a non-negative integer.
            If sep is not a single non-empty character.
    """
    if isinstance(n, bool) or not isinstance(n, (int, float)):
        raise TypeError("n must be an int or float (bool not allowed)")

    if not isinstance(decimals, int) or decimals < 0:
        raise TypeError("decimals must be a non-negative integer")

    if not isinstance(sep, str) or len(sep) != 1:
        raise TypeError("sep must be a single non-empty string")

    if decimals == 0:
        rounded = round(n)
        # int has no signed zero, so no extra normalization needed here.
        formatted = f"{rounded:,}"
    else:
        # Normalize AFTER rounding to the target precision: a value that
        # isn't exactly 0 (e.g. -0.001) can still round to zero at this
        # many decimals, and would otherwise print as "-0.00".
        if round(n, decimals) == 0:
            n = 0.0
        formatted = f"{n:,.{decimals}f}"

    if sep != ",":
        formatted = formatted.replace(",", sep)

    return formatted


if __name__ == "__main__":

    # 1
    assert format_number(1234567) == "1,234,567"

    # 2
    assert format_number(0) == "0"
    assert format_number(999) == "999"
    assert format_number(1000) == "1,000"

    # 3
    assert format_number(1234.5, 2) == "1,234.50"

    # 4
    assert format_number(1234.567, 2) == "1,234.57"

    # 5
    assert format_number(1234.7, 0) == "1,235"

    # 6
    assert format_number(-1234567) == "-1,234,567"
    assert format_number(-0.5, 2) == "-0.50"

    # 7
    assert format_number(-0.0, 2) == "0.00"

    # 8
    assert format_number(0, 2) == "0.00"

    # 9
    assert format_number(1234567, 0, sep=" ") == "1 234 567"
    assert format_number(1234567, 0, sep=".") == "1.234.567"

    # 10
    assert (
        format_number(10**20)
        == "100,000,000,000,000,000,000"
    )

    # 11
    for value in (True, False):
        try:
            format_number(value)
            assert False
        except TypeError:
            pass

    # 12
    for value in ("1234", None, [1]):
        try:
            format_number(value)
            assert False
        except TypeError:
            pass

    # 13
    try:
        format_number(1234, -1)
        assert False
    except TypeError:
        pass

    # 14
    for value in ("", None, ", "):
        try:
            format_number(1234, sep=value)
            assert False
        except TypeError:
            pass

    # 15
    assert format_number(1234.7) == "1,235"
    assert format_number(1234.2) == "1,234"
    assert format_number(999.5) == "1,000"
    assert format_number(1000000.4) == "1,000,000"

    # 16 - negative values that round to zero at the given precision must
    # not display as "-0.00" (regression test)
    assert format_number(-0.001, 2) == "0.00"
    assert format_number(-0.004, 2) == "0.00"
    assert format_number(-0.00001, 3) == "0.000"

    print("All tests passed.")