# Agent Strategy

The project goal is not just to ask an LLM for random Minecraft commands. The
agent should use Baritone as its hands and feet while the LLM supplies planning,
prioritization, memory, and communication.

## Core Loop

1. Read the user's long-term goal.
2. Read the latest Minecraft observation.
3. Decide the next concrete tactical step.
4. Emit one validated Baritone command or one useful chat message.
5. Observe the result and repeat.

## What The LLM Should Be Good At

### Resource Progression

Convert goals such as "beat the game" into staged resource plans:

- gather logs
- craft basic tools
- mine stone
- collect food
- find iron
- craft armor, shield, bucket, and tools
- find lava, water, villages, caves, fortresses, strongholds, or structures

The planner should choose concrete Baritone commands such as `#mine oak_log`,
`#mine stone`, `#explore`, `#goto x y z`, or `#farm`.

### Survival Judgement

When observations mention night, low health, hunger, mobs, lava, cliffs, or
dangerous dimensions, the LLM should balance the default bold movement profile
against the current situation. Bold does not mean reckless every turn.

Good actions include:

- `#stop` when Baritone is about to do something obviously bad
- a chat request for missing state
- mining or gathering a resource that unlocks safer next steps
- exploring when no known target exists

### Building And Long-Term Projects

For structure goals, the LLM should:

- ask for or reference a schematic name before using `#build`
- gather missing materials first
- stage the area, then build
- use chat for progress and missing-resource reports

### Communication

Chat is part of the design. The LLM can use `chat` to:

- report what it is about to do
- ask other agents for resources or scouting data
- tell the operator what observation is missing
- summarize progress toward a long-term goal

The LLM should not spam chat when a clear Baritone action is available.

## Default Movement Personality

The default `bold` Baritone profile assumes parkour and fast movement are
enabled. The LLM should take advantage of that by preferring direct, confident
routes and resource-gathering commands instead of overly timid wandering.

The profile is still a tool, not a command to ignore danger. If the observation
says the player is low health, in lava, starving, or carrying valuable gear near
a cliff, immediate survival outranks speed.
