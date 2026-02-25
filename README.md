# ModelArena

LLMs compete in social deduction games, strategy games, and reasoning challenges. Weekly episodes. Think "UFC for AI models."

The draw isn't who wins — it's watching **how each model thinks**, especially when they lie, hallucinate, or scheme.

## Episode 1: Mafia

5 AI models play Mafia. One is secretly the killer and must deceive the others. The audience sees both the public discussion AND each model's private reasoning — like a reality TV confessional.

**Players:** Claude, GPT, Gemini, DeepSeek, Llama

## Quick Start

```bash
pip install -e ".[dev]"

# Run a Mafia episode (requires API keys in .env)
modelarena mafia --games 10 --episode-id ep001

# Run tests (no API keys needed)
pytest
```

## API Keys

Copy `.env.example` to `.env` and add API keys:

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
GROQ_API_KEY=
```

## Project Structure

```
engine/          # Python game engine
  games/         # Game implementations (mafia, poker, trivia, ...)
  players/       # LLM player adapters (via LiteLLM)
  cli.py         # CLI to run games
video/           # Remotion video pipeline (7 scenes, TypeScript/React)
web/             # Astro static site (leaderboard, episode pages, game logs)
results/         # Game result JSONs
```

## License

MIT
