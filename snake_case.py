"""
Reviewer Note
=============

Semantics
---------
1. Conversion uses a two-pattern regular expression approach.
   The first pattern splits before an uppercase letter followed by lowercase
   letters (e.g. HTMLParser -> HTML_Parser). The second pattern splits
   between lowercase/digits and uppercase letters (e.g. firstName ->
   first_Name). This avoids the common failure where HTMLParser becomes
   h_t_m_l_parser.

2. Already snake_case input passes through unchanged after normalization.
   Examples:
       snake_case("first_name") == "first_name"
       snake_case("hello") == "hello"

3. Non-alphanumeric separators (spaces, hyphens, dots, etc.) are converted
   to underscores.

4. Leading and trailing underscores are removed.

5. Consecutive underscores are collapsed into a single underscore.

6. Digits remain attached to neighbouring words where appropriate.
   Examples:
       parse2XML -> parse2_xml
       v2Result -> v2_result
       XMLHTTPRequest -> xmlhttp_request

7. Empty strings return an empty string.

8. All-uppercase words remain a single word after conversion.
   Example:
       HTML -> html

9. Non-string inputs raise TypeError.

Features
--------
1. Converts camelCase and PascalCase identifiers to snake_case.
2. Correctly preserves acronym groups (e.g., HTMLParser → html_parser).
3. Handles consecutive uppercase letter sequences using a two-stage regex 
    approach.
4. Converts spaces, hyphens, dots, and other non-alphanumeric separators to 
    underscores.
5. Collapses repeated underscores into a single underscore.
6. Removes leading and trailing underscores.
7. Preserves numeric portions of identifiers appropriately.
8. Validates input type and raises TypeError for non-string values.
9. Uses only the Python standard library.
10. Includes comprehensive inline assertion-based tests covering normal, 
    edge, and error cases.


Test Gaps
---------
1. Unicode letters were not explicitly tested. The implementation is
   intended primarily for ASCII identifiers.

2. Boolean values were not tested because bool is not a string and follows
   the standard TypeError validation.

3. Additional punctuation combinations beyond the required separators were
   not exhaustively tested.
"""

import re


def snake_case(s: str) -> str:
    """
    Convert s from camelCase / PascalCase to snake_case.

    Handles two boundary types correctly:
      - lower->Upper: firstName -> first_name
      - Cap-run->Cap+lower: HTMLParser -> html_parser
        (i.e. keep runs of caps together, split before the last cap
        of a run when it's followed by a lowercase letter).

    Already-snake input passes through unchanged. Non-alnum separators
    (spaces, hyphens, dots) are converted to underscores. Leading and
    trailing underscores are stripped. Repeated underscores are
    collapsed to one.

    Raises:
        TypeError: If s is not a string.
    """
    if not isinstance(s, str):
        raise TypeError("s must be a string")

    if s == "":
        return ""

    # Split acronym followed by normal word.
    result = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)

    # Split lowercase/digit followed by uppercase.
    result = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", result)

    # Replace non-alphanumeric separators.
    result = re.sub(r"[^A-Za-z0-9]+", "_", result)

    # Collapse repeated underscores.
    result = re.sub(r"_+", "_", result)

    # Strip surrounding underscores.
    result = result.strip("_")

    return result.lower()


if __name__ == "__main__":
    # camelCase
    assert snake_case("firstName") == "first_name"

    # PascalCase
    assert snake_case("FirstName") == "first_name"

    # Consecutive capitals
    assert snake_case("HTMLParser") == "html_parser"
    assert snake_case("HTMLParser") != "h_t_m_l_parser"

    # Capital run in middle
    assert snake_case("parseXMLDoc") == "parse_xml_doc"

    # Capital run at beginning
    assert snake_case("XMLHTTPRequest") == "xmlhttp_request"

    # Already snake
    assert snake_case("first_name") == "first_name"
    assert snake_case("hello") == "hello"

    # Space separator
    assert snake_case("first name") == "first_name"

    # Hyphen separator
    assert snake_case("first-name") == "first_name"

    # Dot separator
    assert snake_case("first.name") == "first_name"

    # Leading underscore
    assert snake_case("_hello") == "hello"

    # Trailing underscore
    assert snake_case("hello_") == "hello"

    # Repeated underscores
    assert snake_case("hello___world") == "hello_world"

    # Empty string
    assert snake_case("") == ""

    # All capitals
    assert snake_case("HTML") == "html"

    # Digit boundaries
    assert snake_case("parse2XML") == "parse2_xml"
    assert snake_case("v2Result") == "v2_result"

    # Non-string input
    try:
        snake_case(123)
        assert False
    except Exception as exc:
        assert type(exc) is TypeError

    # Real-world sample
    assert (
        snake_case("getUserByEmailAddress")
        == "get_user_by_email_address"
    )

    print("All tests passed.")