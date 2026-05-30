from __future__ import annotations

from dataclasses import dataclass
import json
from importlib import resources
from pathlib import Path
from typing import Any


class BaritoneProfileError(RuntimeError):
    """Raised when a Baritone profile cannot be loaded or rendered."""


@dataclass(frozen=True)
class BaritoneSetting:
    name: str
    value: bool | int | float | str
    category: str
    reason: str

    def command(self) -> str:
        return f"#set {self.name} {_format_setting_value(self.value)}"


@dataclass(frozen=True)
class BaritoneProfile:
    name: str
    display_name: str
    risk_level: str
    description: str
    settings: tuple[BaritoneSetting, ...]
    excluded_settings: tuple[dict[str, str], ...]

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "BaritoneProfile":
        try:
            settings = tuple(
                BaritoneSetting(
                    name=str(item["name"]),
                    value=item["value"],
                    category=str(item.get("category", "general")),
                    reason=str(item.get("reason", "")),
                )
                for item in payload["settings"]
            )
            excluded = tuple(dict(item) for item in payload.get("excluded_settings", []))
            return cls(
                name=str(payload["name"]),
                display_name=str(payload.get("display_name", payload["name"])),
                risk_level=str(payload.get("risk_level", "custom")),
                description=str(payload.get("description", "")),
                settings=settings,
                excluded_settings=excluded,
            )
        except (KeyError, TypeError) as exc:
            raise BaritoneProfileError(f"Invalid Baritone profile: {payload!r}") from exc

    def commands(self) -> list[str]:
        return [setting.command() for setting in self.settings]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "risk_level": self.risk_level,
            "description": self.description,
            "settings": [
                {
                    "name": setting.name,
                    "value": setting.value,
                    "category": setting.category,
                    "reason": setting.reason,
                }
                for setting in self.settings
            ],
            "excluded_settings": list(self.excluded_settings),
        }


def load_baritone_profile(
    profile_name: str = "bold",
    profile_file: str | Path | None = None,
) -> BaritoneProfile:
    if profile_file:
        raw = Path(profile_file).read_text(encoding="utf-8")
    else:
        resource_name = f"baritone_{profile_name}.json"
        try:
            raw = (
                resources.files("llm_playing_minecraft")
                .joinpath("profiles")
                .joinpath(resource_name)
                .read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise BaritoneProfileError(
                f"Unknown built-in Baritone profile {profile_name!r}"
            ) from exc

    return BaritoneProfile.from_mapping(json.loads(raw))


def render_profile_commands(profile: BaritoneProfile, include_comments: bool) -> str:
    lines: list[str] = []
    if include_comments:
        lines.extend(
            [
                f"# {profile.display_name}",
                f"# risk_level: {profile.risk_level}",
                f"# {profile.description}",
            ]
        )

    for setting in profile.settings:
        if include_comments and setting.reason:
            lines.append(f"# {setting.reason}")
        lines.append(setting.command())

    return "\n".join(lines)


def render_profile_markdown(profile: BaritoneProfile) -> str:
    lines = [
        f"# {profile.display_name}",
        "",
        f"Risk level: `{profile.risk_level}`",
        "",
        profile.description,
        "",
        "| Setting | Value | Category | Reason |",
        "| --- | --- | --- | --- |",
    ]

    for setting in profile.settings:
        lines.append(
            f"| `{setting.name}` | `{_format_setting_value(setting.value)}` | "
            f"{setting.category} | {setting.reason} |"
        )

    if profile.excluded_settings:
        lines.extend(["", "## Deliberately Not Enabled", ""])
        for item in profile.excluded_settings:
            lines.append(f"- `{item.get('name')}`: {item.get('reason')}")

    return "\n".join(lines)


def _format_setting_value(value: bool | int | float | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)
