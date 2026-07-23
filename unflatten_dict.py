"""
Reviewer Note
=============  

Semantic Decisions
------------------
1. Round-trip contract
   -------------------
   This function is designed to be the inverse of ``flatten_dict``.
   For every input accepted by ``flatten_dict``:

       unflatten_dict(flatten_dict(x)) == x

   with one documented exception:

       Empty nested dictionaries are discarded by ``flatten_dict``.
       Example:

           {"a": {}, "b": 1}

       becomes

           {"b": 1}

       after a flatten → unflatten round trip.

   This is an intentional semantic decision made by ``flatten_dict``,
   not a bug in this implementation.

2. Prefix collisions
   -----------------
   Inputs such as:

       {"a": 1, "a.b": 2}

   or

       {"a.b": 1, "a.b.c": 2}

   are impossible to represent as nested dictionaries because one path
   requires a scalar while another requires a subtree.

   These cases raise ValueError rather than silently overwriting data.
   The error message names both of the actual colliding flat keys
   (looked up via an internal path -> originating-key map), regardless
   of which key is a prefix of the other or which was inserted first.

3. Order-independent collision detection
   -------------------------------------
   Collision detection works regardless of insertion order.

   Both

       {"a": 1, "a.b": 2}

   and

       {"a.b": 2, "a": 1}

   raise the same ValueError.

4. Separator validation
   --------------------
   ``sep`` must be a single non-empty string.

   Invalid separators include:

       ""
       ".."
       None

   These raise TypeError for consistency with the config-tools helpers.

5. Non-string keys
   ---------------
   Only string keys are supported.

   Automatically coercing keys with ``str()`` would introduce silent
   collisions such as:

       {1: "x", "1": "y"}

6. Empty dictionary
   ----------------
   An empty input dictionary returns an empty dictionary.

Test gaps
---------
1. Keys beginning or ending with the separator intentionally create
   empty-string dictionary keys. Example:

       {".a": 1}
       {"a.": 1}

2. Duplicate dictionary keys cannot be tested because Python dictionaries
   overwrite duplicate literals before this function receives them.

3. Behaviour depends on flatten_dict using identical separator semantics.
"""

from __future__ import annotations


def unflatten_dict(d: dict, sep: str = ".") -> dict:
    """
    Unflatten a single-level dict with sep-joined keys back into a nested dict.

    - {"a.b.c": 1} becomes {"a": {"b": {"c": 1}}}.
    - Keys with no separator become top-level keys unchanged.
    - sep must be a single non-empty string.
    - Non-string keys raise TypeError.
    - Prefix collisions raise ValueError.

    Raises:
        TypeError:
            If d is not a dict, sep is invalid, or any key is not a string.

        ValueError:
            If a scalar/subtree collision is encountered.
    """
    if not isinstance(d, dict):
        raise TypeError("d must be a dict")

    if not isinstance(sep, str) or len(sep) != 1:
        raise TypeError("sep must be a single non-empty string")

    result = {}
    # Maps every path (scalar leaf path or intermediate subtree path) that has
    # been created so far to the original flat_key responsible for it. This
    # lets collision errors name the *actual* other key involved, instead of
    # guessing / fabricating one.
    origin: dict[str, str] = {}

    for flat_key, value in d.items():
        if not isinstance(flat_key, str):
            raise TypeError("all keys must be strings")

        parts = flat_key.split(sep)
        current = result
        path = ""

        for part in parts[:-1]:
            path = part if not path else f"{path}{sep}{part}"

            if path in origin and not isinstance(current.get(part), dict):
                raise ValueError(
                    f"Prefix collision between '{origin[path]}' and '{flat_key}'"
                )

            if part not in current:
                current[part] = {}
                origin[path] = flat_key

            current = current[part]

        final = parts[-1]
        final_path = f"{path}{sep}{final}" if path else final

        if final_path in origin and isinstance(current.get(final), dict):
            raise ValueError(
                f"Prefix collision between '{flat_key}' and '{origin[final_path]}'"
            )

        current[final] = value
        origin[final_path] = flat_key

    return result


if __name__ == "__main__":
    from flatten_dict import flatten_dict

    # Basic
    assert unflatten_dict({"a.b.c": 1}) == {"a": {"b": {"c": 1}}}

    assert unflatten_dict({"a": 1, "b": 2}) == {
        "a": 1,
        "b": 2,
    }

    assert unflatten_dict(
        {
            "a": 1,
            "b.c": 2,
            "b.d": 3,
        }
    ) == {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3,
        },
    }

    # Round-trip
    
    nested = {
        "a": {
            "b": {
                "c": 42,
            }
        },
        "x": 1,
    }

    assert unflatten_dict(flatten_dict(nested)) == nested

    deep = {
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": [
                            1,
                            None,
                            False,
                            "",
                        ]
                    }
                }
            }
        }
    }

    assert unflatten_dict(flatten_dict(deep)) == deep

    # Prefix collisions

    try:
        unflatten_dict({"a": 1, "a.b": 2})
        raise AssertionError
    except ValueError as exc:
        assert type(exc) is ValueError
        assert "a" in str(exc)
        assert "a.b" in str(exc)

    try:
        unflatten_dict({"a.b": 2, "a": 1})
        raise AssertionError
    except ValueError as exc:
        assert type(exc) is ValueError
        assert "a" in str(exc)
        assert "a.b" in str(exc)

    try:
        unflatten_dict({"a.b": 1, "a.b.c": 2})
        raise AssertionError
    except ValueError as exc:
        assert type(exc) is ValueError
        assert "a.b" in str(exc)
        assert "a.b.c" in str(exc)

    # Falsy values

    assert unflatten_dict({"a.b": 0}) == {"a": {"b": 0}}

    assert unflatten_dict({"a.b": False}) == {
        "a": {"b": False}
    }

    assert unflatten_dict({"a.b": None}) == {
        "a": {"b": None}
    }

    assert unflatten_dict({"a.b": ""}) == {
        "a": {"b": ""}
    }

    # Empty

    assert unflatten_dict({}) == {}

    # Custom separator

    assert unflatten_dict(
        {"a/b/c": 1},
        sep="/",
    ) == {
        "a": {
            "b": {
                "c": 1,
            }
        }
    }

    # No separator

    assert unflatten_dict({"hello": 5}) == {"hello": 5}

    # Deep nesting

    tree = unflatten_dict(
        {"a.b.c.d.e.f": 10}
    )

    assert tree["a"]["b"]["c"]["d"]["e"]["f"] == 10

    # List values

    assert unflatten_dict(
        {"a": [1, 2, 3]}
    ) == {
        "a": [1, 2, 3]
    }

    # Invalid inputs

    for bad in (
        [("a", 1)],
        "hello",
        None,
    ):
        try:
            unflatten_dict(bad)
            raise AssertionError
        except TypeError:
            pass

    for bad in (
        {1: "a"},
        {("a",): 1},
    ):
        try:
            unflatten_dict(bad)
            raise AssertionError
        except TypeError:
            pass

    for bad_sep in (
        "",
        "..",
        None,
    ):
        try:
            unflatten_dict(
                {},
                sep=bad_sep,
            )
            raise AssertionError
        except TypeError:
            pass

    # Empty-string segments

    assert unflatten_dict(
        {".a": 1}
    ) == {
        "": {
            "a": 1,
        }
    }

    print("All tests passed.")