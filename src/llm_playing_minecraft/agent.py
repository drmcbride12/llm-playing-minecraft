from __future__ import annotations

from dataclasses import dataclass

from .lmstudio_client import LMStudioClient
from .prompts import build_messages
from .schema import AgentAction, parse_action_response, safe_fallback_action


@dataclass
class MinecraftAgent:
    """Observe-plan-act loop coordinator."""

    client: LMStudioClient

    def plan(
        self,
        goal: str,
        observation: str,
        history: list[AgentAction] | None = None,
    ) -> AgentAction:
        messages = build_messages(
            goal,
            observation,
            history,
            context_length=self.client.config.context_length,
            baritone_profile=self.client.config.baritone_profile,
        )
        response = self.client.chat(messages)

        try:
            return parse_action_response(response)
        except Exception as exc:
            return safe_fallback_action(exc)
