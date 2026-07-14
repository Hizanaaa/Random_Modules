"""
Reviewer Note
=============

This module formats a count together with either a singular or plural
noun.

Semantics
---------
1. Only `n == 1` uses the singular noun.
   - Every other integer (including 0 and negatives) uses the plural.

2. Default plural is `noun + "s"`.
   - Irregular plurals should be supplied explicitly by the caller.

3. `plural=None` enables automatic `noun + "s"`.
   - An empty string is treated literally and is not replaced.

4. Numbers are embedded exactly as provided.
   - No thousands separator or formatting is applied.

5. `n` must be an integer.
   - Non-integer values raise TypeError.

6. Words are used verbatim.
   - No trimming, capitalisation changes, or inflection beyond the
     optional default "s" suffix.

Test gaps
---------
1. Boolean values were not tested.
   - Since bool subclasses int, behaviour follows Python integer rules.

2. Empty noun strings were not tested.
   - The helper intentionally leaves validation to callers.

3. Unicode-specific nouns were not tested.
   - Behaviour is expected to be identical because strings are used
     verbatim.
"""

from typing import Optional


def pluralize(noun: str, n: int, plural: Optional[str] = None) -> str:
    """
    Return a singular or plural noun prefixed with its count.

    Args:
        noun: Singular noun.
        n: Count.
        plural: Explicit plural form. If None, defaults to noun + "s".

    Returns:
        Formatted string containing the count and chosen noun.

    Raises:
        TypeError: If n is not an integer.
    """
    if not isinstance(n, int):
        raise TypeError("n must be an integer")

    word = noun if n == 1 else (noun + "s" if plural is None else plural)
    return f"{n} {word}"


if __name__ == "__main__":
    assert pluralize("file", 1) == "1 file"

    assert pluralize("file", 2) == "2 files"
    assert pluralize("dog", 5) == "5 dogs"

    assert pluralize("file", 0) == "0 files"
    assert pluralize("file", -1) == "-1 files"

    assert pluralize("mouse", 3, "mice") == "3 mice"
    assert pluralize("child", 4, "children") == "4 children"

    assert pluralize("mouse", 1, "mice") == "1 mouse"

    assert pluralize("File", 2) == "2 Files"
    assert pluralize("PDF", 3) == "3 PDFs"

    assert pluralize("row", 1000) == "1000 rows"

    try:
        pluralize("file", 1.5)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    try:
        pluralize("file", "3")
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    try:
        pluralize("file", None)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    assert pluralize("data", 2, "") == "2 "

    assert pluralize("file", 1).count(" ") == 1

    print("All tests passed.")