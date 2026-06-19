"""
Reviewer Note
-------------
Design:
- Uses the standard continuous-refill token bucket formula:

      tokens = min(burst, tokens + (now - last_refill) * rate)

  The bucket is then updated with:
      last_refill = now

  after every refill calculation. This prevents double-counting elapsed
  time and keeps all read/modify/write operations consistent.

- The bucket starts FULL by design. This matches the specification and
  allows the first `burst` tokens to be consumed immediately.

- Thread safety:
  All refill/check/consume operations are performed while holding a
  single lock. This keeps read-modify-write atomic and guarantees that
  concurrent callers cannot over-consume tokens.

- Blocking strategy:
  acquire() computes the deficit and estimated wait time, then sleeps in
  short slices (maximum 50 ms per sleep) before re-checking. Sleeping in
  slices avoids oversleeping when multiple threads contend and allows
  timeout handling to remain responsive.

- tokens_available() is informational only. Callers must not branch on
  it for correctness because another thread may acquire tokens between
  the read and a subsequent acquire() call.

Test gaps:
- No attempt is made to validate real-time scheduling accuracy across
  operating systems; tests use an injectable fake clock and fake sleep.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable


class TokenBucket:
    """Thread-safe continuous-refill token bucket rate limiter."""

    def __init__(
        self,
        rate_per_second: float,
        burst: int,
        clock: Callable[[], float] | None = None,
        _sleep: Callable[[float], None] | None = None,
    ) -> None:
        """
        Args:
            rate_per_second:
                Continuous refill rate in tokens per second.
            burst:
                Maximum bucket capacity.
            clock:
                Injectable monotonic clock for tests; defaults to
                time.monotonic. Pass a FakeClock rather than sleeping
                for real.
            _sleep:
                Injectable sleep callable for tests; defaults to
                time.sleep. Allows deterministic timeout/blocking tests
                without real wall-clock delays. Not part of the public
                API — prefix signals internal use.
        Raises:
            ValueError:
                If rate_per_second <= 0 or burst < 1.
        """
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be > 0")

        if burst < 1:
            raise ValueError("burst must be >= 1")

        self._rate = float(rate_per_second)
        self._burst = burst
        self._clock = clock if clock is not None else time.monotonic
        self._sleep = _sleep if _sleep is not None else time.sleep

        self._tokens = float(burst)
        self._last_refill = self._clock()

        self._lock = threading.Lock()

    def _refill_locked(self) -> None:
        """Refill bucket using elapsed time. Lock must be held."""
        now = self._clock()
        elapsed = now - self._last_refill

        if elapsed > 0:
            self._tokens = min(
                float(self._burst),
                self._tokens + elapsed * self._rate,
            )
            self._last_refill = now

    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Non-blocking token acquisition.

        Args:
            tokens:
                Number of tokens to consume.

        Returns:
            True if acquired, otherwise False.

        Raises:
            ValueError:
                If tokens > burst or tokens < 1.
        """
        if tokens < 1:
            raise ValueError("tokens must be >= 1")

        if tokens > self._burst:
            raise ValueError("tokens cannot exceed burst")

        with self._lock:
            self._refill_locked()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True

            return False

    def acquire(self, tokens: int = 1, timeout: float | None = None) -> bool:
        """
        Acquire tokens, optionally waiting.

        Args:
            tokens:
                Number of tokens to consume.
            timeout:
                None = wait forever.
                0 = non-blocking.
                >0 = wait at most timeout seconds.

        Returns:
            True if acquired, False on timeout.

        Raises:
            ValueError:
                If tokens > burst or tokens < 1.
        """
        if tokens < 1:
            raise ValueError("tokens must be >= 1")

        if tokens > self._burst:
            raise ValueError("tokens cannot exceed burst")

        if timeout == 0:
            return self.try_acquire(tokens)

        start = self._clock()

        while True:
            with self._lock:
                self._refill_locked()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                deficit = tokens - self._tokens
                estimated_wait = deficit / self._rate

            if timeout is not None:
                elapsed = self._clock() - start
                remaining = timeout - elapsed

                if remaining <= 0:
                    return False

                sleep_for = min(0.05, estimated_wait, remaining)
            else:
                sleep_for = min(0.05, estimated_wait)

            self._sleep(max(0.0, sleep_for))

    def tokens_available(self) -> float:
        """
        Return the current token count after applying refill.

        Returns:
            Current token count as a float.
        """
        with self._lock:
            self._refill_locked()
            return self._tokens


class FakeClock:
    """Deterministic test clock."""

    def __init__(self, start: float = 0.0) -> None:
        self._time = start
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._time

    def advance(self, seconds: float) -> None:
        with self._lock:
            self._time += seconds


if __name__ == "__main__":
    # Construction validation.
    for bad_rate in (0, -1):
        try:
            TokenBucket(bad_rate, 1)
            assert False
        except ValueError:
            pass

    for bad_burst in (0, -1):
        try:
            TokenBucket(1, bad_burst)
            assert False
        except ValueError:
            pass

    # Starts full.
    clock = FakeClock()
    bucket = TokenBucket(1, 5, clock=clock)

    for _ in range(5):
        assert bucket.try_acquire()

    assert not bucket.try_acquire()

    # Continuous refill.
    clock = FakeClock()
    bucket = TokenBucket(10, 5, clock=clock)

    assert bucket.try_acquire(5)

    clock.advance(0.5)
    assert abs(bucket.tokens_available() - 5.0) < 1e-9

    assert bucket.try_acquire(5)

    clock.advance(0.3)
    assert abs(bucket.tokens_available() - 3.0) < 1e-9

    # Cap respected.
    clock = FakeClock()
    bucket = TokenBucket(10, 5, clock=clock)

    clock.advance(60)
    assert bucket.tokens_available() == 5.0

    # Multi-token consume.
    clock = FakeClock()
    bucket = TokenBucket(1, 5, clock=clock)

    assert bucket.acquire(3, timeout=0)
    assert bucket.acquire(1, timeout=0)
    assert not bucket.acquire(2, timeout=0)

    # tokens > burst raises immediately.
    bucket = TokenBucket(1, 5)

    try:
        bucket.acquire(6, timeout=100)
        assert False
    except ValueError:
        pass

    try:
        bucket.try_acquire(6)
        assert False
    except ValueError:
        pass

    # Blocking acquire succeeds.
    clock = FakeClock()

    def advancing_sleep(seconds: float) -> None:
        clock.advance(seconds)

    bucket = TokenBucket(
        10,
        5,
        clock=clock,
        _sleep=advancing_sleep,
    )

    assert bucket.acquire(5, timeout=0)
    assert bucket.acquire(timeout=0.5)

    # Blocking acquire times out.
    clock = FakeClock()

    def advancing_sleep_2(seconds: float) -> None:
        clock.advance(seconds)

    bucket = TokenBucket(
        1,
        5,
        clock=clock,
        _sleep=advancing_sleep_2,
    )

    assert bucket.acquire(5, timeout=0)
    assert not bucket.acquire(5, timeout=2)

    # timeout=0 behaves like try_acquire.
    clock = FakeClock()
    sleep_calls = []

    def tracking_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)

    bucket = TokenBucket(
        1,
        1,
        clock=clock,
        _sleep=tracking_sleep,
    )

    assert bucket.acquire(timeout=0)
    assert not bucket.acquire(timeout=0)
    assert sleep_calls == []

    # Thread safety.
    clock = FakeClock()
    bucket = TokenBucket(1, 50, clock=clock)

    results: list[int] = []
    results_lock = threading.Lock()

    def worker() -> None:
        local_successes = 0

        for _ in range(100):
            if bucket.try_acquire():
                local_successes += 1

        with results_lock:
            results.append(local_successes)

    threads = [threading.Thread(target=worker) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    assert sum(results) == 50

    print("All tests passed.")