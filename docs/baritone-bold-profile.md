# Bold Baritone Profile

The built-in `bold` profile is the project's default movement personality.
Parkour is on by default.

The goal is to mimic a confident human player's risk/reward choices: sprint,
parkour, place blocks, take small fall damage, and try water-bucket descents
when equipped.

Print it as commands:

```powershell
python -m llm_playing_minecraft baritone-profile --no-comments
```

Print it as Markdown:

```powershell
python -m llm_playing_minecraft baritone-profile --format markdown
```

## Source

The packaged profile lives at:

```text
src/llm_playing_minecraft/profiles/baritone_bold.json
```

The CLI loads that JSON, renders `#set <setting> <value>` commands, and includes
the configured profile name in planner prompts.

## Highlights

| Setting | Value | Why |
| --- | --- | --- |
| `allowSprint` | `true` | Move like a player who is trying to get somewhere. |
| `sprintAscends` | `true` | Preserve speed up slopes and stairs. |
| `allowParkour` | `true` | Core risky traversal behavior, enabled by default. |
| `allowParkourAscend` | `true` | Allow parkour in upward routes. |
| `allowParkourPlace` | `true` | Let Baritone place blocks during parkour movement. |
| `allowDiagonalDescend` | `true` | Permit faster diagonal descents. |
| `allowOvershootDiagonalDescend` | `true` | Accept slight sprint overshoot on descents. |
| `allowWaterBucketFall` | `true` | Enable bucket-clutch-style fall plans. |
| `maxFallHeightNoWater` | `5` | Accept minor fall damage when it buys speed. |
| `maxFallHeightBucket` | `22` | Allow high-risk bucket falls below unarmored lethal height. |
| `jumpPenalty` | `0.0` | Stop discouraging jumps in path cost. |
| `blockPlacementPenalty` | `2.0` | Make bridging and pillaring routes more competitive. |
| `avoidance` | `false` | Do not add conservative mob/spawner avoidance costs by default. |

## Deliberately Not Enabled

These settings are not part of `bold` because they require external abilities or
turn risk into nonsense:

- `assumeWalkOnLava`
- `assumeWalkOnWater`
- `assumeSafeWalk`
- `allowVines`

The profile should feel brave, not delusional.

## Operational Notes

`maxFallHeightNoWater=5` can cause fall damage. `maxFallHeightBucket=22` assumes
the bot has a water bucket and that the clutch succeeds. Use a lower value for
hardcore worlds, important gear, or servers where death recovery is expensive.

If a future Fabric bridge applies settings automatically, it should still load
this JSON file rather than duplicating the settings in code.
