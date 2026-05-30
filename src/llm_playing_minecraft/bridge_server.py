from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Lock
from time import time
from typing import Callable
from urllib.parse import parse_qs, unquote, urlparse

from .agent import MinecraftAgent
from .schema import AgentAction


Planner = Callable[[str, str, list[AgentAction]], AgentAction]


@dataclass
class ClientState:
    client_id: str
    goal: str
    observation: str = ""
    command: dict | None = None
    command_id: int = 0
    history: list[AgentAction] = field(default_factory=list)
    connected_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    planning: bool = False
    last_error: str | None = None

    def public(self) -> dict:
        return {
            "client_id": self.client_id,
            "goal": self.goal,
            "has_observation": bool(self.observation),
            "command_id": self.command_id,
            "planning": self.planning,
            "connected_at": self.connected_at,
            "updated_at": self.updated_at,
            "last_error": self.last_error,
        }


class BridgeController:
    """Coordinates Minecraft bridge clients and the LLM planner."""

    def __init__(
        self,
        planner: Planner,
        default_goal: str,
        auto_plan: bool = True,
        max_workers: int = 4,
    ):
        self._planner = planner
        self._default_goal = default_goal
        self._auto_plan = auto_plan
        self._clients: dict[str, ClientState] = {}
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    @classmethod
    def from_agent(
        cls,
        agent: MinecraftAgent,
        default_goal: str,
        auto_plan: bool = True,
    ) -> "BridgeController":
        return cls(
            planner=lambda goal, observation, history: agent.plan(goal, observation, history),
            default_goal=default_goal,
            auto_plan=auto_plan,
        )

    def list_clients(self) -> list[dict]:
        with self._lock:
            return [client.public() for client in self._clients.values()]

    def client_public(self, client_id: str) -> dict:
        with self._lock:
            return self._client(client_id).public()

    def set_goal(self, client_id: str, goal: str) -> dict:
        with self._lock:
            client = self._client(client_id)
            client.goal = goal
            client.updated_at = time()
            return client.public()

    def update_observation(self, client_id: str, observation: str) -> dict:
        with self._lock:
            client = self._client(client_id)
            client.observation = observation
            client.updated_at = time()
            public = client.public()

        if self._auto_plan:
            self._schedule_plan(client_id)
        return public

    def queue_manual_command(
        self,
        client_id: str,
        baritone_command: str | None = None,
        chat: str | None = None,
        reason: str = "Manual operator command.",
    ) -> dict:
        action = AgentAction(
            reason=reason,
            chat=chat,
            baritone_command=baritone_command,
            wait_seconds=0,
            done=False,
        )
        return self._queue_action(client_id, action)

    def command_for(self, client_id: str, last_id: int) -> dict:
        with self._lock:
            client = self._client(client_id)
            if client.command is None or client.command_id <= last_id:
                return {"command": None}
            return {"command": dict(client.command)}

    def _schedule_plan(self, client_id: str) -> None:
        with self._lock:
            client = self._client(client_id)
            if client.planning or not client.observation or not client.goal:
                return
            client.planning = True

        self._executor.submit(self._plan_for_client, client_id)

    def _plan_for_client(self, client_id: str) -> None:
        with self._lock:
            client = self._client(client_id)
            goal = client.goal
            observation = client.observation
            history = list(client.history)

        try:
            action = self._planner(goal, observation, history)
            self._queue_action(client_id, action)
            error = None
        except Exception as exc:
            error = str(exc)

        with self._lock:
            client = self._client(client_id)
            client.planning = False
            client.last_error = error
            client.updated_at = time()

    def _queue_action(self, client_id: str, action: AgentAction) -> dict:
        with self._lock:
            client = self._client(client_id)
            client.command_id += 1
            client.history.append(action)
            client.command = {
                "id": client.command_id,
                "reason": action.reason,
                "chat": action.chat,
                "baritone_command": action.baritone_command,
                "done": action.done,
            }
            client.updated_at = time()
            return dict(client.command)

    def _client(self, client_id: str) -> ClientState:
        if client_id not in self._clients:
            self._clients[client_id] = ClientState(
                client_id=client_id,
                goal=self._default_goal,
            )
        return self._clients[client_id]


def run_bridge_server(host: str, port: int, controller: BridgeController) -> None:
    server = ThreadingHTTPServer((host, port), _handler(controller))
    print(f"llm-playing-minecraft bridge server listening on http://{host}:{port}")
    server.serve_forever()


def _handler(controller: BridgeController) -> type[BaseHTTPRequestHandler]:
    class BridgeRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            parts = _parts(parsed.path)

            if parts == ["health"]:
                self._json({"ok": True})
            elif parts == ["api", "clients"]:
                self._json({"clients": controller.list_clients()})
            elif len(parts) == 3 and parts[:2] == ["api", "clients"]:
                self._json(controller.client_public(parts[2]))
            elif len(parts) == 4 and parts[:2] == ["api", "clients"] and parts[3] == "command":
                query = parse_qs(parsed.query)
                last_id = int(query.get("last_id", ["0"])[0])
                self._json(controller.command_for(parts[2], last_id))
            else:
                self._json({"error": "not found"}, status=404)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            parts = _parts(parsed.path)
            body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode("utf-8")

            if len(parts) == 4 and parts[:2] == ["api", "clients"] and parts[3] == "observation":
                self._json(controller.update_observation(parts[2], body))
            elif len(parts) == 4 and parts[:2] == ["api", "clients"] and parts[3] == "goal":
                payload = _json_body(body)
                self._json(controller.set_goal(parts[2], str(payload.get("goal", ""))))
            elif len(parts) == 4 and parts[:2] == ["api", "clients"] and parts[3] == "command":
                payload = _json_body(body)
                self._json(
                    controller.queue_manual_command(
                        parts[2],
                        baritone_command=payload.get("baritone_command"),
                        chat=payload.get("chat"),
                        reason=str(payload.get("reason", "Manual operator command.")),
                    )
                )
            else:
                self._json({"error": "not found"}, status=404)

        def log_message(self, format: str, *args) -> None:
            return

        def _json(self, payload: dict, status: int = 200) -> None:
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return BridgeRequestHandler


def _parts(path: str) -> list[str]:
    return [unquote(part) for part in path.split("/") if part]


def _json_body(body: str) -> dict:
    if not body.strip():
        return {}
    value = json.loads(body)
    if not isinstance(value, dict):
        raise ValueError("expected JSON object body")
    return value
