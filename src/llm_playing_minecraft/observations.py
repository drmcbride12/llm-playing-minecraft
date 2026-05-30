from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from typing import Any


MAX_LIST_ITEMS = 12


@dataclass(frozen=True)
class CompactObservation:
    """Decision-oriented Minecraft state without screenshots or block dumps."""

    summary: str
    player: dict[str, Any] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    baritone: dict[str, Any] = field(default_factory=dict)
    important_blocks: list[dict[str, Any]] = field(default_factory=list)
    entities: list[dict[str, Any]] = field(default_factory=list)
    hazards: list[dict[str, Any]] = field(default_factory=list)
    regions: list[dict[str, Any]] = field(default_factory=list)
    memory: list[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "CompactObservation":
        return cls(
            summary=str(payload.get("summary", "")).strip()
            or "No observation summary provided.",
            player=dict(payload.get("player", {})),
            inventory=_string_list(payload.get("inventory", [])),
            baritone=dict(payload.get("baritone", {})),
            important_blocks=_mapping_list(payload.get("important_blocks", [])),
            entities=_mapping_list(payload.get("entities", [])),
            hazards=_mapping_list(payload.get("hazards", [])),
            regions=_mapping_list(payload.get("regions", [])),
            memory=_string_list(payload.get("memory", [])),
        )

    def to_prompt_text(self) -> str:
        sections = [
            f"Summary: {self.summary}",
            _render_mapping("Player", self.player),
            _render_list("Inventory", self.inventory),
            _render_mapping("Baritone", self.baritone),
            _render_records("Important blocks", self.important_blocks),
            _render_records("Entities", self.entities),
            _render_records("Hazards", self.hazards),
            _render_records("Regions", self.regions),
            _render_list("Memory", self.memory),
        ]
        return "\n".join(section for section in sections if section)


def compact_observation_from_text(text: str) -> str:
    """Return compact prompt text from JSON observations or plain text."""

    stripped = text.strip()
    if not stripped:
        return "Summary: No observation was provided."

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stripped

    if isinstance(payload, dict):
        if "blocks" in payload and "important_blocks" not in payload:
            payload = dict(payload)
            payload["important_blocks"] = summarize_block_cloud(payload.pop("blocks"))
        return CompactObservation.from_mapping(payload).to_prompt_text()

    return stripped


def summarize_block_cloud(blocks: Any, limit: int = MAX_LIST_ITEMS) -> list[dict[str, Any]]:
    """Collapse raw block records into count/range summaries if one slips through."""

    if not isinstance(blocks, list):
        return []

    counts: Counter[str] = Counter()
    ranges: dict[str, dict[str, list[int]]] = {}

    for item in blocks:
        if isinstance(item, str):
            block_name = item
            position = None
        elif isinstance(item, dict):
            block_name = str(item.get("block") or item.get("name") or "unknown")
            position = item.get("pos") or item.get("position")
        else:
            continue

        counts[block_name] += 1
        if isinstance(position, dict):
            axis_ranges = ranges.setdefault(
                block_name,
                {"x": [], "y": [], "z": []},
            )
            for axis in ("x", "y", "z"):
                value = position.get(axis)
                if isinstance(value, int | float):
                    axis_ranges[axis].append(int(value))

    summaries: list[dict[str, Any]] = []
    for block_name, count in counts.most_common(limit):
        record: dict[str, Any] = {"block": block_name, "count": count}
        if block_name in ranges:
            record["range"] = {
                axis: [min(values), max(values)]
                for axis, values in ranges[block_name].items()
                if values
            }
        summaries.append(record)
    return summaries


def _render_mapping(title: str, values: dict[str, Any]) -> str:
    if not values:
        return ""
    parts = [f"{key}={value}" for key, value in values.items()]
    return f"{title}: {', '.join(parts)}"


def _render_list(title: str, values: list[str]) -> str:
    if not values:
        return ""
    return f"{title}: {', '.join(values[:MAX_LIST_ITEMS])}"


def _render_records(title: str, records: list[dict[str, Any]]) -> str:
    if not records:
        return ""
    lines = [f"{title}:"]
    for record in records[:MAX_LIST_ITEMS]:
        lines.append(f"- {_record_inline(record)}")
    return "\n".join(lines)


def _record_inline(record: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in record.items())


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value[:MAX_LIST_ITEMS]]


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value[:MAX_LIST_ITEMS] if isinstance(item, dict)]
