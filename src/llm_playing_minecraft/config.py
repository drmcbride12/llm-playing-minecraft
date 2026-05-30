from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


DEFAULT_BASE_URL = "http://localhost:1234/api/v1"
DEFAULT_MODEL = "google/gemma-4-e4b"
DEFAULT_CONTEXT_LENGTH = 16384
DEFAULT_BARITONE_PROFILE = "bold"


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


def load_env_file(path: str | Path | None = ".env") -> None:
    """Load simple KEY=VALUE entries from an env file without extra packages."""

    if path is None:
        return

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {value!r}") from exc


def _int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got {value!r}") from exc


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for the local LM Studio-backed agent."""

    base_url: str
    api_key: str
    model: str
    context_length: int
    timeout_seconds: float
    temperature: float
    baritone_profile: str

    @classmethod
    def from_env(cls, env_file: str | Path | None = ".env") -> "AppConfig":
        load_env_file(env_file)

        api_key = _first_env(
            "MINECRAFT_LLM_API_KEY",
            "LMSTUDIO_API_KEY",
            "OPENAI_API_KEY",
        )
        if not api_key:
            raise ConfigError(
                "Set MINECRAFT_LLM_API_KEY in your environment or .env file. "
                "LM Studio may accept a local placeholder, but the program "
                "always sends a Bearer API key."
            )

        base_url = _first_env("MINECRAFT_LLM_BASE_URL", "LMSTUDIO_BASE_URL")
        model = _first_env("MINECRAFT_LLM_MODEL", "LMSTUDIO_MODEL")

        context_length = _int_env(
            "MINECRAFT_LLM_CONTEXT_LENGTH",
            DEFAULT_CONTEXT_LENGTH,
        )
        if context_length < 2048:
            raise ConfigError("MINECRAFT_LLM_CONTEXT_LENGTH must be at least 2048")

        return cls(
            base_url=(base_url or DEFAULT_BASE_URL).rstrip("/"),
            api_key=api_key,
            model=model or DEFAULT_MODEL,
            context_length=context_length,
            timeout_seconds=_float_env("MINECRAFT_LLM_TIMEOUT_SECONDS", 60.0),
            temperature=_float_env("MINECRAFT_LLM_TEMPERATURE", 0.2),
            baritone_profile=os.environ.get(
                "MINECRAFT_BARITONE_PROFILE",
                DEFAULT_BARITONE_PROFILE,
            ),
        )
