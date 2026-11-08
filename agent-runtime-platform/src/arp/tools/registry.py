from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from arp.security.policy import ToolPolicy

ToolFunction = Callable[[dict[str, Any]], Awaitable[str]]


class ToolError(Exception):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    execute: ToolFunction


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"Invalid or duplicate tool name: {tool.name}")
        self._tools[tool.name] = tool

    def descriptions(self, policy: ToolPolicy) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for name, tool in self._tools.items()
            if name in policy.allowed_tools
        ]

    async def invoke(self, name: str, arguments: dict[str, Any], policy: ToolPolicy) -> str:
        policy.authorize(name)
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        return await self._tools[name].execute(arguments)


async def echo_tool(arguments: dict[str, Any]) -> str:
    text = arguments.get("text")
    if not isinstance(text, str) or not text or len(text) > 4000:
        raise ToolError("echo requires a nonempty text string of at most 4000 characters")
    return text


def default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(Tool("echo", "Return the supplied text; arguments: {text: string}.", echo_tool))
    return registry
