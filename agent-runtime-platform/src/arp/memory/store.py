from __future__ import annotations

from collections import defaultdict
from typing import Protocol


class MemoryStore(Protocol):
    def add(self, namespace: str, value: str) -> None: ...

    def search(self, namespace: str, query: str, limit: int = 5) -> list[str]: ...


class InMemoryStore:
    """Ephemeral lexical retrieval, not a vector or multi-tenant production store."""

    def __init__(self) -> None:
        self._items: dict[str, list[str]] = defaultdict(list)

    def add(self, namespace: str, value: str) -> None:
        if not namespace or not value:
            raise ValueError("namespace and value must be nonempty")
        self._items[namespace].append(value)

    def search(self, namespace: str, query: str, limit: int = 5) -> list[str]:
        if not namespace or not query or limit < 1:
            raise ValueError("namespace, query and positive limit are required")
        needle = query.casefold()
        return [v for v in reversed(self._items.get(namespace, [])) if needle in v.casefold()][:limit]
