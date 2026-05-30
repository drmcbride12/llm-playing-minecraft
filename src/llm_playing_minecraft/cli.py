from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import time

from .agent import MinecraftAgent
from .baritone_profiles import (
    BaritoneProfileError,
    load_baritone_profile,
    render_profile_commands,
    render_profile_markdown,
)
from .bridge_server import BridgeController, run_bridge_server
from .config import (
    DEFAULT_BARITONE_PROFILE,
    AppConfig,
    ConfigError,
    load_env_file,
)
from .lmstudio_client import LLMApiError, LMStudioClient
from .schema import AgentAction, render_action
from .transports import ConsoleTransport


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "baritone-profile":
        load_env_file(args.env_file)
        try:
            return _baritone_profile(
                args,
                profile_name=os.environ.get(
                    "MINECRAFT_BARITONE_PROFILE",
                    DEFAULT_BARITONE_PROFILE,
                ),
            )
        except BaritoneProfileError as exc:
            print(f"baritone profile error: {exc}", file=sys.stderr)
            return 4

    try:
        config = AppConfig.from_env(args.env_file)
    except ConfigError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    client = LMStudioClient(config)

    try:
        if args.command == "doctor":
            return _doctor(config, client)
        if args.command == "models":
            return _models(client)
        if args.command == "plan":
            return _plan(args, client)
        if args.command == "run":
            return _run(args, client)
        if args.command == "serve":
            return _serve(args, client)
    except LLMApiError as exc:
        print(f"llm api error: {exc}", file=sys.stderr)
        return 3
    except BaritoneProfileError as exc:
        print(f"baritone profile error: {exc}", file=sys.stderr)
        return 4
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-playing-minecraft",
        description="Run a local LM Studio-backed Minecraft Baritone planning agent.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a simple KEY=VALUE env file. Defaults to .env.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check configuration and LM Studio reachability.")
    subparsers.add_parser("models", help="List models reported by the configured API.")

    profile_parser = subparsers.add_parser(
        "baritone-profile",
        help="Print a Baritone settings profile as #set commands, JSON, or Markdown.",
    )
    profile_parser.add_argument("--profile", default=None, help="Built-in profile name.")
    profile_parser.add_argument("--profile-file", type=Path, help="Load a profile JSON file.")
    profile_parser.add_argument(
        "--format",
        choices=("commands", "json", "markdown"),
        default="commands",
        help="Output format. Defaults to commands.",
    )
    profile_parser.add_argument(
        "--no-comments",
        action="store_true",
        help="For command output, print only runnable #set lines.",
    )

    plan_parser = subparsers.add_parser("plan", help="Ask the LLM for one action.")
    _add_goal_observation_args(plan_parser)

    run_parser = subparsers.add_parser("run", help="Run a supervised planning loop.")
    _add_goal_observation_args(run_parser)
    run_parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Maximum planning steps to run. Defaults to 1.",
    )
    run_parser.add_argument(
        "--interactive-observation",
        action="store_true",
        help="Prompt for a fresh observation before every step.",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Run the local multi-client Minecraft bridge controller.",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    serve_parser.add_argument("--port", type=int, default=8765, help="Bind port.")
    serve_parser.add_argument(
        "--goal",
        required=True,
        help="Default goal assigned to every connected Minecraft client.",
    )
    serve_parser.add_argument(
        "--no-auto-plan",
        action="store_true",
        help="Accept observations but only send manually queued commands.",
    )

    return parser


def _add_goal_observation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", required=True, help="Minecraft objective for the agent.")
    parser.add_argument(
        "--observation",
        help="Plain text or JSON description of the current Minecraft state.",
    )
    parser.add_argument(
        "--observation-file",
        type=Path,
        help="Read the current Minecraft observation from a file.",
    )


def _doctor(config: AppConfig, client: LMStudioClient) -> int:
    print("configuration")
    print(f"  base_url: {config.base_url}")
    print(f"  model: {config.model}")
    print(f"  context_length: {config.context_length}")
    print(f"  baritone_profile: {config.baritone_profile}")
    print(f"  api_key: {'set' if config.api_key else 'missing'}")
    print("api")

    records = client.list_model_records()
    print(f"  reachable: yes")
    if records:
        print("  models:")
        for record in records:
            model_id = record.get("key") or record.get("id")
            if not model_id:
                continue
            model = str(model_id)
            marker = " (configured)" if model == config.model else ""
            loaded_contexts = [
                str(instance.get("config", {}).get("context_length"))
                for instance in record.get("loaded_instances", [])
                if instance.get("config", {}).get("context_length")
            ]
            context_note = (
                f"; loaded context={', '.join(loaded_contexts)}"
                if loaded_contexts
                else ""
            )
            print(f"    - {model}{marker}{context_note}")
    else:
        print("  models: none reported")
    return 0


def _models(client: LMStudioClient) -> int:
    for model in client.list_models():
        print(model)
    return 0


def _baritone_profile(args: argparse.Namespace, profile_name: str) -> int:
    profile = load_baritone_profile(
        profile_name=args.profile or profile_name,
        profile_file=args.profile_file,
    )

    if args.format == "json":
        print(json.dumps(profile.to_dict(), indent=2, sort_keys=True))
    elif args.format == "markdown":
        print(render_profile_markdown(profile))
    else:
        print(render_profile_commands(profile, include_comments=not args.no_comments))
    return 0


def _plan(args: argparse.Namespace, client: LMStudioClient) -> int:
    agent = MinecraftAgent(client)
    action = agent.plan(args.goal, _read_observation(args))
    print(render_action(action))
    return 0


def _run(args: argparse.Namespace, client: LMStudioClient) -> int:
    if args.steps < 1:
        print("--steps must be at least 1", file=sys.stderr)
        return 2

    agent = MinecraftAgent(client)
    transport = ConsoleTransport()
    history: list[AgentAction] = []

    for step in range(1, args.steps + 1):
        observation = _read_observation(args, prompt=args.interactive_observation)
        action = agent.plan(args.goal, observation, history)
        history.append(action)

        print(f"\nstep {step}")
        print(render_action(action))
        print(transport.execute(action))

        if action.done:
            return 0
        if action.wait_seconds:
            time.sleep(action.wait_seconds)

    return 0


def _serve(args: argparse.Namespace, client: LMStudioClient) -> int:
    controller = BridgeController.from_agent(
        MinecraftAgent(client),
        default_goal=args.goal,
        auto_plan=not args.no_auto_plan,
    )
    run_bridge_server(args.host, args.port, controller)
    return 0


def _read_observation(args: argparse.Namespace, prompt: bool = False) -> str:
    if prompt:
        typed = input("Minecraft observation> ").strip()
        if typed:
            return typed

    if args.observation_file:
        return args.observation_file.read_text(encoding="utf-8")

    if args.observation:
        return args.observation

    return (
        "No live Minecraft observation was provided. Assume the player is safe, "
        "stationary, and waiting for the next supervised Baritone instruction."
    )


if __name__ == "__main__":
    raise SystemExit(main())
