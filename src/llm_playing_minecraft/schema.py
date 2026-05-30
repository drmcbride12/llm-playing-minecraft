from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any


ALLOWED_BARITONE_COMMANDS = {
    "#build",
    "#explore",
    "#farm",
    "#follow",
    "#goto",
    "#mine",
    "#path",
    "#pause",
    "#resume",
    "#set",
    "#stop",
}

COMMANDS_REQUIRING_ARGUMENTS = {
    "#build",
    "#follow",
    "#goto",
    "#mine",
    "#set",
}


class ActionValidationError(ValueError):
    """Raised when an LLM action is malformed or unsafe."""


@dataclass(frozen=True)
class AgentAction:
    """A single supervised Minecraft action proposed by the LLM."""

    reason: str
    chat: str | None = None
    baritone_command: str | None = None
    wait_seconds: int = 1
    done: bool = False

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "AgentAction":
        reason = _coerce_short_text(payload.get("reason"), "reason", required=True)
        chat = _coerce_short_text(payload.get("chat"), "chat", required=False)
        command = _normalize_baritone_command(
            payload.get("baritone_command", payload.get("command"))
        )
        wait_seconds = _coerce_wait_seconds(payload.get("wait_seconds", 1))
        done = bool(payload.get("done", False))

        if not chat and not command and not done:
            raise ActionValidationError(
                "action must include chat, baritone_command, or done=true"
            )

        return cls(
            reason=reason,
            chat=chat,
            baritone_command=command,
            wait_seconds=wait_seconds,
            done=done,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_action_response(text: str) -> AgentAction:
    """Parse and validate the LLM's JSON action response."""

    payload = _extract_json_object(text)
    if not isinstance(payload, dict):
        raise ActionValidationError("LLM response must be a JSON object")
    return AgentAction.from_mapping(payload)


def safe_fallback_action(error: Exception) -> AgentAction:
    """Return a conservative action when the model produces invalid output."""

    return AgentAction(
        reason=f"Rejected unsafe or invalid model output: {error}",
        baritone_command="#stop",
        wait_seconds=1,
        done=False,
    )


def render_action(action: AgentAction) -> str:
    return json.dumps(action.to_dict(), indent=2, sort_keys=True)


def _extract_json_object(text: str) -> Any:
    stripped = text.strip()

    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(stripped[start : end + 1])


def _coerce_short_text(value: Any, name: str, required: bool) -> str | None:
    if value is None:
        if required:
            raise ActionValidationError(f"{name} is required")
        return None

    text = str(value).strip()
    if not text:
        if required:
            raise ActionValidationError(f"{name} cannot be empty")
        return None

    if len(text) > 500:
        raise ActionValidationError(f"{name} must be 500 characters or fewer")
    return text


def _normalize_baritone_command(value: Any) -> str | None:
    if value is None:
        return None

    command = str(value).strip()
    if not command or command.lower() in {"none", "null", "wait"}:
        return None

    if not command.startswith("#"):
        raise ActionValidationError(
            "baritone_command must be a Baritone chat command starting with #"
        )

    command_name = command.split(maxsplit=1)[0].lower()
    if command_name not in ALLOWED_BARITONE_COMMANDS:
        allowed = ", ".join(sorted(ALLOWED_BARITONE_COMMANDS))
        raise ActionValidationError(
            f"unsupported Baritone command {command_name!r}; allowed: {allowed}"
        )

    if command_name in COMMANDS_REQUIRING_ARGUMENTS and len(command.split()) == 1:
        raise ActionValidationError(f"{command_name} requires target arguments")

    if "\n" in command or "\r" in command:
        raise ActionValidationError("baritone_command must be one line")

    if len(command) > 200:
        raise ActionValidationError("baritone_command must be 200 characters or fewer")

    return command


def _coerce_wait_seconds(value: Any) -> int:
    try:
        wait_seconds = int(value)
    except (TypeError, ValueError) as exc:
        raise ActionValidationError("wait_seconds must be an integer") from exc

    if wait_seconds < 0 or wait_seconds > 300:
        raise ActionValidationError("wait_seconds must be between 0 and 300")
    return wait_seconds
