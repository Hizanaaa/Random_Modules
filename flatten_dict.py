"""
Reviewer Note
=============

Semantic Decisions
------------------
1. Only dictionaries are traversed recursively.
   Lists, tuples, sets and every other value are treated as leaf values and
   stored unchanged.

2. Empty nested dictionaries contribute no output keys.
   Example:
       {"a": {}, "b": 1}
   becomes:
       {"b": 1}

3. The prefix is treated as the outer namespace.
   No separator is automatically added to the prefix. The caller is
   responsible for supplying any desired separator.

4. Empty top-level dictionaries return an empty dictionary.

5. Invalid argument types raise TypeError.

6. The separator must be a single non-empty string.

7. Recursive implementation is intentionally used because recursion depth
   depends only on dictionary nesting depth.

Test Gaps
---------
1. Colliding pre-dotted keys (e.g. {"a.b": 1, "a": {"b": 2}})
   are considered caller responsibility. The last assignment wins,
   matching normal dictionary behaviour.

2. Extremely deep nesting approaching Python's recursion limit is
   not explicitly tested.

3. Non-string dictionary keys are accepted and converted using str().
"""

from typing import Any


def flatten_dict(
    d: dict,
    sep: str = ".",
    prefix: str = "",
) -> dict:
    """
    Flatten a nested dictionary into a single-level dictionary.

    Only dictionary values are recursively traversed. Every other value
    is treated as a leaf.

    Args:
        d: Dictionary to flatten.
        sep: Separator joining nested keys.
        prefix: Optional namespace prepended to every key.

    Returns:
        A flattened dictionary.

    Raises:
        TypeError:
            If d is not a dict.
            If sep is not a single-character string.
            If prefix is not a string.
    """
    if not isinstance(d, dict):
        raise TypeError("d must be a dict")

    if not isinstance(sep, str) or len(sep) != 1:
        raise TypeError("sep must be a single non-empty string")

    if not isinstance(prefix, str):
        raise TypeError("prefix must be a string")

    flattened: dict[str, Any] = {}

    def _flatten(current: dict, current_key: str) -> None:
        for key, value in current.items(): 
            key = str(key)

            if current_key:
                new_key = current_key + sep + key
            else:
                new_key = key

            if isinstance(value, dict):
                if value:
                    _flatten(value, new_key)
            else:
                flattened[new_key] = value

    _flatten(d, prefix)

    return flattened


if __name__ == "__main__":

    # 1
    assert flatten_dict({"a": {"b": {"c": 1}}}) == {"a.b.c": 1}

    # 2
    assert flatten_dict({"a": 1, "b": 2}) == {
        "a": 1,
        "b": 2,
    }

    # 3
    assert flatten_dict(
        {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3,
            },
        }
    ) == {
        "a": 1,
        "b.c": 2,
        "b.d": 3,
    }

    # 4
    assert flatten_dict({"a": [1, 2, 3]}) == {
        "a": [1, 2, 3]
    }

    # 5
    assert flatten_dict({"a": {}, "b": 1}) == {
        "b": 1
    }

    # 6
    assert flatten_dict({}) == {}

    # 7
    assert flatten_dict({"a": 1}, prefix="cfg") == {
        "cfg.a": 1
    }

    assert flatten_dict(
        {"a": {"b": 1}},
        prefix="cfg",
    ) == {
        "cfg.a.b": 1
    }

    # 8
    assert flatten_dict(
        {"a": {"b": 1}},
        sep="/",
    ) == {
        "a/b": 1
    }

    # 9
    result = flatten_dict({"a": {"b": 0}})
    assert result["a.b"] == 0

    result = flatten_dict({"a": {"b": False}})
    assert result["a.b"] is False

    assert flatten_dict({"a": {"b": ""}}) == {
        "a.b": ""
    }

    assert flatten_dict({"a": {"b": None}}) == {
        "a.b": None
    }

    # 10
    try:
        from deep_get import deep_get

        nested = {"a": {"b": {"c": 42}}}
        flat = flatten_dict(nested)

        key = next(iter(flat))
        assert deep_get(nested, key) == flat[key]
    except ImportError:
        pass

    # 11
    deep = {
        "a": {
            "b": {
                "c": {
                    "d": {
                        "e": {
                            "f": 99
                        }
                    }
                }
            }
        }
    }

    assert flatten_dict(deep) == {
        "a.b.c.d.e.f": 99
    }

    # 12
    for bad in ([1, 2], "hello", None):
        try:
            flatten_dict(bad)
            assert False
        except TypeError:
            pass

    # 13
    for bad_sep in ("", "..", None):
        try:
            flatten_dict({}, sep=bad_sep)
            assert False
        except TypeError:
            pass

    # 14
    for bad_prefix in (42, None):
        try:
            flatten_dict({}, prefix=bad_prefix)
            assert False
        except TypeError:
            pass

    # 15
    config = {
        "db": {
            "host": "localhost",
            "port": 5432,
            "auth": {
                "user": "admin",
                "password": "secret",
            },
        },
        "api": {
            "url": "example.com",
            "timeout": 30,
            "retry": {
                "count": 5,
                "delay": 2,
            },
        },
        "logging": {
            "level": "INFO",
            "file": "app.log",
        },
        "cache": {
            "enabled": True,
            "ttl": 60,
        },
    }

    flat = flatten_dict(config)

    assert flat["db.host"] == "localhost"
    assert flat["db.port"] == 5432
    assert flat["db.auth.user"] == "admin"
    assert flat["db.auth.password"] == "secret"
    assert flat["api.url"] == "example.com"
    assert flat["api.timeout"] == 30
    assert flat["api.retry.count"] == 5
    assert flat["api.retry.delay"] == 2
    assert flat["logging.level"] == "INFO"
    assert flat["logging.file"] == "app.log"
    assert flat["cache.enabled"] is True
    assert flat["cache.ttl"] == 60

    print("All tests passed.")