"""LLM player adapter using LiteLLM for unified API access."""

from __future__ import annotations

import json
import logging
from typing import Any

from litellm import completion

from engine.models import PlayerInfo

logger = logging.getLogger(__name__)

# Model name mapping for LiteLLM
DEFAULT_MODELS = {
    "Claude": "anthropic/claude-sonnet-4-20250514",
    "GPT": "openai/gpt-4o",
    "Gemini": "gemini/gemini-2.0-flash",
    "DeepSeek": "deepseek/deepseek-chat",
    "Llama": "groq/llama-3.3-70b-versatile",
}

PLAYER_COLORS = {
    "Claude": "#D97706",
    "GPT": "#10B981",
    "Gemini": "#3B82F6",
    "DeepSeek": "#8B5CF6",
    "Llama": "#EF4444",
}


def get_default_players() -> list[PlayerInfo]:
    return [
        PlayerInfo(name=name, model=model, avatar_color=PLAYER_COLORS.get(name, "#666"))
        for name, model in DEFAULT_MODELS.items()
    ]


class LLMPlayer:
    def __init__(self, player_info: PlayerInfo, temperature: float = 0.9):
        self.info = player_info
        self.temperature = temperature

    def call(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> dict[str, str]:
        """Call the LLM and parse JSON response. Returns dict with expected keys."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(max_retries):
            try:
                response = completion(
                    model=self.info.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=1024,
                )
                content = response.choices[0].message.content.strip()
                return self._parse_response(content)
            except json.JSONDecodeError:
                logger.warning(
                    f"[{self.info.name}] Invalid JSON on attempt {attempt + 1}, retrying"
                )
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": "Your response was not valid JSON. Please respond ONLY with a JSON object.",
                })
            except Exception as e:
                logger.error(f"[{self.info.name}] API error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return self._fallback_response()

        return self._fallback_response()

    def _parse_response(self, content: str) -> dict[str, str]:
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            content = "\n".join(lines)
        return json.loads(content)

    def _fallback_response(self) -> dict[str, str]:
        return {
            "public_statement": f"[{self.info.name} failed to respond]",
            "private_reasoning": "[API call failed after retries]",
            "vote": "",
        }
