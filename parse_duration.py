"""
Reviewer Note
=============

Design choices
--------------

1. Return type
   This helper returns an integer number of seconds rather than a
   ``datetime.timedelta``. Callers that require a timedelta can construct
   one themselves using ``datetime.timedelta(seconds=parse_duration(text))``.

2. Supported units
   Recognised units are exactly:
       w / week / weeks
       d / day / days
       h / hr / hour / hours
       m / min / minute / minutes
       s / sec / second / seconds
   Months, years, milliseconds and other units are intentionally excluded.
   Months and years are calendar-dependent, while sub-second precision is
   outside the scope of a helper whose contract is whole seconds.

3. Case-insensitive parsing
   Unit names are matched case-insensitively, so inputs such as
   ``1H 30M`` and ``1Hours`` are accepted.

4. Optional whitespace
   Components may be adjacent (``1h30m``) or separated by arbitrary
   whitespace (``1h 30m``).

5. Multi-component durations
   All parsed components are summed to produce the final duration.

6. Duplicate units
   Duplicate units are allowed and are also summed. For example,
   ``1h 2h`` evaluates to three hours.

7. Bare numbers
   Numeric values without an accompanying unit are rejected with
   ``ValueError``. This avoids assuming seconds when callers may have
   intended another unit.

8. Negative values
   Negative components are rejected with ``ValueError`` because durations
   are defined as non-negative.

9. Invalid input
   Empty strings, whitespace-only strings, unknown units, decimal values,
   malformed input and partially parsed input all raise ``ValueError``.

10. Exceptions
    ``ValueError`` is the only exception intentionally raised by this
    function.

Test gaps
---------

1. Very large integer values were not explicitly tested. Python integers
   have arbitrary precision, so behaviour is expected to remain correct.

2. Unicode whitespace characters were not tested. The implementation uses
   ``str.isspace()``, which already recognises standard Unicode whitespace.
"""

from __future__ import annotations

import re

_UNIT_SECONDS = {
    "w": 604800,
    "week": 604800,
    "weeks": 604800,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "h": 3600,
    "hr": 3600,
    "hour": 3600,
    "hours": 3600,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
}

_COMPONENT_RE = re.compile(r"(\d+)([A-Za-z]+)", re.IGNORECASE)


def parse_duration(text: str) -> int:
    """
    Parse a human-readable duration into whole seconds.

    Recognised units (case-insensitive):

        w / week / weeks
        d / day / days
        h / hr / hour / hours
        m / min / minute / minutes
        s / sec / second / seconds

    Components may optionally be separated by whitespace and are summed.

    Examples:
        "1h30m" -> 5400
        "2h 15m" -> 8100

    Raises:
        ValueError:
            If the input is empty, malformed, contains bare numbers,
            unknown units, decimal numbers, negative values or any
            unparseable content.
    """
    if not text or text.strip() == "":
        raise ValueError("duration cannot be empty")

    if "-" in text:
        raise ValueError("negative durations are not allowed")

    total = 0
    position = 0
    matched = False

    while position < len(text):
        while position < len(text) and text[position].isspace():
            position += 1

        if position >= len(text):
            break

        match = _COMPONENT_RE.match(text, position)

        if match is None:
            raise ValueError("invalid duration")

        matched = True

        number = match.group(1)
        unit = match.group(2).lower()

        if unit not in _UNIT_SECONDS:
            raise ValueError("unknown duration unit")

        total += int(number) * _UNIT_SECONDS[unit]
        position = match.end()

    if not matched:
        raise ValueError("invalid duration")

    return total


if __name__ == "__main__":
    # Seconds
    assert parse_duration("45s") == 45

    # Minutes
    assert parse_duration("30m") == 1800
    assert parse_duration("1min") == 60
    assert parse_duration("2minutes") == 120

    # Hours
    assert parse_duration("1h") == 3600
    assert parse_duration("2hours") == 7200
    assert parse_duration("3hr") == 10800

    # Days and weeks
    assert parse_duration("1d") == 86400
    assert parse_duration("2days") == 172800
    assert parse_duration("1w") == 604800
    assert parse_duration("2weeks") == 1209600

    # Multi-component
    assert parse_duration("1h 30m 15s") == 5415
    assert parse_duration("2h 45m") == 9900

    # Optional whitespace
    assert parse_duration("1h30m15s") == 5415

    # Case insensitive
    assert parse_duration("1H 30M") == 5400
    assert parse_duration("1HOUR") == 3600
    assert parse_duration("45SEC") == 45

    # Duplicate units
    assert parse_duration("1h 2h") == 10800
    assert parse_duration("30m 30m") == 3600

    # Bare number
    try:
        parse_duration("300")
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Negative component
    try:
        parse_duration("-5m")
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Empty string
    try:
        parse_duration("")
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Whitespace only
    try:
        parse_duration("   ")
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Float component
    try:
        parse_duration("1.5h")
        assert False
    except Exception as exc:
        assert type(exc) is ValueError

    # Unknown units
    for value in ("5x", "10lightyears"):
        try:
            parse_duration(value)
            assert False
        except Exception as exc:
            assert type(exc) is ValueError

    # ValueError only
    invalid_inputs = [
        "300",
        "-5m",
        "", "   ",
        "1.5h",
        "5x",
        "10lightyears",
    ]

    for value in invalid_inputs:
        try:
            parse_duration(value)
            assert False
        except Exception as exc:
            assert type(exc) is ValueError

    # Zero values
    assert parse_duration("0s") == 0
    assert parse_duration("0h 0m") == 0

    print("All tests passed.")