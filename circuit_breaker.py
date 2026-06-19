"""
Reviewer Note
-------------
Design choices
==============

This implementation follows the classical Nygard/Fowler circuit breaker
pattern with three states:

    closed -> open -> half_open -> closed

State transitions:

- CLOSED -> OPEN
    Triggered when consecutive failures reach failure_threshold.

- OPEN -> HALF_OPEN
    Triggered lazily during call() when cooldown_seconds has elapsed
    since the breaker entered OPEN. No background thread is used.

- HALF_OPEN -> CLOSED
    Triggered when successful probe count reaches success_threshold.

- HALF_OPEN -> OPEN
    Triggered immediately on the first probe failure.
    The cooldown timer is restarted.

Concurrency model
=================

A single threading.Lock protects all state mutations.

The protected state includes:

- breaker state
- consecutive failure count
- half-open success count
- active probe count
- opened timestamp

The wrapped function is NEVER executed while holding the lock.

Half-open semantics
===================

HALF_OPEN allows at most halfopen_max_probes concurrent probe calls.

When active probes already equal the configured limit,
additional callers receive CircuitOpenError immediately.

Probe slots are tracked using an active-probe counter and are
released in finally-style paths regardless of success or failure.

Failure predicate
=================

If failure_predicate is supplied:

    True  -> exception counts as a breaker failure
    False -> exception is re-raised without affecting breaker state

The predicate is evaluated before any counters are updated.

State change callback
=====================

on_state_change(old_state, new_state) is invoked exactly once for
real transitions.

Callbacks are dispatched outside the lock to avoid re-entrancy
deadlocks.

record_success() semantics
==========================

record_success() does NOT close an OPEN breaker.

OPEN state remains OPEN until:

- cooldown elapses and a probe succeeds, or
- reset() is called.

This avoids externally recorded successes bypassing the cooldown
safety mechanism.

Test gaps
=========

Not tested:

- Callback exceptions. Current behavior allows callback exceptions
  to propagate to the caller.

- Extremely large thread counts beyond the required concurrency test.

- System clock anomalies because monotonic clocks are expected.

- Recursive callback re-entry into the breaker.

- Long-running probes completing after another probe has already
  reopened the breaker.

These are documented but considered outside the required scope.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when a call is rejected by an OPEN or saturated HALF_OPEN breaker."""


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        halfopen_max_probes: int = 1,
        success_threshold: int = 1,
        failure_predicate: Callable[[BaseException], bool] | None = None,
        on_state_change: Callable[[str, str], None] | None = None,
        clock: Callable[[], float] | None = None,
        _sleep: Callable[[float], None] | None = None,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")

        if cooldown_seconds <= 0:
            raise ValueError("cooldown_seconds must be > 0")

        if success_threshold < 1:
            raise ValueError("success_threshold must be >= 1")

        if halfopen_max_probes < 1:
            raise ValueError("halfopen_max_probes must be >= 1")

        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._halfopen_max_probes = halfopen_max_probes
        self._success_threshold = success_threshold

        self._failure_predicate = failure_predicate
        self._on_state_change = on_state_change

        self._clock = clock or time.monotonic
        self._sleep = _sleep or time.sleep

        self._lock = threading.Lock()

        self._state = "closed"
        self._consecutive_failures = 0
        self._half_open_successes = 0
        self._active_probes = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> str:
        """Return current breaker state."""
        with self._lock:
            return self._state

    @property
    def consecutive_failures(self) -> int:
        """Expose current consecutive failure count."""
        with self._lock:
            return self._consecutive_failures

    def call(self, fn: Callable[..., T], *args, **kwargs) -> T:
        """Invoke a function through the breaker."""

        callback = None
        was_probe = False

        with self._lock:
            callback = self._maybe_transition_from_open_locked()

            if self._state == "open":
                pass_to_fn = False
            elif self._state == "half_open":
                if self._active_probes >= self._halfopen_max_probes:
                    pass_to_fn = False
                else:
                    self._active_probes += 1
                    was_probe = True
                    pass_to_fn = True
            else:
                pass_to_fn = True

        if callback:
            callback()

        if not pass_to_fn:
            raise CircuitOpenError("Circuit breaker is open")

        try:
            result = fn(*args, **kwargs)

        except BaseException as exc:
            callback = None

            with self._lock:
                if was_probe:
                    self._active_probes -= 1

                callback = self._record_failure_locked(exc)

            if callback:
                callback()

            raise

        else:
            callback = None

            with self._lock:
                if was_probe:
                    self._active_probes -= 1

                callback = self._record_success_locked()

            if callback:
                callback()

            return result

    def record_success(self) -> None:
        """Manually record a success."""

        callback = None

        with self._lock:
            callback = self._record_success_locked()

        if callback:
            callback()

    def record_failure(self, exc: BaseException | None = None) -> None:
        """Manually record a failure."""

        callback = None

        with self._lock:
            callback = self._record_failure_locked(exc)

        if callback:
            callback()

    def reset(self) -> None:
        """Force the breaker back to CLOSED."""

        callback = None

        with self._lock:
            old = self._state

            self._state = "closed"
            self._consecutive_failures = 0
            self._half_open_successes = 0
            self._active_probes = 0
            self._opened_at = None

            if old != "closed":
                callback = self._make_transition_callback(
                    old,
                    "closed",
                )

        if callback:
            callback()

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _record_success_locked(self):
        if self._state == "closed":
            self._consecutive_failures = 0
            return None

        if self._state == "open":
            return None

        self._half_open_successes += 1

        if self._half_open_successes >= self._success_threshold:
            old = self._state

            self._state = "closed"
            self._consecutive_failures = 0
            self._half_open_successes = 0
            self._opened_at = None

            return self._make_transition_callback(old, "closed")

        return None

    def _record_failure_locked(self, exc: BaseException | None):
        if exc is not None and self._failure_predicate is not None:
            if not self._failure_predicate(exc):
                return None

        if self._state == "half_open":
            old = self._state

            self._state = "open"
            self._opened_at = self._clock()
            self._half_open_successes = 0

            return self._make_transition_callback(old, "open")

        self._consecutive_failures += 1

        if (
            self._state == "closed"
            and self._consecutive_failures >= self._failure_threshold
        ):
            old = self._state

            self._state = "open"
            self._opened_at = self._clock()

            return self._make_transition_callback(old, "open")

        return None

    def _maybe_transition_from_open_locked(self):
        if self._state != "open":
            return None

        assert self._opened_at is not None

        elapsed = self._clock() - self._opened_at

        if elapsed >= self._cooldown_seconds:
            old = self._state

            self._state = "half_open"
            self._half_open_successes = 0

            return self._make_transition_callback(old, "half_open")

        return None

    def _make_transition_callback(self, old: str, new: str):
        if self._on_state_change is None:
            return None

        def callback():
            self._on_state_change(old, new)

        return callback


# ----------------------------------------------------------
# Tests
# ----------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds: float):
        self.now += seconds


if __name__ == "__main__":

    # 1 Validation

    try:
        CircuitBreaker(failure_threshold=0)
        assert False
    except ValueError:
        pass

    try:
        CircuitBreaker(cooldown_seconds=0)
        assert False
    except ValueError:
        pass

    try:
        CircuitBreaker(success_threshold=0)
        assert False
    except ValueError:
        pass

    try:
        CircuitBreaker(halfopen_max_probes=0)
        assert False
    except ValueError:
        pass

    # 2 Happy path

    cb = CircuitBreaker()

    for _ in range(100):
        assert cb.call(lambda: 123) == 123

    assert cb.state == "closed"
    assert cb.consecutive_failures == 0

    # 3 Trip open

    clock = FakeClock()
    cb = CircuitBreaker(
        failure_threshold=3,
        cooldown_seconds=10,
        clock=clock,
    )

    def fail():
        raise ValueError

    for _ in range(3):
        try:
            cb.call(fail)
        except ValueError:
            pass

    assert cb.state == "open"

    invoked = False

    def should_not_run():
        nonlocal_invoked[0] = True

    nonlocal_invoked = [False]

    try:
        cb.call(lambda: nonlocal_invoked.__setitem__(0, True))
    except CircuitOpenError:
        pass

    assert nonlocal_invoked[0] is False

    # 4 cooldown -> half open

    clock.advance(11)

    assert cb.call(lambda: "ok") == "ok"
    assert cb.state == "closed"

    # 5 single probe close

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=5,
        success_threshold=1,
        clock=clock,
    )

    try:
        cb.call(fail)
    except ValueError:
        pass

    clock.advance(6)

    cb.call(lambda: 1)
    assert cb.state == "closed"

    # 6 multi-probe close + reopen

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=5,
        success_threshold=3,
        clock=clock,
    )

    try:
        cb.call(fail)
    except ValueError:
        pass

    clock.advance(6)

    cb.call(lambda: 1)
    assert cb.state == "half_open"

    cb.call(lambda: 1)
    assert cb.state == "half_open"

    try:
        cb.call(fail)
    except ValueError:
        pass

    assert cb.state == "open"

    # Capture the exact clock time of the probe failure so the cooldown
    # boundary assertions below are relative to this moment, not the
    # original open time (which was clock.now - 6 seconds ago).
    failure_reopen_time = clock.now

    # 7 cooldown restart

    # Advance to just before cooldown_seconds=5 from the re-open moment.
    # Total elapsed since original open: 6 + 4 = 10, but only 4 from re-open.
    clock.advance(4)
    assert clock.now - failure_reopen_time < 5, "sanity: still within cooldown"

    try:
        cb.call(lambda: 1)
        assert False, "expected CircuitOpenError before cooldown elapses"
    except CircuitOpenError:
        pass

    # Now advance past cooldown from the re-open moment (4 + 2 = 6 > 5).
    clock.advance(2)
    assert clock.now - failure_reopen_time >= 5, "sanity: cooldown has elapsed"

    cb.call(lambda: 1)
    assert cb.state == "half_open"

    # 8 concurrency cap

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=1,
        clock=clock,
    )

    try:
        cb.call(fail)
    except ValueError:
        pass

    clock.advance(2)

    started = threading.Event()
    release = threading.Event()

    def slow_probe():
        started.set()
        release.wait()
        return "ok"

    t = threading.Thread(target=lambda: cb.call(slow_probe))
    t.start()

    started.wait()

    try:
        cb.call(lambda: "x")
        assert False
    except CircuitOpenError:
        pass

    release.set()
    t.join()

    # 9 failure predicate

    cb = CircuitBreaker(
        failure_threshold=2,
        failure_predicate=lambda exc: not isinstance(exc, ValueError),
    )

    for _ in range(100):
        try:
            cb.call(fail)
        except ValueError:
            pass

    assert cb.state == "closed"

    # 10 state transitions

    transitions = []

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=5,
        on_state_change=lambda old, new: transitions.append((old, new)),
        clock=clock,
    )

    try:
        cb.call(fail)
    except ValueError:
        pass

    clock.advance(6)

    cb.call(lambda: 1)

    assert transitions == [
        ("closed", "open"),
        ("open", "half_open"),
        ("half_open", "closed"),
    ]

    # 11 manual record

    cb = CircuitBreaker(failure_threshold=2)

    cb.record_failure()
    assert cb.consecutive_failures == 1

    cb.record_success()
    assert cb.consecutive_failures == 0

    # 12 reset

    transitions = []

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=1,
        cooldown_seconds=5,
        clock=clock,
        on_state_change=lambda old, new: transitions.append((old, new)),
    )

    cb.record_failure()

    assert cb.state == "open"

    cb.reset()

    assert cb.state == "closed"
    assert cb.consecutive_failures == 0
    assert ("open", "closed") in transitions

    # 13 thread safety

    import random

    clock = FakeClock()

    cb = CircuitBreaker(
        failure_threshold=5,
        cooldown_seconds=1,
        clock=clock,
    )

    # Each call independently draws from random so the 50 % failure rate
    # holds per-call regardless of thread interleaving.  The shared-counter
    # modulo approach gave approximately 50 % overall but the exact split
    # per thread depended on scheduling order.
    rng_lock = threading.Lock()
    rng = random.Random(42)

    def flaky():
        with rng_lock:
            should_fail = rng.random() < 0.5

        if should_fail:
            raise ValueError

        return "ok"

    def worker():
        for _ in range(100):
            try:
                cb.call(flaky)
            except Exception:
                pass

    threads = [threading.Thread(target=worker) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert cb.state in {"closed", "open", "half_open"}
    assert cb.consecutive_failures <= cb._failure_threshold + 1

    print("All tests passed.")