# Configuration

The agent reads a simple `.env` file first, then falls back to process
environment variables. Existing process variables win over `.env` entries.

## Required Variables

| Variable | Required | Description |
| --- | --- | --- |
| `MINECRAFT_LLM_API_KEY` | yes | API key sent as `Authorization: Bearer ...`. |

LM Studio commonly accepts any non-empty key for local development. This program
still requires a key because every runtime should use the same authenticated API
shape from the beginning.

Aliases are accepted in this order:

```text
MINECRAFT_LLM_API_KEY
LMSTUDIO_API_KEY
OPENAI_API_KEY
```

## Optional Variables

| Variable | Default | Description |
| --- | --- | --- |
| `MINECRAFT_LLM_BASE_URL` | `http://localhost:1234/api/v1` | LM Studio native API base URL. |
| `MINECRAFT_LLM_MODEL` | `google/gemma-4-e4b` | Model id sent in chat requests. |
| `MINECRAFT_LLM_CONTEXT_LENGTH` | `16384` | Active planner context budget in tokens. |
| `MINECRAFT_LLM_TIMEOUT_SECONDS` | `60` | HTTP timeout for local inference. |
| `MINECRAFT_LLM_TEMPERATURE` | `0.2` | Sampling temperature. |
| `MINECRAFT_BARITONE_PROFILE` | `bold` | Baritone settings profile name included in prompts and rendered by the CLI. |

Base URL and model aliases:

```text
MINECRAFT_LLM_BASE_URL -> LMSTUDIO_BASE_URL
MINECRAFT_LLM_MODEL -> LMSTUDIO_MODEL
```

## Example `.env`

```env
MINECRAFT_LLM_BASE_URL=http://localhost:1234/api/v1
MINECRAFT_LLM_API_KEY=lm-studio-local-development-key
MINECRAFT_LLM_MODEL=google/gemma-4-e4b
MINECRAFT_LLM_CONTEXT_LENGTH=16384
MINECRAFT_LLM_TEMPERATURE=0.2
MINECRAFT_LLM_TIMEOUT_SECONDS=60
MINECRAFT_BARITONE_PROFILE=bold
```

## Choosing the Model Id

The repository default is the Hugging Face id:

```text
google/gemma-4-e4b
```

Some LM Studio downloads expose a local quantized id instead. To inspect what
your server reports, run:

```powershell
python -m llm_playing_minecraft models
```

If the output differs from `google/gemma-4-e4b`, set
`MINECRAFT_LLM_MODEL` to the reported value.

## Context Length

The current design target is:

```env
MINECRAFT_LLM_CONTEXT_LENGTH=16384
```

The prompt builder uses this as a rough budget. It reserves room for the model's
response, then trims very large goals or observations before calling LM Studio.
LM Studio itself controls the actual loaded model context length.

## Baritone Profile

The default profile is:

```env
MINECRAFT_BARITONE_PROFILE=bold
```

Print the configured profile as runnable Baritone commands:

```powershell
python -m llm_playing_minecraft baritone-profile --no-comments
```

Print the same profile as Markdown documentation:

```powershell
python -m llm_playing_minecraft baritone-profile --format markdown
```
