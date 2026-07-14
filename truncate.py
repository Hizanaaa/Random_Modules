"""
Reviewer Note
-------------
Design choices:

1. max_length INCLUDES the suffix.
   Example:
       truncate("Hello World!", 8)
   returns "Hello…", not "Hello Wo…".
   The final returned string (including suffix) is constrained to
   max_length characters or fewer.

2. If max_length < len(suffix), this implementation returns the suffix
   truncated to max_length characters rather than raising ValueError.
   This keeps the function total and predictable for all non-negative
   lengths and avoids forcing callers to special-case small values.

3. Empty string input returns an empty string unchanged.
   None is considered a programming error and raises TypeError because
   the contract explicitly accepts str.

4. When breakonwords=True, truncation searches for the last whitespace
   character within the available content budget
   (max_length - len(suffix)).
   If no whitespace exists in that range, the implementation falls back
   to a hard character cut.

5. Trailing whitespace at the cut point is removed before appending the
   suffix so results look like:
       "Hello…"
   rather than:
       "Hello …"

6. truncate_middle keeps both a head and tail whenever possible.
   When available space after the suffix is at least 2, it is split
   between head and tail (tail gets available // 2, head gets the rest).
   When available < 2 (i.e. 0 or 1), tail_len would be 0, and
   text[-0:] returns the entire string rather than an empty slice — a
   Python gotcha. The implementation degrades to a plain truncate in
   this case to avoid that bug and keep the result well-formed.

Test gaps:
- Unicode grapheme clusters (e.g. emoji sequences, combining marks)
  were not tested. Length calculations use Python character counts.
- Extremely large strings were not performance-tested because the
  implementation is straightforward and uses standard slicing/search.
- Non-space word boundaries (language-specific tokenization rules)
  were not tested; only Python whitespace handling is used.
"""

from typing import Final


def truncate(
    text: str,
    max_length: int,
    suffix: str = "…",
    breakonwords: bool = True,
) -> str:
    """
    Truncate text to max_length characters including the suffix.

    If text already fits, it is returned unchanged. When
    breakonwords=True, truncation prefers the last whitespace boundary
    that fits. If no such boundary exists, a hard character cut is used.

    Args:
        text: Input text.
        max_length: Maximum allowed length including suffix.
        suffix: Truncation marker.
        breakonwords: Whether to prefer word-boundary cuts.

    Returns:
        The truncated string.

    Raises:
        TypeError: If text is not a string.
        ValueError: If max_length is negative.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if max_length < 0:
        raise ValueError("max_length must be non-negative")

    if text == "":
        return ""

    if max_length < len(suffix):
        return suffix[:max_length]

    if len(text) <= max_length:
        return text

    available = max_length - len(suffix)

    if available <= 0:
        return suffix[:max_length]

    if not breakonwords:
        return text[:available] + suffix

    candidate = text[:available]
    cut_index = candidate.rfind(" ")

    if cut_index == -1:
        return candidate + suffix

    trimmed = candidate[:cut_index].rstrip()

    if not trimmed:
        return candidate + suffix

    return trimmed + suffix


def truncate_middle(
    text: str,
    max_length: int,
    suffix: str = "…",
) -> str:
    """
    Keep the beginning and end of a string and replace the middle.

    The returned string length equals max_length whenever truncation
    occurs and max_length is at least the suffix length.

    Args:
        text: Input text.
        max_length: Maximum allowed length including suffix.
        suffix: Replacement marker inserted in the middle.

    Returns:
        The original string if it already fits, otherwise a middle-
        truncated version.

    Raises:
        TypeError: If text is not a string.
        ValueError: If max_length is negative.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    if max_length < 0:
        raise ValueError("max_length must be non-negative")

    if text == "":
        return ""

    if max_length < len(suffix):
        return suffix[:max_length]

    if len(text) <= max_length:
        return text

    available = max_length - len(suffix)

    if available < 2:
        return truncate(
            text=text,
            max_length=max_length,
            suffix=suffix,
            breakonwords=False,
        )

    tail_len = available // 2
    head_len = available - tail_len

    head = text[:head_len]
    tail = text[-tail_len:]

    return head + suffix + tail


if __name__ == "__main__":
    # Shorter than max_length
    assert truncate("Hello", 10) == "Hello"

    # Exactly max_length
    assert truncate("Hello", 5) == "Hello"

    # Word boundary truncation
    result = truncate("The quick brown fox jumps", 15)
    assert result == "The quick…"
    assert len(result) <= 15

    # No whitespace in cut range, hard-cut fallback
    assert truncate("Supercalifragilistic", 10) == "Supercali…"

    # Hard-cut mode
    assert truncate("Hello World", 8, breakonwords=False) == "Hello W…"

    # Custom suffix length math
    assert truncate("Hello World", 8, suffix="...") == "Hello..."
    assert len(truncate("Hello World", 8, suffix="...")) == 8

    # Empty string
    assert truncate("", 10) == ""

    # max_length < len(suffix)
    assert truncate("Hello", 2, suffix="...") == ".."

    # trailing whitespace at the cut point is trimmed before suffix. 
    assert truncate("Hello world", 7) == "Hello…"
    assert truncate("Hello world", 7)[-2] != " ", "space must be stripped before suffix"

    # truncate_middle happy path
    text = "path/to/some/deeply/nested/file.txt"
    result = truncate_middle(text, 25)
    assert len(result) == 25
    assert result.startswith("path/to/")
    assert result.endswith("file.txt")
    assert "…" in result

    # truncate_middle small max_length — degradation boundary.
    result = truncate_middle("abcdefghijk", 1, suffix="…")
    assert result == "…"

    # available=1: tail_len would be 0, triggering text[-0:] = full string.
    result = truncate_middle("abcdefghijk", 2, suffix="…")
    assert result == "a…"
    assert len(result) == 2
    
    # available=2: first non-degrade case (head=1, tail=1). Confirm split works.
    result = truncate_middle("abcdefghijk", 3, suffix="…")
    assert result == "a…k"
    assert len(result) == 3

    print("All tests passed.")