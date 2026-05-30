# Prompt Contract

The LLM is asked to return exactly one JSON object. The program validates that
object before any transport sees it.

When using LM Studio's native API with Gemma 4, the response may include a
separate `reasoning` item and a final `message` item. The client discards the
reasoning item and validates only the final message content.

## Response Schema

```json
{
  "reason": "one short sentence explaining the immediate tactical reason",
  "chat": "optional short in-game chat message, or null",
  "baritone_command": "optional Baritone command beginning with #, or null",
  "wait_seconds": 0,
  "done": false
}
```

## Field Rules

| Field | Rule |
| --- | --- |
| `reason` | Required, non-empty, 500 characters or fewer. |
| `chat` | Optional, 500 characters or fewer. |
| `baritone_command` | Optional, one line, 200 characters or fewer, must be allowlisted. |
| `wait_seconds` | Integer from 0 to 300. |
| `done` | Boolean. Only true when the goal is already satisfied. |

At least one of `chat`, `baritone_command`, or `done=true` is required.
Commands such as `#mine`, `#goto`, `#build`, `#follow`, and `#set` must include
target arguments.

## Valid Example

```json
{
  "reason": "The player needs logs before crafting basic tools.",
  "chat": null,
  "baritone_command": "#mine oak_log",
  "wait_seconds": 3,
  "done": false
}
```

## Invalid Examples

Slash commands are rejected:

```json
{
  "reason": "Teleporting is not a normal survival action.",
  "baritone_command": "/tp 0 70 0",
  "wait_seconds": 1,
  "done": false
}
```

Unsupported Baritone commands are rejected:

```json
{
  "reason": "The command is not in the allowlist.",
  "baritone_command": "#unsupported thing",
  "wait_seconds": 1,
  "done": false
}
```

Targetless commands are rejected:

```json
{
  "reason": "The command does not say what to mine.",
  "baritone_command": "#mine",
  "wait_seconds": 1,
  "done": false
}
```

If validation fails, the agent emits:

```json
{
  "reason": "Rejected unsafe or invalid model output: ...",
  "chat": null,
  "baritone_command": "#stop",
  "wait_seconds": 1,
  "done": false
}
```

## Prompt Design Principles

- One action per model call.
- Use observations; do not invent state.
- Keep commands short and reversible.
- Fit prompts inside the configured 16,384-token context budget.
- Keep the operator in the loop until a direct client bridge is implemented.
- Treat Minecraft control as an execution system, not a chat demo.
