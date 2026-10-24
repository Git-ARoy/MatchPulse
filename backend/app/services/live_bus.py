"""In-process pub/sub boundary for WebSocket fan-out.

This is intentionally replaceable with Redis Pub/Sub in multi-pod deployments;
the FastAPI contract is independent of that transport.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class LiveMatchBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = defaultdict(set)

    def subscribe(self, match_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers[match_id].add(queue)
        return queue

    def unsubscribe(self, match_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers[match_id].discard(queue)
        if not self._subscribers[match_id]:
            self._subscribers.pop(match_id, None)

    async def publish(self, match_id: str, message: dict[str, Any]) -> None:
        for queue in tuple(self._subscribers.get(match_id, ())):
            if queue.full():
                queue.get_nowait()  # Drop oldest state; newest state is authoritative.
            queue.put_nowait(message)


live_bus = LiveMatchBus()
