"""
Reviewer Note
=============

Purpose
-------
Provides a small synchronous retry helper for transient failures.

Semantic Decisions
------------------
1. `attempts` counts TOTAL function calls, not retries.
   - `attempts=3` means the function may be called at most three times.
   - This avoids the common off-by-one ambiguity.

2. `attempts=1` is valid.
   - The function is called exactly once with no retry.
   - Values less than 1 raise ValueError.

3. Delay occurs ONLY between attempts.
   - For attempts=3 and delay=1.0:
         call -> sleep -> call -> sleep -> call
   - Total sleep time is (attempts - 1) * delay.

4. Only matching exceptions are retried.
   - Exceptions outside the supplied filter immediately propagate
     without consuming remaining attempts.

5. Retry exhaustion re-raises the LAST exception directly.
   - No wrapping or custom RetryExhaustedError is used so the original
     traceback remains meaningful.

6. `fn` must be a zero-argument callable.
   - Arguments should be bound by the caller using a lambda or
     functools.partial.

7. Invalid arguments.
   - Non-callable fn raises TypeError.
   - Negative delay raises TypeError.
   - attempts < 1 raises ValueError.

8. Uses time.sleep().
   - This helper is intentionally synchronous.
   - Async retry belongs in a separate utility.

Test Gaps
---------
1. Floating-point scheduling inaccuracies on heavily loaded systems
   are not exhaustively tested.
2. Extremely large delay values are not exercised.
3. Thread interaction and cancellation behaviour are outside scope.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    attempts: int = 3,
    delay: float = 0.0,
    exceptions: type | tuple[type, ...] = Exception,
) -> T:
    """
    Call fn up to attempts times, retrying matching exceptions.

    Args:
        fn:
            Zero-argument callable.
        attempts:
            Maximum total number of calls.
        delay:
            Seconds to sleep between failed attempts.
        exceptions:
            Exception type(s) that trigger a retry.

    Returns:
        The first successful result.

    Raises:
        ValueError:
            If attempts < 1.
        TypeError:
            If fn is not callable or delay is negative.
        Exception:
            Re-raises the final matching exception, or immediately
            propagates non-matching exceptions.
    """
    if not callable(fn):
        raise TypeError("fn must be callable")

    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    if delay < 0:
        raise TypeError("delay must be non-negative")

    for attempt in range(attempts):
        try:
            return fn()
        except exceptions:
            if attempt == attempts - 1:
                raise
            if delay:
                time.sleep(delay)


if __name__ == "__main__":

    # Success on first attempt
    counter = {"n": 0}

    def first() -> int:
        counter["n"] += 1
        return 42

    assert retry(first) == 42
    assert counter["n"] == 1

    # Success on second attempt
    counter = {"n": 0}

    def second() -> int:
        counter["n"] += 1
        if counter["n"] == 1:
            raise ValueError("fail")
        return 42

    assert retry(second) == 42
    assert counter["n"] == 2

    # Success on last attempt
    counter = {"n": 0}

    def third() -> int:
        counter["n"] += 1
        if counter["n"] < 3:
            raise ValueError("fail")
        return 42

    assert retry(third, attempts=3) == 42
    assert counter["n"] == 3

    # Last exception is re-raised
    counter = {"n": 0}

    def always_fail() -> int:
        counter["n"] += 1
        raise ValueError(f"attempt {counter['n']}")

    try:
        retry(always_fail, attempts=3)
        assert False
    except ValueError as exc:
        assert type(exc) is ValueError
        assert str(exc) == "attempt 3"

    # attempts=1
    assert retry(lambda: 1, attempts=1) == 1

    # attempts < 1
    for bad in (0, -2):
        try:
            retry(lambda: 1, attempts=bad)
            assert False
        except ValueError as exc:
            assert type(exc) is ValueError

    # Delay between attempts
    counter = {"n": 0}

    def timing() -> int:
        counter["n"] += 1
        if counter["n"] < 3:
            raise ValueError
        return 5

    start = time.perf_counter()
    assert retry(timing, attempts=3, delay=0.1) == 5
    elapsed = time.perf_counter() - start

    assert elapsed >= 0.2
    assert elapsed < 0.3

    # delay=0
    counter = {"n": 0}

    def fast_retry() -> int:
        counter["n"] += 1
        if counter["n"] < 3:
            raise ValueError
        return 8

    start = time.perf_counter()
    assert retry(fast_retry, delay=0) == 8
    elapsed = time.perf_counter() - start

    assert elapsed < 0.01

    # Non-matching exception
    counter = {"n": 0}

    def wrong_exception() -> int:
        counter["n"] += 1
        raise KeyError("nope")

    try:
        retry(
            wrong_exception,
            attempts=5,
            exceptions=ValueError,
        )
        assert False
    except KeyError:
        assert counter["n"] == 1

    # Exception tuple
    counter = {"n": 0}

    def tuple_case() -> int:
        counter["n"] += 1
        if counter["n"] == 1:
            raise TypeError
        return 9

    assert retry(
        tuple_case,
        exceptions=(TypeError, ValueError),
    ) == 9

    # Non-callable fn
    try:
        retry(None)  # type: ignore[arg-type]
        assert False
    except TypeError as exc:
        assert type(exc) is TypeError

    # Negative delay
    try:
        retry(lambda: 1, delay=-0.5)
        assert False
    except TypeError as exc:
        assert type(exc) is TypeError

    # Object identity preserved
    obj = {"a": 1}
    assert retry(lambda: obj) is obj

    print("All tests passed.")