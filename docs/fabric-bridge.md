# Fabric Bridge Mod

The Fabric bridge is the Minecraft-side piece of the project. Each Minecraft
client gets this mod. The controller program runs once on the PC, talks to LM
Studio, and coordinates one or more bridge clients.

## Build

```powershell
cd fabric-bridge
$env:JAVA_HOME="C:\Users\swage\Documents\jdk25-temurin\jdk-25.0.3+9"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
.\gradlew.bat build --stacktrace --console=plain
```

The mod jar will be under:

```text
fabric-bridge/build/libs/
```

The repository release script also copies the final jar to `dist/release/`.

## Runtime Protocol

By default each client reads:

```text
config/llm-playing-minecraft-bridge.properties
```

The default generated config points to:

```text
http://127.0.0.1:8765
```

Generated keys:

| Key | Default | Purpose |
| --- | --- | --- |
| `client_id` | generated UUID | Stable identity for this Minecraft client. Use a different value per client. |
| `controller_url` | `http://127.0.0.1:8765` | Local controller HTTP endpoint. |
| `auto_connect_server` | empty | Optional `host:port` to join from the title screen for dev or multi-client test runs. |
| `report_ticks` | `40` | Observation post interval. 40 ticks is about two seconds. |
| `poll_ticks` | `20` | Command poll interval. 20 ticks is about one second. |

Each client:

1. Posts compact observations to
   `/api/clients/{client_id}/observation`.
2. Polls `/api/clients/{client_id}/command?last_id=N`.
3. Executes returned `baritone_command` values through Baritone's command
   manager by reflection.

Because each client has its own `client_id`, one controller can coordinate
multiple Minecraft clients on the same PC with one LM Studio server.

## Local Multi-Client Pattern

Run one controller:

```powershell
llm-playing-minecraft-controller.exe serve `
  --goal "Survive the first day: gather wood, avoid danger, and keep moving productively"
```

Then launch as many Fabric clients as the PC can handle. Each client needs:

- Fabric Loader and Fabric API for Minecraft `26.1.2`
- Baritone for Minecraft `26.1.2`
- `llm-playing-minecraft-bridge-0.1.0.jar`
- a distinct `client_id` in `config/llm-playing-minecraft-bridge.properties`

All clients can point to the same `controller_url` and the same LM Studio model.

## Smoke-Tested Path

The current bridge was tested with:

- local controller on `127.0.0.1:8765`
- local Fabric server on `127.0.0.1:25565`
- bridge config `auto_connect_server=127.0.0.1:25565`
- LM Studio model id `google/gemma-4-e4b`

Observed results:

- bridge loaded in the client
- client auto-connected to the local server
- server logged the player joining
- manual controller command `#goto 45 92 8` reached Baritone
- LM Studio produced `#explore`
- Baritone accepted it and began exploring from a `GoalXZ`, with pathing stats
  printed in the Minecraft log

## Run The Controller

```powershell
$env:MINECRAFT_LLM_API_KEY="lm-studio-local-development-key"
python -m llm_playing_minecraft serve `
  --goal "Survive, gather resources, and build early-game capability"
```
