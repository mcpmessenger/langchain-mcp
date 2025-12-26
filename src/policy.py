"""
Policy enforcement for MCP invocations.

Goals:
- Keep MCP-native semantics (deny early, return MCP-shaped error on /mcp/invoke)
- Prevent accidental overload (very large query payloads)
- Support Glazyr safety knobs (URL allowlisting, simple budget checks)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


_URL_RE = re.compile(r"https?://[^\s)]+", re.IGNORECASE)


def _extract_urls(text: str) -> List[str]:
    return _URL_RE.findall(text or "")


def _domain_of(url: str) -> Optional[str]:
    # Minimal parsing to avoid heavy deps; sufficient for allowlist gating.
    m = re.match(r"^https?://([^/]+)", url, re.IGNORECASE)
    if not m:
        return None
    host = m.group(1)
    # strip port
    host = host.split(":")[0]
    return host.lower()


def _host_allowed(host: str, allowlisted_domains: List[str]) -> bool:
    if not allowlisted_domains:
        return True
    host = host.lower()
    for allowed in allowlisted_domains:
        a = allowed.lower()
        if host == a:
            return True
        # allow subdomains: *.example.com via "example.com"
        if host.endswith("." + a):
            return True
    return False


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    status_code: int = 200
    reason: Optional[str] = None
    code: Optional[str] = None


def evaluate_invoke_policy(
    *,
    query: str,
    max_query_chars: int,
    allowlisted_domains: List[str],
) -> PolicyDecision:
    if query is None or str(query).strip() == "":
        # Let endpoint handle the canonical missing query response
        return PolicyDecision(allowed=True)

    if len(query) > max_query_chars:
        return PolicyDecision(
            allowed=False,
            status_code=413,
            reason=f"Query too large (len={len(query)} > MAX_QUERY_CHARS={max_query_chars})",
            code="PAYLOAD_TOO_LARGE",
        )

    urls = _extract_urls(query)
    if urls and allowlisted_domains:
        for url in urls:
            host = _domain_of(url)
            if host and not _host_allowed(host, allowlisted_domains):
                return PolicyDecision(
                    allowed=False,
                    status_code=403,
                    reason=f"URL domain not allowlisted: {host}",
                    code="DOMAIN_NOT_ALLOWED",
                )

    return PolicyDecision(allowed=True)


