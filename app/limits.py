"""Tiny in-memory limits so a public demo cannot burn the LLM quota."""
import os
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, per_minute: int | None = None, daily_cap: int | None = None):
        self.per_minute = per_minute if per_minute is not None else int(os.getenv("RATE_LIMIT_PER_MIN", "8"))
        self.daily_cap = daily_cap if daily_cap is not None else int(os.getenv("DAILY_CAP", "300"))
        self.hits: dict[str, deque] = defaultdict(deque)
        self.day, self.today_count = "", 0

    def check(self, ip: str, now: float | None = None) -> str | None:
        """Return an error message if the request must be refused; otherwise record it and return None."""
        now = time.time() if now is None else now
        recent = self.hits[ip]
        while recent and now - recent[0] > 60:
            recent.popleft()
        if len(recent) >= self.per_minute:
            return "Too many requests. Please wait a minute and try again."
        day = time.strftime("%Y-%m-%d", time.gmtime(now))
        if day != self.day:
            self.day, self.today_count = day, 0
        if self.today_count >= self.daily_cap:
            return "The daily limit for this free demo has been reached. Please try again tomorrow."
        recent.append(now)
        self.today_count += 1
        return None
