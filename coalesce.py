"""
Reviewer Note
=============

Semantics
---------
1. Only None is skipped. Falsy values are considered present.
   - coalesce(0, 5) returns 0, not 5.
   - coalesce("", "fallback") returns "", not "fallback".
   - coalesce(False, True) returns False, not True.
2. If no positional arguments are supplied, the function returns default.
3. If every positional argument is None, the function returns default.
4. The first non-None positional value always wins.
5. The implementation intentionally uses next() with a generator expression for
   a concise, Pythonic implementation.
6. default=None is a valid caller choice. No sentinel object is needed because
   None is the intended default result.

Test gaps
---------
1. No performance or memory benchmarking was performed with extremely large
   argument lists. Functional behaviour was verified only.
"""


def coalesce(*values, default=None):
    """Return the first argument in values that is not None.

    If every value is None (or no values were passed), returns default.

    Note the sharp semantic: ONLY None is skipped. Falsy values (0, "", [], False)
    are considered "present" and are returned.
    """
    return next((value for value in values if value is not None), default)


if __name__ == "__main__":
    assert coalesce(None, "a") == "a"
    assert coalesce(None, "a", "b") == "a"

    assert coalesce(0, 5) == 0
    assert coalesce(0, 5) != 5

    assert coalesce("", "fallback") == ""
    assert coalesce("", "fallback") != "fallback"

    assert coalesce([], [1, 2]) == []

    assert coalesce(False, True) is False

    assert coalesce(None, None, None) is None
    assert coalesce(None, None, default="x") == "x"

    assert coalesce() is None
    assert coalesce(default=42) == 42

    assert coalesce(None, default=None) is None

    assert coalesce("only") == "only"
    assert coalesce(None) is None

    assert coalesce(None, None, "x", "y") == "x"

    print("All tests passed.")