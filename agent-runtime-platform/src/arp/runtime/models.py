from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Decision:
    kind: str
    content: str = ""
    tool: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class Run:
    goal: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.RUNNING
    events: list[dict[str, Any]] = field(default_factory=list)
    result: str | None = None
    error: str | None = None

    def record(self, event_type: str, **data: Any) -> None:
        self.events.append({"type": event_type, **data})
