"""
Reviewer Note
=============
Semantics
---------
1. Produces lowerCamelCase, not UpperCamelCase.
   The first segment remains lowercase while every subsequent
   segment is title-cased.

2. Splits on underscores, hyphens, dots, and whitespace.
   Consecutive separators are treated as one and empty segments
   are discarded.

3. Leading and trailing separators are ignored.
   Inputs such as "_hello_world_" correctly become "helloWorld".

4. All-caps segments are flattened.
   For example, "get_HTML_parser" becomes "getHtmlParser".
   This keeps the function a natural inverse of snake_case.

5. Already-camel input passes through unchanged when there are
   no separators.

6. Empty string and all-separator input both return an empty string.

7. Leading digits are preserved exactly as supplied.

8. Non-string inputs raise TypeError.

Test Gaps
---------
1. Unicode title-casing behaviour was not exhaustively tested.
2. Extremely long strings were not benchmarked.
3. Separator characters beyond the documented set were not tested.
"""

import re


def camel_case(s: str) -> str:
    """
    Convert a string to lowerCamelCase.

    Splits on underscores, hyphens, dots, and whitespace.
    The first segment remains lowercase while subsequent
    segments are title-cased. Empty segments are ignored.

    Args:
        s: Input string.

    Returns:
        The converted lowerCamelCase string.

    Raises:
        TypeError:
            If s is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("s must be a string")

    if s == "":
        return ""

    if not re.search(r"[_\-\.\s]", s):
        return s

    parts = [part for part in re.split(r"[_\-.\s]+", s) if part]

    if not parts:
        return ""

    first = parts[0].lower()
    rest = [part.capitalize() for part in parts[1:]]

    return first + "".join(rest)


def snake_case(s: str) -> str:
    """
    Minimal snake_case implementation used only for the
    required round-trip test.
    """
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


if __name__ == "__main__":
    # 1
    assert camel_case("first_name") == "firstName"

    # 2
    assert (
        camel_case("get_user_by_email_address")
        == "getUserByEmailAddress"
    )

    # 3
    assert camel_case("first_name") != "FirstName"

    # 4
    assert camel_case("first-name") == "firstName"

    # 5
    assert camel_case("first.name") == "firstName"

    # 6
    assert camel_case("first name") == "firstName"

    # 7
    assert camel_case("foo_bar-baz.qux") == "fooBarBazQux"

    # 8
    assert camel_case("foo__bar") == "fooBar"

    # 9
    assert camel_case("_hello_world") == "helloWorld"

    # 10
    assert camel_case("hello_world_") == "helloWorld"

    # 11
    assert camel_case("fooBar") == "fooBar"

    # 12
    assert camel_case("hello") == "hello"

    # 13
    assert camel_case("") == ""

    # 14
    assert camel_case("___") == ""

    # 15
    assert camel_case("get_HTML_parser") == "getHtmlParser"

    # 16
    assert (
        snake_case(camel_case("get_user_by_email"))
        == "get_user_by_email"
    )

    # 17
    try:
        camel_case(123)
        raise AssertionError("Expected TypeError")
    except TypeError as exc:
        assert type(exc) is TypeError

    # 18
    assert camel_case("parse_xml_doc") == "parseXmlDoc"

    print("All tests passed.")