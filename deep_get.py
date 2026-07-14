"""
Reviewer Note
=============

Purpose
-------
Safely retrieves a value from a nested dictionary using a separator-based
path string. If any intermediate step cannot be traversed, the supplied
default value is returned instead of raising an exception.

Semantic Decisions
------------------
1. Missing keys and None-valued intermediate keys are treated the same.
   - If traversal cannot continue because an intermediate value is None,
     the function returns the default value.
   - This matches common configuration and JSON access patterns where
     either case means the requested path is unavailable.

2. Only dictionaries are traversed.
   - Lists, tuples, sets, strings and other container types are never
     indexed into.
   - They may be returned if they are the final resolved value.

3. Empty path returns the original object unchanged.
   - This is considered a successful lookup rather than an error.

4. Custom separators are supported through the sep argument.

5. sep must be a single non-empty string.
   - Empty strings, multi-character strings and non-string values raise
     TypeError.

6. path must be a string.
   - Pre-split lists or tuples of keys are intentionally unsupported.

7. Falsy terminal values are preserved.
   - Values such as 0, False, "" and [] are returned exactly as stored.
   - The default value is only returned when traversal fails.

8. obj may be any type.
   - Non-dictionary objects immediately return the default for non-empty
     paths.

Test Gaps
---------
1. Dictionary subclasses with custom lookup behaviour are not exercised.
2. Extremely deep recursion-like nesting beyond normal practical usage
   is not benchmarked.
3. Future support for list indexing is intentionally excluded and would
   require additional tests.
"""

from __future__ import annotations

from typing import Any


def deep_get(
    obj: Any,
    path: str,
    default: Any = None,
    sep: str = ".",
) -> Any:
    """
    Safely retrieve a nested value from a dictionary.

    Args:
        obj:
            Object to traverse.
        path:
            Separator-delimited path.
        default:
            Value returned if traversal fails.
        sep:
            Separator used in the path.

    Returns:
        The resolved value if the walk succeeds, otherwise default.

    Raises:
        TypeError:
            If path is not a string or sep is not a single non-empty
            string.
    """
    if not isinstance(path, str):
        raise TypeError("path must be a string")

    if not isinstance(sep, str) or len(sep) != 1:
        raise TypeError("sep must be a single non-empty string")

    if path == "":
        return obj

    current = obj

    for key in path.split(sep):
        if current is None or not isinstance(current, dict):
            return default

        if key not in current:
            return default

        current = current[key]

    return current


if __name__ == "__main__":

    # Basic lookup
    assert deep_get({"a": {"b": {"c": 1}}}, "a.b.c") == 1

    # Missing leaf
    assert deep_get({"a": {"b": {}}}, "a.b.c", default="x") == "x"

    # Missing intermediate
    assert deep_get({"a": {}}, "a.b.c", default="x") == "x"

    # Missing root
    assert deep_get({}, "a.b.c", default="x") == "x"

    # None intermediate
    assert deep_get({"a": None}, "a.b", default="x") == "x"

    # Falsy terminal values
    assert deep_get({"a": {"b": 0}}, "a.b", default="x") == 0
    assert deep_get({"a": {"b": False}}, "a.b", default="x") is False
    assert deep_get({"a": {"b": ""}}, "a.b", default="x") == ""

    # Empty path
    obj = {"a": 1}
    assert deep_get(obj, "") is obj
    assert deep_get(obj, "", default="x") is obj

    # Single key
    assert deep_get({"a": 1}, "a") == 1

    # Custom separator
    assert deep_get({"a": {"b": 1}}, "a/b", sep="/") == 1

    # Lists are not traversed
    sample = {"a": [1, 2, 3]}
    assert deep_get(sample, "a.0", default="x") == "x"
    assert deep_get(sample, "a") == [1, 2, 3]

    # Non-dict root
    assert deep_get(None, "a", default="x") == "x"
    assert deep_get(42, "a", default="x") == "x"
    assert deep_get("hello", "a", default="x") == "x"

    # Seven-level nesting
    nested = {
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": {
                            "f": {
                                "g": 99
                            }
                        }
                    }
                }
            }
        }
    }

    assert deep_get(nested, "a.b.c.d.e.f.g") == 99

    # path must be string
    try:
        deep_get({}, ["a", "b"])  # type: ignore[arg-type]
        assert False
    except TypeError as exc:
        assert type(exc) is TypeError

    # Empty separator
    try:
        deep_get({}, "a.b", sep="")
        assert False
    except TypeError as exc:
        assert type(exc) is TypeError

    # Multi-character separator
    try:
        deep_get({}, "a..b", sep="..")
        assert False
    except TypeError as exc:
        assert type(exc) is TypeError

    # Default default
    assert deep_get({}, "a.b") is None

    print("All tests passed.")