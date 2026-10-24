"""Best-effort Redis snapshot cache; no Redis configuration is required."""

from __future__ import annotations

import json
import os
from typing import Any


class RedisMatchCache:
    def __init__(self) -> None:
        self._client: Any | None = None
        url = os.getenv("REDIS_URL", "").strip()
        if not url:
            return
        try:
            import redis
            self._client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.2, socket_timeout=0.2)
            self._client.ping()
        except Exception:
            self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def write(self, match_id: str, state: dict[str, Any], insights: list[dict[str, Any]]) -> None:
        if self._client is None:
            return
        try:
            pipe = self._client.pipeline()
            pipe.set(f"match:{match_id}:state", json.dumps(state), ex=5)
            pipe.set(f"match:{match_id}:insights", json.dumps(insights), ex=5)
            pipe.execute()
        except Exception:
            # Read/write correctness remains backed by the in-memory ledger.
            self._client = None
