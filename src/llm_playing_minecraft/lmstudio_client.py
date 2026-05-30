from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import AppConfig


class LLMApiError(RuntimeError):
    """Raised when the LM Studio API cannot complete a request."""


class LMStudioClient:
    """Tiny client for LM Studio's native local API."""

    def __init__(self, config: AppConfig):
        self.config = config

    def list_models(self) -> list[str]:
        models: list[str] = []
        for item in self.list_model_records():
            model_id = item.get("key") or item.get("id")
            if model_id:
                models.append(str(model_id))
        return models

    def list_model_records(self) -> list[dict[str, Any]]:
        payload = self._request_json("GET", "/models")
        if isinstance(payload.get("models"), list):
            return list(payload["models"])
        if isinstance(payload.get("data"), list):
            return list(payload["data"])
        return []

    def chat(self, messages: list[dict[str, str]]) -> str:
        system_prompt = "\n\n".join(
            message["content"] for message in messages if message["role"] == "system"
        )
        input_text = "\n\n".join(
            f"{message['role']}: {message['content']}"
            for message in messages
            if message["role"] != "system"
        )

        body: dict[str, Any] = {
            "model": self.config.model,
            "system_prompt": system_prompt,
            "input": input_text,
            "temperature": self.config.temperature,
        }

        payload = self._request_json("POST", "/chat", body)
        return extract_chat_content(payload)

    def _request_json(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self._url(path),
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMApiError(f"LM Studio returned HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise LLMApiError(
                f"Could not reach LM Studio at {self.config.base_url}: {exc.reason}"
            ) from exc

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMApiError(f"LM Studio returned non-JSON data: {raw[:500]!r}") from exc

    def _url(self, path: str) -> str:
        return f"{self.config.base_url}/{path.lstrip('/')}"


def extract_chat_content(payload: dict[str, Any]) -> str:
    """Extract final assistant text from native or OpenAI-style responses."""

    output = payload.get("output")
    if isinstance(output, list):
        message_parts = [
            item.get("content")
            for item in output
            if isinstance(item, dict) and item.get("type") == "message"
        ]
        message_parts = [part for part in message_parts if part]
        if message_parts:
            return str(message_parts[-1])

    try:
        return str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMApiError(f"Unexpected chat response shape: {payload!r}") from exc
