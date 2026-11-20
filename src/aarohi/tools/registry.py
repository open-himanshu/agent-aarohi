"""Registry for explicitly implemented tools."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aarohi.security.policy import Risk


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: Risk
    handler: Callable[..., Any]

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"Invalid or duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolSpec:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_tools(self) -> list[ToolSpec]:
        return sorted(self._tools.values(), key=lambda item: item.name)
