"""
Reviewer Note
=============

Provides a reusable helper for masking the middle portion of sensitive
display strings while preserving the original displayed length.

Semantic notes
--------------
1. Masking is length-preserving. Every masked character is replaced by
   exactly one ``mask_char`` so the output length always matches the input
   length. This intentionally does not collapse masked regions into a fixed
   number of characters.
2. If ``keep_start + keep_end >= len(text)``, the original text is returned
   unchanged. There is nothing left to mask, and callers need not special-case
   short inputs.
3. An empty string returns an empty string. Degenerate inputs are handled
   without raising exceptions.
4. ``mask_char`` must be exactly one character. An empty string or a
   multi-character string raises ``ValueError``. This is the only
   ``ValueError`` raised by this function.
5. ``keep_start`` and ``keep_end`` count Python characters (Unicode code
   points), not bytes. The implementation uses normal string slicing and
   ``len()``.
6. Negative ``keep_start`` or ``keep_end`` values are clamped to ``0`` rather
   than raising an exception.

Test gaps
---------
- Did not test every possible Unicode edge case such as combining characters,
  zero-width joiners, or grapheme clusters. The implementation follows Python's
  documented code-point semantics.
- Did not benchmark very large strings since the function performs only simple
  slicing and string multiplication.
- Did not test every possible one-character Unicode value for ``mask_char``;
  representative ASCII masking characters were used.
"""

from typing import Final


def mask(
    text: str,
    keep_start: int = 2,
    keep_end: int = 2,
    mask_char: str = "*",
) -> str:
    """
    Mask the middle of a string while preserving its displayed length.

    Characters at the beginning and end of the string are preserved according
    to ``keep_start`` and ``keep_end``. The remaining middle characters are
    replaced one-for-one with ``mask_char``.

    Args:
        text: The string to mask.
        keep_start: Number of leading characters to preserve. Negative values
            are treated as zero.
        keep_end: Number of trailing characters to preserve. Negative values
            are treated as zero.
        mask_char: Single character used for masking.

    Returns:
        A masked string with the same length as the input.

    Raises:
        ValueError: If ``mask_char`` is not exactly one character.
    """
    if len(mask_char) != 1:
        raise ValueError("mask_char must be exactly one character")

    keep_start = max(0, keep_start)
    keep_end = max(0, keep_end)

    text_length: Final[int] = len(text)

    if text_length == 0:
        return ""

    if keep_start + keep_end >= text_length:
        return text

    masked_length = text_length - keep_start - keep_end

    return (
        text[:keep_start]
        + (mask_char * masked_length)
        + text[text_length - keep_end :]
    )


if __name__ == "__main__":
    # Default behaviour
    assert mask("ABCDE1234F") == "AB******4F"

    # Custom keep amounts
    assert mask("9876543210", 4, 2) == "9876****10"

    # Length preservation
    assert len(mask("ABCDEFGHIJ")) == len("ABCDEFGHIJ")

    # Custom mask character
    assert mask("9876543210", 4, 2, mask_char="#") == "9876####10"

    # keep_start + keep_end == len(text)
    assert mask("ABCD", 2, 2) == "ABCD"

    # keep_start + keep_end > len(text)
    assert mask("ABC", 2, 2) == "ABC"

    # Empty string
    assert mask("") == ""

    # Single character
    assert mask("X") == "X"

    # Multi-character mask_char
    try:
        mask("ABCDEFGHIJ", 2, 2, mask_char="XX")
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # Empty mask_char
    try:
        mask("ABCDEFGHIJ", 2, 2, mask_char="")
        assert False, "Expected ValueError"
    except ValueError:
        pass

    # Unicode counted as code points
    unicode_result = mask("café-1234", 2, 2)
    assert unicode_result == "ca*****34"
    assert len(unicode_result) == len("café-1234") == 9

    # Negative keep_start clamped to 0
    assert mask("ABCDEFGHIJ", -1, 2) == "********IJ"

    # Negative keep_end clamped to 0
    assert mask("ABCDEFGHIJ", 2, -1) == "AB********"

    # Both keep amounts zero
    assert mask("ABCDEFGHIJ", 0, 0) == "**********"

    # One-sided masking
    assert mask("ABCDEFGHIJ", 0, 4) == "******GHIJ"

    print("All tests passed.")