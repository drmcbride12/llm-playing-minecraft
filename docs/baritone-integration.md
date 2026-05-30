# Baritone Integration

Baritone is a Minecraft client mod. Its `#` commands are typed into the client
chat box and interpreted by the mod in that client. This distinction matters:

- server RCON sends server commands
- Minecraft slash commands target server/game command handling
- Baritone `#` commands target the local client mod

Because of that, this project starts with a console transport instead of
pretending RCON can drive Baritone directly.

## Supported Command Allowlist

The first allowlist is deliberately small:

```text
#build
#explore
#farm
#follow
#goto
#mine
#path
#pause
#resume
#set
#stop
```

The validator rejects:

- slash commands such as `/op`, `/kill`, or `/tp`
- shell commands
- target-requiring commands without targets, such as bare `#mine`
- unsupported `#` commands
- multiline commands
- commands longer than 200 characters

If the model outputs an invalid command, the agent emits `#stop`.

## Current Workflow

1. Run Minecraft with Fabric and Baritone.
2. Apply the default `bold` profile if the client has not already been configured.
3. Run the planner with a goal and observation.
4. Read the validated action printed by the console transport.
5. Paste or type the Baritone command into the Minecraft client.
6. Provide the next observation.

Print the default profile:

```powershell
python -m llm_playing_minecraft baritone-profile --no-comments
```

Example:

```powershell
python -m llm_playing_minecraft run `
  --goal "Gather logs and craft a wooden pickaxe" `
  --interactive-observation `
  --steps 3
```

## Future Bridge Options

### Fabric Sidecar Mod

A small Fabric mod could expose a localhost socket or HTTP endpoint that accepts
validated chat text from this program and sends it through the local client
chat path. This is the cleanest route because it lives inside the Baritone
client process.

### Macro Bridge

A desktop macro bridge could focus the Minecraft window and type validated chat
text. This is easier to prototype but harder to make robust and safe.

### Bot Client

A bot client can join a server and act as the player. This is powerful, but it
usually means rethinking Baritone integration and authentication.

## Observation Strategy

Useful observations should include:

- player coordinates and dimension
- biome
- health, hunger, armor, and effects
- inventory summary
- nearby blocks, mobs, dangers, and structures
- time of day and weather
- current Baritone pathing status
- current short-term goal

The planner accepts plain text now, but JSON observations are a good target:

```json
{
  "position": {"x": 120, "y": 64, "z": -42, "dimension": "overworld"},
  "biome": "plains",
  "health": 20,
  "hunger": 18,
  "inventory": ["oak_log: 4"],
  "nearby_blocks": ["oak_log", "grass_block", "stone"],
  "nearby_mobs": [],
  "baritone_status": "idle"
}
```

## Default Bold Profile

`bold` is the default Baritone profile. It turns parkour on by default and also
enables sprinting, parkour ascends, parkour placement, diagonal descents,
overshoot descents, block placement, inventory movement, auto-tool, water-bucket
falls, and a small amount of no-water fall tolerance.

This profile is meant to make the bot play more like a confident survival player
who accepts some risk for speed and progress. It is still bounded by ordinary
Minecraft assumptions: the project does not enable lava walking, water walking,
or other settings that assume powers the player may not have.

See [baritone-bold-profile.md](baritone-bold-profile.md) for the full profile.
