"""Conservative memory capture and task-context assembly policy."""
from __future__ import annotations

import re

from aarohi.memory.store import MemoryStore

_EXPLICIT_PREFIX = re.compile(
    r"^\s*(?:please\s+)?(?:remember(?:\s+that)?|keep\s+in\s+mind(?:\s+that)?|yaad\s+rakhna|yaad\s+rakhiye|yaad\s+rakho)[:,]?\s+",
    re.IGNORECASE,
)


class MemoryManager:
    """Curate only explicit memory requests and assemble bounded task context."""

    def __init__(self, store: MemoryStore):
        self.store = store

    def capture_explicit(self, statement: str, *, source: str = "explicit user request", scope: str = "global") -> dict:
        match = _EXPLICIT_PREFIX.match(statement)
        if not match:
            return {"status": "ignored", "reason": "No explicit remember instruction detected"}
        content = statement[match.end():].strip()
        if not content:
            return {"status": "ignored", "reason": "Memory statement is empty"}
        lowered = content.lower()
        category = "preference" if any(word in lowered for word in ("prefer", "always", "never", "likes", "dislikes", "pasand", "hamesha", "kabhi nahi")) else "decision" if any(word in lowered for word in ("decided", "decision", "will use", "locked", "final", "decide", "use karenge")) else "fact"
        return self.store.curate(
            content, category=category, scope=scope, source=source,
            confidence=1.0, confirmed=True,
        )

    def build_context(self, query: str, *, scope: str | None = None, limit: int = 5, max_chars: int = 4000) -> list[dict]:
        if limit < 1 or limit > 20:
            raise ValueError("context limit must be between 1 and 20")
        if max_chars < 100 or max_chars > 20000:
            raise ValueError("max_chars must be between 100 and 20000")
        results = self.store.search(query, scope=scope, confirmed_only=True, limit=limit * 3)
        query_terms = set(re.findall(r"[a-z0-9]{2,}", query.lower()))
        selected = []
        used = 0
        for item in results:
            terms = set(re.findall(r"[a-z0-9]{2,}", item["content"].lower()))
            overlap = len(query_terms & terms)
            if query_terms and overlap < min(2, len(query_terms)):
                continue
            excerpt = {key: item[key] for key in ("id", "content", "category", "scope", "source", "confidence", "confirmed", "updated_at")}
            cost = len(excerpt["content"])
            if used + cost > max_chars:
                continue
            selected.append(excerpt)
            used += cost
            if len(selected) >= limit:
                break
        return selected
