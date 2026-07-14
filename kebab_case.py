"""
Reviewer Note
=============

This module converts strings into kebab-case by delegating all parsing and
word-boundary detection to the sibling snake_case module.

Semantic decisions
------------------
1. Delegates directly to snake_case().
   This implementation intentionally reuses the snake_case conversion logic
   instead of duplicating the regular expressions. This keeps a single
   source of truth for detecting word boundaries (including consecutive
   capital letters such as HTMLParser). Any future fixes to snake_case are
   automatically inherited by kebab_case.

2. The output is simply the snake_case result with underscores replaced by
   hyphens.

3. All edge cases handled by snake_case are inherited automatically,
   including:
   - camelCase
   - PascalCase
   - consecutive capital letters
   - mixed separators
   - repeated separators
   - leading/trailing separators
   - digit boundaries

4. Empty strings return an empty string.

5. Already-kebab-case strings remain unchanged.

6. Inputs consisting only of separators return an empty string.

7. Non-string inputs raise TypeError through delegation to snake_case.

Test gaps
---------
1. Unicode casing behaviour depends entirely on snake_case.
2. Performance on extremely large strings was not benchmarked.
3. Behaviour is intentionally coupled to snake_case; changes there will be
   reflected here automatically.
"""

from snake_case import snake_case


def kebab_case(s: str) -> str:
    """
    Convert a string to kebab-case.

    This function delegates parsing and normalization to snake_case() and
    replaces underscores with hyphens.

    Args:
        s: Input string.

    Returns:
        The kebab-case representation of the input.

    Raises:
        TypeError: If s is not a string.
    """
    return snake_case(s).replace("_", "-")


if __name__ == "__main__":

    # Basic camelCase
    assert kebab_case("firstName") == "first-name"

    # PascalCase
    assert kebab_case("FirstName") == "first-name"

    # Consecutive capitals
    assert kebab_case("HTMLParser") == "html-parser"

    # Capital run in middle
    assert kebab_case("parseXMLDoc") == "parse-xml-doc"

    # Underscore separator
    assert kebab_case("first_name") == "first-name"

    # Space separator
    assert kebab_case("hello world") == "hello-world"

    # Dot separator
    assert kebab_case("first.name") == "first-name"

    # Already kebab-case
    assert kebab_case("first-name") == "first-name"

    # Mixed separators
    assert kebab_case("foo_bar-baz.qux") == "foo-bar-baz-qux"

    # Leading separator stripped
    assert kebab_case("-hello-world") == "hello-world"

    # Trailing separator stripped
    assert kebab_case("hello-world-") == "hello-world"

    # Repeated separators collapse
    assert kebab_case("hello---world") == "hello-world"

    # Empty string
    assert kebab_case("") == ""

    # All separators
    assert kebab_case("---") == ""

    # Delegation contract
    s = "getUserByEmailAddress"
    assert kebab_case(s) == snake_case(s).replace("_", "-")

    # Non-string raises TypeError
    try:
        kebab_case(123)  # type: ignore[arg-type]
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    # Real-world sample
    assert (
        kebab_case("getUserByEmailAddress")
        == "get-user-by-email-address"
    )

    print("All tests passed.")