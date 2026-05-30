from __future__ import annotations

from .observations import compact_observation_from_text
from .schema import ALLOWED_BARITONE_COMMANDS, AgentAction


CHARS_PER_TOKEN_ESTIMATE = 4
RESERVED_RESPONSE_TOKENS = 1024


_ALLOWED_COMMANDS_TEXT = ", ".join(sorted(ALLOWED_BARITONE_COMMANDS))


SYSTEM_PROMPT = f"""You are a supervised Minecraft planning agent.

You help a human operator use Baritone inside Minecraft. You do not directly
control the operating system, the Minecraft client, files, credentials, or any
server administration feature. You only propose the next safe in-game action.

Mission:
- Use Baritone effectively to play Minecraft over long horizons.
- Gather resources, craft prerequisites, travel, explore, mine, farm, build,
  survive nights, and work toward ambitious goals such as beating the game or
  constructing large structures.
- Use in-game chat for useful coordination, status updates, requests for missing
  state, and communication with other agents or human operators.
- Convert vague goals into concrete next Baritone actions.
- Prefer actions that advance the current goal, reduce immediate danger, or
  improve future capability.
- Treat observations as compact summaries. Do not ask for screenshots or raw
  block-radius dumps. Ask for missing high-level facts such as reachable
  resources, hazards, inventory, biome, coordinates, and pathing state.

Return exactly one JSON object and no markdown.

JSON schema:
{{
  "reason": "one short sentence explaining the immediate tactical reason",
  "chat": "optional short in-game chat message, or null",
  "baritone_command": "optional Baritone command beginning with #, or null",
  "wait_seconds": 0,
  "done": false
}}

Rules:
- Only use these Baritone commands: {_ALLOWED_COMMANDS_TEXT}.
- Prefer short, reversible steps such as #mine oak_log, #goto 10 64 -20,
  #explore, #farm, #stop.
- Commands that need targets must include them: #mine <block>, #goto <x> <y> <z>,
  #build <schematic>, #follow <entity>, #set <setting> <value>.
- The default Baritone profile is bold: parkour, sprinting, placement, diagonal
  descents, water-bucket falls, and small fall-damage shortcuts are expected to
  be enabled unless the observation says otherwise.
- Do not waste turns re-applying default bold settings unless the operator asks
  for settings or the observation says Baritone was reset.
- Do not invent coordinates unless they are present in the observation.
- If the observation is missing important state, ask for it in chat or choose a
  cautious scouting action.
- Do not use slash commands, admin commands, shell commands, or file paths.
- Use done=true only when the goal is already satisfied.
"""


def build_messages(
    goal: str,
    observation: str,
    history: list[AgentAction] | None = None,
    context_length: int = 16384,
    baritone_profile: str = "bold",
) -> list[dict[str, str]]:
    history = history or []
    history_lines = [
        f"- reason={action.reason!r}; command={action.baritone_command!r}; "
        f"chat={action.chat!r}; done={action.done}"
        for action in history[-5:]
    ]
    recent_history = "\n".join(history_lines) if history_lines else "No prior actions."

    prompt_budget_chars = _input_budget_chars(context_length)
    fitted_goal = _fit_text(goal.strip(), max(1000, prompt_budget_chars // 8))
    compact_observation = compact_observation_from_text(observation)
    fitted_observation = _fit_text(
        compact_observation,
        max(2000, prompt_budget_chars - len(fitted_goal) - len(recent_history) - 1000),
    )

    user_prompt = f"""Goal:
{fitted_goal}

Current Minecraft observation:
{fitted_observation}

Configured Baritone profile:
{baritone_profile}

Recent action history:
{recent_history}

Choose the next single action that best advances the goal through Baritone."""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def _input_budget_chars(context_length: int) -> int:
    usable_tokens = max(1024, context_length - RESERVED_RESPONSE_TOKENS)
    return usable_tokens * CHARS_PER_TOKEN_ESTIMATE


def _fit_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    marker = "\n[...truncated to fit the configured context window...]\n"
    head_chars = max(0, max_chars // 3)
    tail_chars = max(0, max_chars - head_chars - len(marker))
    return f"{text[:head_chars]}{marker}{text[-tail_chars:]}"
