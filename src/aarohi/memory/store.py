"""Local-first durable memory storage and deterministic retrieval."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from aarohi.database import connect, initialise

_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token)\s*[:=]"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)
_TOKEN = re.compile(r"[a-z0-9]{2,}")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _validate_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} cannot be empty")
    cleaned = value.strip()
    if any(pattern.search(cleaned) for pattern in _SECRET_PATTERNS):
        raise ValueError("Memory cannot store content that appears to contain credentials")
    return cleaned


class MemoryStore:
    """Persist user/project memories with provenance and explicit lifecycle."""

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        initialise(self.database_path)

    def list_memories(
        self, *, scope: str | None = None, category: str | None = None,
        include_archived: bool = False, limit: int = 100,
    ) -> list[dict]:
        """List recent memories, active by default; archived records are opt-in."""
        if limit < 1 or limit > 500:
            raise ValueError("limit must be between 1 and 500")
        clauses = []
        params: list[object] = []
        if not include_archived:
            clauses.append("status = 'active'")
        if scope is not None:
            clauses.append("scope = ?")
            params.append(scope.lower())
        if category is not None:
            clauses.append("category = ?")
            params.append(category.lower())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with connect(self.database_path) as db:
            rows = db.execute(
                f"SELECT * FROM memories {where} ORDER BY updated_at DESC LIMIT ?",
                [*params, limit],
            ).fetchall()
        results = [dict(row) for row in rows]
        for item in results:
            item["confirmed"] = bool(item["confirmed"])
        return results

    def find_conflicts(
        self, content: str, *, category: str = "fact", scope: str = "global",
        threshold: float = 0.5, limit: int = 5,
    ) -> list[dict]:
        """Find same-scope/category memories with substantial lexical overlap.

        These are review candidates, not proven contradictions. The store never
        silently overwrites an existing memory.
        """
        content = _validate_text(content, "content")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        incoming = set(_TOKEN.findall(content.lower()))
        if not incoming:
            return []
        with connect(self.database_path) as db:
            rows = db.execute(
                """SELECT * FROM memories
                WHERE status = 'active' AND scope = ? AND category = ?
                ORDER BY updated_at DESC""",
                (scope.lower(), category.lower()),
            ).fetchall()
        matches = []
        for row in rows:
            item = dict(row)
            existing = set(_TOKEN.findall(item["content"].lower()))
            union = incoming | existing
            similarity = len(incoming & existing) / len(union) if union else 0.0
            if similarity >= threshold:
                item["confirmed"] = bool(item["confirmed"])
                item["similarity"] = round(similarity, 3)
                matches.append(item)
        matches.sort(key=lambda item: (item["similarity"], item["updated_at"]), reverse=True)
        return matches[:limit]

    def curate(
        self, content: str, *, category: str = "fact", scope: str = "global",
        source: str, confidence: float = 1.0, confirmed: bool = False,
        replace_id: str | None = None,
    ) -> dict:
        """Save a candidate, requiring an explicit ID to replace a similar memory."""
        candidates = self.find_conflicts(content, category=category, scope=scope)
        if candidates and replace_id is None:
            return {"status": "needs_review", "memory_id": None, "candidates": candidates}
        if replace_id is not None:
            if not any(item["id"] == replace_id for item in candidates):
                raise ValueError("replace_id must identify a matching active memory")
            updated = self.update(
                replace_id, content=content, source=source,
                confidence=confidence, confirmed=confirmed,
            )
            if not updated:
                raise ValueError("The selected memory could not be updated")
            return {"status": "updated", "memory_id": replace_id, "candidates": candidates}
        memory_id = self.save(
            content, category=category, scope=scope, source=source,
            confidence=confidence, confirmed=confirmed,
        )
        return {"status": "saved", "memory_id": memory_id, "candidates": []}

    def save(
        self,
        content: str,
        *,
        category: str = "fact",
        scope: str = "global",
        source: str,
        confidence: float = 1.0,
        confirmed: bool = False,
    ) -> str:
        content = _validate_text(content, "content")
        source = _validate_text(source, "source")
        category = _validate_text(category, "category").lower()
        scope = _validate_text(scope, "scope").lower()
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError("confidence must be a number")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not isinstance(confirmed, bool):
            raise TypeError("confirmed must be a boolean")
        memory_id, now = str(uuid4()), _now()
        with connect(self.database_path) as db:
            db.execute(
                """INSERT INTO memories
                (id, content, category, scope, source, confidence, confirmed,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)""",
                (memory_id, content, category, scope, source, confidence,
                 int(confirmed), now, now),
            )
        return memory_id

    def get(self, memory_id: str) -> dict | None:
        with connect(self.database_path) as db:
            row = db.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE memories SET last_accessed_at = ? WHERE id = ?",
                (_now(), memory_id),
            )
        result = dict(row)
        result["confirmed"] = bool(result["confirmed"])
        return result

    def search(
        self,
        query: str,
        *,
        scope: str | None = None,
        category: str | None = None,
        confirmed_only: bool = False,
        limit: int = 10,
    ) -> list[dict]:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100")
        terms = set(_TOKEN.findall(query.lower()))
        if not terms:
            return []
        clauses = ["status = 'active'"]
        params: list[object] = []
        if scope is not None:
            clauses.append("scope = ?")
            params.append(scope.lower())
        if category is not None:
            clauses.append("category = ?")
            params.append(category.lower())
        if confirmed_only:
            clauses.append("confirmed = 1")
        with connect(self.database_path) as db:
            rows = db.execute(
                f"SELECT * FROM memories WHERE {' AND '.join(clauses)}", params
            ).fetchall()
        ranked: list[tuple[int, str, dict]] = []
        for row in rows:
            item = dict(row)
            haystack = f"{item['content']} {item['category']} {item['scope']}".lower()
            item_terms = set(_TOKEN.findall(haystack))
            score = len(terms & item_terms)
            if query.strip().lower() in item["content"].lower():
                score += len(terms) + 2
            if score:
                item["confirmed"] = bool(item["confirmed"])
                ranked.append((score, item["updated_at"], item))
        ranked.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
        results = [entry[2] for entry in ranked[:limit]]
        if results:
            now = _now()
            with connect(self.database_path) as db:
                db.executemany(
                    "UPDATE memories SET last_accessed_at = ? WHERE id = ?",
                    [(now, item["id"]) for item in results],
                )
        return results

    def update(self, memory_id: str, **changes: object) -> bool:
        allowed = {"content", "category", "scope", "source", "confidence", "confirmed"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Unsupported memory fields: {', '.join(sorted(unknown))}")
        if not changes:
            return self.get(memory_id) is not None
        if "content" in changes:
            changes["content"] = _validate_text(changes["content"], "content")  # type: ignore[arg-type]
        if "source" in changes:
            changes["source"] = _validate_text(changes["source"], "source")  # type: ignore[arg-type]
        for field in ("category", "scope"):
            if field in changes:
                changes[field] = _validate_text(changes[field], field).lower()  # type: ignore[arg-type]
        if "confidence" in changes:
            confidence = changes["confidence"]
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise TypeError("confidence must be a number")
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("confidence must be between 0 and 1")
        if "confirmed" in changes and not isinstance(changes["confirmed"], bool):
            raise TypeError("confirmed must be a boolean")
        assignments = [f"{field} = ?" for field in changes]
        values = [int(value) if field == "confirmed" else value for field, value in changes.items()]
        assignments.append("updated_at = ?")
        values.extend([_now(), memory_id])
        with connect(self.database_path) as db:
            cursor = db.execute(
                f"UPDATE memories SET {', '.join(assignments)} WHERE id = ? AND status = 'active'",
                values,
            )
            return cursor.rowcount == 1

    def archive(self, memory_id: str) -> bool:
        with connect(self.database_path) as db:
            cursor = db.execute(
                "UPDATE memories SET status = 'archived', updated_at = ? WHERE id = ? AND status = 'active'",
                (_now(), memory_id),
            )
            return cursor.rowcount == 1

    def forget(self, memory_id: str) -> bool:
        """Delete one memory and scrub its copies from persisted task snapshots."""
        import json

        with connect(self.database_path) as db:
            cursor = db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            if cursor.rowcount != 1:
                return False
            snapshots = db.execute(
                "SELECT task_id, context_json FROM task_context"
            ).fetchall()
            for snapshot in snapshots:
                try:
                    context = json.loads(snapshot["context_json"])
                except (TypeError, json.JSONDecodeError):
                    continue
                if not isinstance(context, list):
                    continue
                filtered = [
                    item for item in context
                    if not isinstance(item, dict) or item.get("id") != memory_id
                ]
                if len(filtered) != len(context):
                    db.execute(
                        "UPDATE task_context SET context_json = ? WHERE task_id = ?",
                        (json.dumps(filtered, ensure_ascii=False), snapshot["task_id"]),
                    )
            return True
