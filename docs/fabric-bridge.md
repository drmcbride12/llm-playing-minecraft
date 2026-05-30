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

## Current Checkpoint

This first checkpoint is a compiling Fabric client mod skeleton. The next
checkpoint adds the localhost controller protocol, compact observations, and
Baritone command execution.
