"""
slugify.py

A small utility for turning arbitrary text into URL-safe / filename-safe
slugs using only the Python standard library.
"""

from __future__ import annotations

import re
import unicodedata


def slugify(
    text: str,
    separator: str = "-",
    max_length: int | None = None,
    lowercase: bool = True,
) -> str:
    """
    Turn arbitrary text into a URL-safe / filename-safe slug.

    Lowercases (configurable), strips diacritics, replaces any run
    of non-alphanumeric chars with separator, trims leading/trailing
    separators, optionally caps total length.

    Returns:
        A slug string, or '' if nothing slug-able remains.

    Examples:
        >>> slugify("Hello, World!")
        'hello-world'

        >>> slugify("Café résumé")
        'cafe-resume'

        >>> slugify("Hello World", separator="_")
        'hello_world'

        >>> slugify("Hello, World!", separator="")
        'helloworld'
    """
    if not text:
        return ""

    # Strip diacritics using Unicode normalization.
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        ch for ch in normalized
        if not unicodedata.combining(ch)
    )

    # Keep ASCII only. Non-Latin scripts collapse away.
    ascii_text = stripped.encode("ascii", "ignore").decode("ascii")

    if lowercase:
        ascii_text = ascii_text.lower()

    if separator == "":
        slug = re.sub(r"[^A-Za-z0-9]+", "", ascii_text)
    else:
        slug = re.sub(r"[^A-Za-z0-9]+", separator, ascii_text)
        slug = slug.strip(separator)

    if max_length is not None:
        slug = slug[:max_length]

        if separator:
            slug = slug.rstrip(separator)

    return slug


if __name__ == "__main__":
    # 1. Basic happy path
    assert slugify("Hello, World!") == "hello-world"

    # 2. Diacritic strip
    assert slugify("Café résumé") == "cafe-resume"

    # 3. Custom separator
    assert slugify("Hello World", separator="_") == "hello_world"

    # 4. Separator runs collapse
    assert slugify("a   b---c") == "a-b-c"

    # 5. Leading/trailing strip
    assert slugify("---hello---") == "hello"

    # 6. lowercase=False
    assert slugify("HelloWorld", lowercase=False) == "HelloWorld"

    # 7. max_length cap
    result = slugify("the quick brown fox", max_length=15)
    assert len(result) <= 15
    assert not result.endswith("-")

    # 8. max_length lands on separator
    assert slugify("aaa bbb ccc", max_length=4) == "aaa"

    # 9. Empty input
    assert slugify("") == ""

    # 10. Only punctuation
    assert slugify("!!!---???") == ""

    # 11. Non-Latin script
    assert slugify("Привет, мир!") == ""

    # 12. separator="" collapse
    assert slugify("Hello, World!", separator="") == "helloworld"

    print("All tests passed!")
