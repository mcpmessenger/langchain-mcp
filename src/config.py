"""
Configuration helpers for the MCP server.

Centralizes environment variable parsing so main.py / agent.py stay focused on behavior.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name, default)
    if v is None:
        return None
    v = v.strip()
    return v if v != "" else None


def _get_bool(name: str, default: bool = False) -> bool:
    v = _get_env(name)
    if v is None:
        return default
    return v.lower() in {"1", "true", "yes", "y", "on"}


def _get_int(name: str, default: int) -> int:
    v = _get_env(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def _get_csv(name: str) -> List[str]:
    v = _get_env(name)
    if not v:
        return []
    return [part.strip() for part in v.split(",") if part.strip()]


@dataclass(frozen=True)
class RuntimeConfig:
    # Security / auth
    api_key: Optional[str]

    # Agent controls
    max_iterations: int
    max_execution_time: int  # seconds
    tool_timeout: int  # seconds per tool
    max_concurrent_tools: int
    enable_progress_reports: bool

    # Policy enforcement
    policy_enforcement: bool
    max_query_chars: int
    allowlisted_domains: List[str]

    # State persistence
    redis_url: Optional[str]
    task_ttl_seconds: int
    recent_tasks_max: int


def load_config() -> RuntimeConfig:
    # Support both MAX_ITERATIONS and LANGCHAIN_MAX_ITERATIONS (spec preference)
    # LANGCHAIN_MAX_ITERATIONS takes precedence if set
    langchain_max_iter = _get_env("LANGCHAIN_MAX_ITERATIONS")
    max_iterations = (
        int(langchain_max_iter) if langchain_max_iter
        else _get_int("MAX_ITERATIONS", 100)  # Default: 100 per specification
    )
    
    return RuntimeConfig(
        api_key=_get_env("API_KEY"),
        max_iterations=max_iterations,
        max_execution_time=_get_int("LANGCHAIN_MAX_EXECUTION_TIME", 180),  # Default: 180 seconds (3 minutes)
        tool_timeout=_get_int("LANGCHAIN_TOOL_TIMEOUT", 60),  # Default: 60 seconds per tool
        max_concurrent_tools=_get_int("LANGCHAIN_MAX_CONCURRENT_TOOLS", 1),  # Default: 1 (sequential)
        enable_progress_reports=_get_bool("LANGCHAIN_ENABLE_PROGRESS_REPORTS", False),
        policy_enforcement=_get_bool("POLICY_ENFORCEMENT", False),
        max_query_chars=_get_int("MAX_QUERY_CHARS", 5_000_000),
        allowlisted_domains=_get_csv("ALLOWLISTED_DOMAINS"),
        redis_url=_get_env("REDIS_URL"),
        task_ttl_seconds=_get_int("TASK_TTL_SECONDS", 60 * 60 * 24),
        recent_tasks_max=_get_int("RECENT_TASKS_MAX", 200),
    )


