# Observation Contract

The agent should not use images, screenshots, video, or raw block-radius dumps.
Those approaches are expensive, brittle, and eat context quickly.

Instead, the Minecraft bridge should send compact, decision-oriented state. The
LLM needs to know what matters for choosing the next action, not every block in
a cube.

## Design Principles

- Summarize the world into facts, counts, nearest targets, hazards, and regions.
- Prefer reachable or visible points of interest over raw block coordinates.
- Include distance, direction, and confidence when available.
- Include Baritone state so the LLM knows whether it is idle, pathing, stuck, or
  failing.
- Include memory facts that matter for long goals, such as base location,
  village coordinates, nether portal location, and previous failures.
- Cap every list. If a list grows large, rank by usefulness.

## Recommended JSON Shape

```json
{
  "summary": "Morning plains spawn with trees, sheep, and exposed stone nearby.",
  "player": {
    "position": "0 64 0 overworld",
    "biome": "plains",
    "health": 20,
    "hunger": 20,
    "time": "morning"
  },
  "inventory": ["empty"],
  "baritone": {
    "status": "idle",
    "profile": "bold",
    "last_command": null,
    "last_error": null
  },
  "important_blocks": [
    {"block": "oak_log", "nearest": "8m north", "count": 14, "reachable": true},
    {"block": "stone", "nearest": "18m east hillside", "count": 40, "reachable": true}
  ],
  "entities": [
    {"type": "sheep", "nearest": "12m west", "count": 3},
    {"type": "zombie", "nearest": "none visible", "count": 0}
  ],
  "hazards": [
    {"type": "ravine", "nearest": "35m south", "severity": "medium"}
  ],
  "regions": [
    {"name": "oak grove", "direction": "north", "distance": 8, "resources": ["oak_log"]},
    {"name": "stone hillside", "direction": "east", "distance": 18, "resources": ["stone", "coal_ore"]}
  ],
  "memory": [
    "spawn is near 0 64 0",
    "no base established"
  ]
}
```

## What To Summarize

### Nearby Resources

Report the nearest useful blocks or regions:

- logs
- exposed stone
- coal, iron, copper, diamond, redstone
- water and lava
- crops, animals, villages
- sand, gravel, clay, dirt, cobblestone
- structure blocks or containers

### Hazards

Report hazards by type, distance, and severity:

- hostile mobs
- lava
- cliffs, ravines, void, deep drops
- powder snow
- drowning risk
- low hunger or health
- nightfall

### Baritone State

The LLM needs to know whether the previous action worked:

```json
{
  "baritone": {
    "status": "pathing",
    "last_command": "#mine oak_log",
    "distance_to_goal": 6,
    "stuck_ticks": 0,
    "last_error": null
  }
}
```

## Raw Block Cloud Fallback

If an early bridge accidentally sends a `blocks` list, the Python runtime will
collapse it into counts and coordinate ranges before prompting the LLM. This is
a fallback, not the target design.

Good:

```json
{"block": "oak_log", "count": 14, "nearest": "8m north", "reachable": true}
```

Avoid:

```json
[
  {"block": "air", "pos": {"x": 1, "y": 64, "z": 1}},
  {"block": "air", "pos": {"x": 1, "y": 64, "z": 2}}
]
```

## LLM Behavior

When information is missing, the LLM should ask for a compact fact, not a visual
input or a huge block list. Example chat:

```text
Please report nearest logs, exposed stone, food, hostile mobs, and Baritone status.
```
