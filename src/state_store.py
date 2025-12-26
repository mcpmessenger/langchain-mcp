"""
State persistence for MCP workflows (optional).

Glazyr can pass a stable task_id per workflow. We store only safe summaries
(no raw screenshots/base64) to avoid leaking visuals to any dashboards.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class TaskRecord:
    task_id: str
    created_at: float
    updated_at: float
    status: str  # "running" | "succeeded" | "failed"
    attempts: int
    query_preview: str
    query_sha256: str
    last_output_preview: Optional[str] = None
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "attempts": self.attempts,
            "query_preview": self.query_preview,
            "query_sha256": self.query_sha256,
            "last_output_preview": self.last_output_preview,
            "last_error": self.last_error,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TaskRecord":
        return TaskRecord(
            task_id=str(data["task_id"]),
            created_at=float(data["created_at"]),
            updated_at=float(data["updated_at"]),
            status=str(data["status"]),
            attempts=int(data.get("attempts", 0)),
            query_preview=str(data.get("query_preview", "")),
            query_sha256=str(data.get("query_sha256", "")),
            last_output_preview=data.get("last_output_preview"),
            last_error=data.get("last_error"),
        )


class StateStore(Protocol):
    def get_task(self, task_id: str) -> Optional[TaskRecord]: ...
    def put_task(self, record: TaskRecord, ttl_seconds: int) -> None: ...
    def add_recent(self, task_id: str, max_items: int) -> None: ...
    def list_recent(self, limit: int) -> List[str]: ...


class InMemoryStateStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._recent: List[str] = []

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)

    def put_task(self, record: TaskRecord, ttl_seconds: int) -> None:
        # TTL not enforced for in-memory store (intentionally simple for dev/test)
        self._tasks[record.task_id] = record

    def add_recent(self, task_id: str, max_items: int) -> None:
        if task_id in self._recent:
            self._recent.remove(task_id)
        self._recent.insert(0, task_id)
        del self._recent[max_items:]

    def list_recent(self, limit: int) -> List[str]:
        return self._recent[:limit]


class RedisStateStore:
    def __init__(self, redis_url: str) -> None:
        import redis  # lazy import so redis is optional at runtime

        # decode_responses=True ensures we get str, not bytes
        self._r = redis.Redis.from_url(redis_url, decode_responses=True)

    def _task_key(self, task_id: str) -> str:
        return f"task:{task_id}"

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        raw = self._r.get(self._task_key(task_id))
        if not raw:
            return None
        try:
            return TaskRecord.from_dict(json.loads(raw))
        except Exception:
            return None

    def put_task(self, record: TaskRecord, ttl_seconds: int) -> None:
        self._r.set(self._task_key(record.task_id), json.dumps(record.to_dict()), ex=ttl_seconds)

    def add_recent(self, task_id: str, max_items: int) -> None:
        # Maintain a small recency index without storing payloads.
        self._r.lrem("recent_tasks", 0, task_id)
        self._r.lpush("recent_tasks", task_id)
        self._r.ltrim("recent_tasks", 0, max_items - 1)

    def list_recent(self, limit: int) -> List[str]:
        return list(self._r.lrange("recent_tasks", 0, max(0, limit - 1)))


def now_ts() -> float:
    return time.time()


