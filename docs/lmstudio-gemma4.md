# LM Studio And Gemma 4 Setup

This project targets a local LM Studio server running a Gemma 4 instruction
model, with `google/gemma-4-e4b` as the default local LM Studio model id and
16,384 tokens as the active context window.

## Install And Load

1. Install LM Studio.
2. Search for a Gemma 4 E4B instruction model or a compatible local/quantized
   variant.
3. Load the model in LM Studio.
4. Start the local server.
5. Confirm the server base URL. This project targets the native LM Studio API:

```text
http://localhost:1234/api/v1
```

## Configure This Project

Create `.env` from `.env.example` and keep the API key non-empty:

```env
MINECRAFT_LLM_BASE_URL=http://localhost:1234/api/v1
MINECRAFT_LLM_API_KEY=lm-studio-local-development-key
MINECRAFT_LLM_MODEL=google/gemma-4-e4b
MINECRAFT_LLM_CONTEXT_LENGTH=16384
```

LM Studio local development servers may not validate the key, but the program
requires it and sends it anyway. This keeps the code compatible with other
OpenAI-style endpoints later.

## Verify Connectivity

```powershell
python -m llm_playing_minecraft doctor
```

If the configured model is loaded, the doctor output should show LM Studio as
reachable and list the model id.

## If The Model Id Is Different

Run:

```powershell
python -m llm_playing_minecraft models
```

Then copy the exact id into `.env`:

```env
MINECRAFT_LLM_MODEL=the-model-id-reported-by-lm-studio
```

## Prompting Notes

Gemma 4 supports a normal `system` role. The runtime uses that role to pin the
agent contract:

- return one JSON object
- avoid slash commands
- avoid shell commands and file paths
- choose one small Baritone action
- use `done=true` only when the goal is satisfied

The temperature defaults to `0.2` because Minecraft control is an execution
problem, not a creative writing problem.

## Troubleshooting

`Could not reach LM Studio`

: Confirm LM Studio's local server is running and the base URL matches your
  server settings.

`HTTP 404` or `model not found`

: The model id in `.env` does not match what LM Studio is serving. Run the
  `models` command and copy the reported id.

Slow responses

: Try a smaller quantization, shorten the observation, or confirm that LM Studio
  is using the expected hardware acceleration.
