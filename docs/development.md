# Development

The first implementation uses only the Python standard library. That keeps the
project easy to run while the architecture is still settling.

## Local Setup

With Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

## Run Tests

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests
```

## Run The CLI Without Installing

```powershell
$env:PYTHONPATH="src"
python -m llm_playing_minecraft doctor
```

## Run The CLI After Editable Install

```powershell
llm-playing-minecraft doctor
```

## Build Release Artifacts

```powershell
.\scripts\build_release.ps1
```

The script runs the Python tests, builds the controller exe, attempts to build
the Fabric bridge jar, and copies release-ready files to:

```text
dist/release/
```

If Windows blocks JDK 25 access from inside PowerShell script execution, run the
bridge build command from [fabric-bridge.md](fabric-bridge.md) first; the release
script will package the existing jar.

## Add A Transport

1. Create a class implementing `CommandTransport`.
2. Accept only `AgentAction` objects, never raw model text.
3. Keep action validation in `schema.py`.
4. Add tests for command rendering or execution behavior.
5. Document safety and setup in `docs/baritone-integration.md`.

## Add An Observation Source

Observation collection should be separate from transports. A future source might
read:

- Minecraft logs
- Fabric mod state
- Baritone status
- server events

Keep the output as plain text or JSON that the prompt builder can include in
the next model turn.
