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

## Runtime Protocol

By default each client reads:

```text
config/llm-playing-minecraft-bridge.properties
```

The default generated config points to:

```text
http://127.0.0.1:8765
```

Each client:

1. Posts compact observations to
   `/api/clients/{client_id}/observation`.
2. Polls `/api/clients/{client_id}/command?last_id=N`.
3. Executes returned `baritone_command` values through Baritone's command
   manager by reflection.

Because each client has its own `client_id`, one controller can coordinate
multiple Minecraft clients on the same PC with one LM Studio server.

## Run The Controller

```powershell
$env:MINECRAFT_LLM_API_KEY="lm-studio-local-development-key"
python -m llm_playing_minecraft serve `
  --goal "Survive, gather resources, and build early-game capability"
```
