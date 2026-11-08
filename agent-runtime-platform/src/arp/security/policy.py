from dataclasses import dataclass


class PermissionDenied(Exception):
    pass


@dataclass(frozen=True)
class ToolPolicy:
    allowed_tools: frozenset[str]

    def authorize(self, name: str) -> None:
        if name not in self.allowed_tools:
            raise PermissionDenied(f"Tool not permitted: {name}")
