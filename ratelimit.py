"""In-memory sliding-window rate limiter, keyed by client identifier.

Single-process only — correct for a single gunicorn worker (the default,
and what render.yaml's startCommand runs). A multi-worker deployment would
need a shared store (e.g. Redis) instead; not needed at this scale.
"""

import threading
import time


class RateLimiter:
    def __init__(self, max_requests, window_seconds, clock=time.monotonic):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits = {}
        self._lock = threading.Lock()

    def allow(self, key):
        now = self._clock()
        cutoff = now - self._window_seconds
        with self._lock:
            timestamps = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(timestamps) >= self._max_requests:
                self._hits[key] = timestamps
                return False
            timestamps.append(now)
            self._hits[key] = timestamps
            return True
