import time
from collections import defaultdict, deque
from collections.abc import Callable


# shortcut: in-memory, per-process; resets on restart. Move to Postgres if >1 instance.
class RateLimiter:
    """Sliding window: at most `limit` hits per key within `window_seconds`."""

    def __init__(
        self, limit: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.limit = limit
        self.window = window_seconds
        self.clock = clock
        self._hits: defaultdict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> bool:
        now = self.clock()
        q = self._hits[key]
        while q and q[0] <= now - self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)


login_limiter = RateLimiter(10, 300)
