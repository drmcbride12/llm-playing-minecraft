from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .schema import AgentAction


class CommandTransport(Protocol):
    """A destination that can receive a planned Minecraft action."""

    def execute(self, action: AgentAction) -> str:
        """Execute or display an action and return a human-readable summary."""


@dataclass
class ConsoleTransport:
    """Default supervised transport that prints commands for the operator."""

    prefix: str = "[minecraft-agent]"

    def execute(self, action: AgentAction) -> str:
        lines = [f"{self.prefix} reason: {action.reason}"]

        if action.chat:
            lines.append(f"{self.prefix} chat: {action.chat}")

        if action.baritone_command:
            lines.append(f"{self.prefix} baritone: {action.baritone_command}")

        if action.wait_seconds:
            lines.append(f"{self.prefix} wait: {action.wait_seconds}s")

        if action.done:
            lines.append(f"{self.prefix} done")

        return "\n".join(lines)
