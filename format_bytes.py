"""
Reviewer Note
-------------
Semantics pinned:

1. Default mode is binary (1024).
   Units:
       B, KiB, MiB, GiB, TiB, PiB, EiB, ZiB, YiB

2. Decimal mode uses:
       B, KB, MB, GB, TB, PB, EB, ZB, YB

3. Bytes are always shown as integers.
   Example:
       500 -> "500 B"

4. Negative values are supported.
   Example:
       -2048 -> "-2.00 KiB"

5. Zero formats as:
       "0 B"

6. Unit selection uses the largest unit whose value is >= 1.

7. precision=0 removes decimal places cleanly.

8. Unit ladder extends beyond PiB so very large values continue
   scaling naturally rather than being capped.

Test Gaps
---------
Not explicitly tested:

- Arbitrarily huge integers.
- Non-integer inputs.

The public contract requires integer byte counts.
"""

from typing import Final


def format_bytes(
    n: int,
    binary: bool = True,
    precision: int = 2,
) -> str:
    """
    Format an integer byte count as a human-readable string.

    binary=True:
        B, KiB, MiB, GiB, TiB, PiB, EiB, ZiB, YiB

    binary=False:
        B, KB, MB, GB, TB, PB, EB, ZB, YB
    """

    if binary:
        base = 1024
        units = [
            "B",
            "KiB",
            "MiB",
            "GiB",
            "TiB",
            "PiB",
            "EiB",
            "ZiB",
            "YiB",
        ]
    else:
        base = 1000
        units = [
            "B",
            "KB",
            "MB",
            "GB",
            "TB",
            "PB",
            "EB",
            "ZB",
            "YB",
        ]

    sign = "-" if n < 0 else ""

    value = abs(n)

    unit_index = 0

    while (
        value >= base
        and unit_index < len(units) - 1
    ):
        value /= base
        unit_index += 1

    unit = units[unit_index]

    if unit == "B":
        return f"{sign}{int(value)} B"

    if precision == 0:
        return f"{sign}{value:.0f} {unit}"

    return f"{sign}{value:.{precision}f} {unit}"


# Zero
assert format_bytes(0) == "0 B"

# Sub-KiB
assert format_bytes(500) == "500 B"

# Boundary
assert format_bytes(1023) == "1023 B"
assert format_bytes(1024) == "1.00 KiB"

# MiB
assert format_bytes(1048576) == "1.00 MiB"

# Mid-range
assert format_bytes(1536) == "1.50 KiB"

# GiB
assert format_bytes(1073741824) == "1.00 GiB"

# Decimal mode
assert format_bytes(1000, binary=False) == "1.00 KB"

# Decimal boundary
assert format_bytes(999, binary=False) == "999 B"
assert format_bytes(1000, binary=False) == "1.00 KB"

# Negative KiB
assert format_bytes(-2048) == "-2.00 KiB"

# Negative bytes
assert format_bytes(-500) == "-500 B"

# precision=0
assert format_bytes(1536, precision=0) == "2 KiB"

# precision=4
assert format_bytes(1536, precision=4) == "1.5000 KiB"

# PiB
assert format_bytes(1125899906842624) == "1.00 PiB"

# Beyond PiB
large_value = 1125899906842624 * 2000
result = format_bytes(large_value)

assert any(
    unit in result
    for unit in ("PiB", "EiB", "ZiB", "YiB")
)

print("All tests passed.")