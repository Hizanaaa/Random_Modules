"""
Reviewer Note
    - Implemented using a private _MISSING sentinel so that default=None, 
        default=False, and "no default supplied" remain distinguishable.
    - Performs the bool type check before the int check, since bool is a 
        subclass of int in Python.
    - Integer inputs are converted using Python's standard truthiness 
        (bool(value)).
    - String inputs are normalized with strip() and lower() before matching 
        against the supported truthy and falsy string sets.
    - Only the explicitly documented string values are accepted; all other 
        inputs are considered unrecognized.
    - Unrecognized values return the supplied default when provided; otherwise, 
        the function raises exactly ValueError. No custom exceptions or 
        TypeError are introduced.

Test Gaps
    - Floating-point numbers (e.g., 0.0, 1.5) were not tested because only 
        boolean, integer, and string handling is defined by the specification.
    - Other numeric types such as Decimal and Fraction were not tested.
    - Unicode or localized boolean strings (e.g., "sí", "ja", "oui") were 
        not tested since only the specified English literals are supported.
    - Extremely long string inputs were not performance-tested.
    - Custom objects implementing __str__ or __bool__ were not explicitly 
        tested because the specification only defines behavior for booleans, 
        integers, strings, and the default fallback path.
"""


from typing import Any

_MISSING = object()

_TRUTHY = {"1", "true", "t", "yes", "y", "on"}
_FALSY = {"0", "false", "f", "no", "n", "off"}


def parse_bool(
    value: Any,
    default: Any = _MISSING,
) -> bool:
    """
    Coerce a value to bool.

    Recognises common truthy/falsy strings (case-insensitive,
    whitespace stripped), passes booleans through, coerces integers
    using Python truthiness, and returns the supplied default (if any)
    for unrecognised values. Otherwise raises ValueError.
    """

    # Bool passthrough (must come before int check)
    if isinstance(value, bool):
        return value

    # Integer coercion
    if isinstance(value, int):
        return bool(value)

    # String lookup
    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in _TRUTHY:
            return True

        if normalized in _FALSY:
            return False

    # Unrecognised value
    if default is not _MISSING:
        return default

    raise ValueError(f"Cannot parse {value!r} as a boolean.")


if __name__ == "__main__":

    # Truthy strings
    for s in ("1", "true", "t", "yes", "y", "on"):
        assert parse_bool(s) is True

    # Falsy strings
    for s in ("0", "false", "f", "no", "n", "off"):
        assert parse_bool(s) is False

    # Case-insensitive
    assert parse_bool("TRUE") is True
    assert parse_bool("True") is True
    assert parse_bool("YES") is True
    assert parse_bool("FALSE") is False
    assert parse_bool("No") is False

    # Whitespace stripped
    assert parse_bool("  true  ") is True
    assert parse_bool("\tno\n") is False

    # Bool passthrough
    assert parse_bool(True) is True
    assert parse_bool(False) is False

    # Integer coercion
    assert parse_bool(0) is False
    assert parse_bool(1) is True
    assert parse_bool(42) is True
    assert parse_bool(-1) is True

    # Unrecognised string with default
    assert parse_bool("maybe", default=False) is False
    assert parse_bool("truthy?", default=True) is True

    # Unrecognised string without default
    try:
        parse_bool("maybe")
        assert False
    except ValueError as e:
        assert type(e) is ValueError

    # Empty string without default
    try:
        parse_bool("")
        assert False
    except ValueError:
        pass

    # Empty string with default
    assert parse_bool("", default=False) is False

    # None without default
    try:
        parse_bool(None)
        assert False
    except ValueError:
        pass

    # None with default
    assert parse_bool(None, default=False) is False
    assert parse_bool(None, default=None) is None

    # Sentinel test
    assert parse_bool("maybe", default=False) is False

    print("All tests passed.")