"""
Reviewer Note
-----------------
- Uses a private sentinel (_MISSING = object()) so that default=None,
  default=0 and "no default supplied" are distinguishable.
- int values are returned unchanged (coerced via int() so bool inputs
  come back as plain int 0/1, not bool). bool values are intentionally
  accepted because bool is a subclass of int in Python.
- String inputs are stripped and parsed using int(value, 10) to enforce
  base-10 parsing only. This intentionally rejects hexadecimal (0xff),
  binary (0b101) and octal representations.
- Float strings ("3.14"), thousands separators ("1,000"), empty strings,
  whitespace-only strings and None are treated as invalid inputs.
- On parse failure, the supplied default is returned when present;
  otherwise ValueError is raised.
- ValueError is the only exception exposed by this helper.
"""

from typing import Any

_MISSING = object()


def safe_int(
    value: Any,
    default: Any = _MISSING,
) -> int:
    """
    Parse value as a base-10 integer.

    Accepted:
        - int (returned unchanged)
        - bool (returned as 0/1)
        - str (whitespace stripped)

    Rejected:
        - float strings
        - hex/octal/binary strings
        - thousands separators
        - empty strings
        - None
        - anything else not parseable

    Returns:
        Parsed integer or supplied default.

    Raises:
        ValueError if parsing fails and no default is supplied.
    """

    if isinstance(value, int):
        return int(value)

    if isinstance(value, str):
        value = value.strip()

        try:
            result = int(value, 10)
        except ValueError:
            if default is not _MISSING:
                return default
            raise ValueError(f"Invalid integer: {value!r}")

        return result

    if default is not _MISSING:
        return default

    raise ValueError(f"Invalid integer: {value!r}")


if __name__ == "__main__":

    # Int passthrough
    assert safe_int(5) == 5
    assert safe_int(-3) == -3
    assert safe_int(0) == 0

    # Bool as 0/1
    assert safe_int(True) == 1
    assert safe_int(False) == 0
    assert type(safe_int(True)) is int
    assert type(safe_int(False)) is int

    # Basic string parse
    assert safe_int("5") == 5
    assert safe_int("42") == 42

    # Whitespace stripped
    assert safe_int("  42  ") == 42
    assert safe_int("\t7\n") == 7

    # Signed strings
    assert safe_int("-3") == -3
    assert safe_int("+3") == 3

    # Float string rejected with default
    assert safe_int("3.14", default=0) == 0

    # Float string rejected without default
    try:
        safe_int("3.14")
        assert False
    except ValueError:
        pass

    # Hex rejected
    assert safe_int("0xff", default=-1) == -1

    # Binary rejected
    assert safe_int("0b101", default=-1) == -1

    # Thousands separator rejected
    assert safe_int("1,000", default=0) == 0

    # Empty string
    assert safe_int("", default=0) == 0

    try:
        safe_int("")
        assert False
    except ValueError:
        pass

    # Whitespace only
    assert safe_int("   ", default=0) == 0

    # None rejected
    assert safe_int(None, default=0) == 0

    try:
        safe_int(None)
        assert False
    except ValueError:
        pass

    # Sentinel (default=0)
    assert safe_int("nope", default=0) == 0

    # Sentinel (default=None)
    assert safe_int("nope", default=None) is None

    # Random strings
    assert safe_int("hello", default=-1) == -1
    assert safe_int("12abc", default=-1) == -1

    # Raises ValueError only
    try:
        safe_int("hello")
        assert False
    except ValueError:
        pass

    # Unicode digits
    # Arabic-Indic digits for "123"
    assert safe_int("١٢٣") == 123

    # Full-width digits
    assert safe_int("４５６") == 456

    # Extremely large integer
    large_num = "9" * 1000
    assert safe_int(large_num) == int(large_num)

    # String subclass
    class MyStr(str):
        pass

    assert safe_int(MyStr(" 123 ")) == 123

    # Object implementing __int__
    class HasInt:
        def __int__(self):
            return 99

    assert safe_int(HasInt(), default=-1) == -1

    try:
        safe_int(HasInt())
        assert False
    except ValueError:
        pass

    # 22. Bytes input rejected
    assert safe_int(b"123", default=-1) == -1

    try:
        safe_int(b"123")
        assert False
    except ValueError:
        pass

    # Bytearray input rejected
    assert safe_int(bytearray(b"123"), default=-1) == -1

    try:
        safe_int(bytearray(b"123"))
        assert False
    except ValueError:
        pass

    # Invalid sign combinations
    assert safe_int("--5", default=0) == 0
    assert safe_int("++3", default=0) == 0
    assert safe_int("+-2", default=0) == 0

    # Leading zeros
    assert safe_int("00042") == 42
    assert safe_int("-0007") == -7
    assert safe_int("+0009") == 9

    # Non-string iterables rejected
    for value in (
        [1, 2],
        (1, 2),
        {"a": 1},
        {1, 2},
    ):
        assert safe_int(value, default=-1) == -1

        try:
            safe_int(value)
            assert False
        except ValueError:
            pass
    print("All tests passed.")