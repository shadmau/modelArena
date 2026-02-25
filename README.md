# ModelArena

LLMs play games against each other. Each model's public moves and private reasoning are captured, rendered as video, and published.

Currently supports Mafia. More games planned.

## Setup

```bash
pip install -e ".[dev]"
cp .env.example .env  # add API keys
```

## Usage

```bash
modelarena mafia --games 10 --episode-id ep001

# Dry run with mock players (no API keys)
modelarena mafia --dry-run --games 3

# Run tests
pytest
```

## API Keys

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
GROQ_API_KEY=
```

## Structure

```
engine/          # Game engine (Python, LiteLLM)
video/           # Video renderer (Remotion, React)
web/             # Website (Astro, static)
results/         # Game result JSONs (committed)
```

## License

MIT