from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4


class AgentRole(StrEnum):
    RESEARCH = "research"
    SCRAPER = "scraper"
    PLANNER = "planner"
    VALIDATOR = "validator"
    CRITIC = "critic"
    CODING = "coding"
    KNOWLEDGE = "knowledge"
    SUPERVISOR = "supervisor"


@dataclass(frozen=True)
class AgentMessage:
    sender: AgentRole
    recipient: AgentRole
    task_id: str
    content: str
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
