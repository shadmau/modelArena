"""LLM player adapter using LiteLLM for unified API access."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from engine.models import PlayerInfo

logger = logging.getLogger(__name__)

DEFAULT_MODELS = {
    "Claude": "anthropic/claude-sonnet-4-6",
    "GPT": "openai/gpt-5.2",
    "Gemini": "gemini/gemini-3.1-pro-preview",
    "DeepSeek": "deepseek/deepseek-chat",
    "Llama": "openrouter/meta-llama/llama-4-maverick",
    "Grok": "xai/grok-4-1-fast-reasoning",
}

PLAYER_COLORS = {
    "Claude": "#D97706",
    "GPT": "#10B981",
    "Gemini": "#3B82F6",
    "DeepSeek": "#8B5CF6",
    "Llama": "#EF4444",
    "Grok": "#F97316",
}

# Regex to strip markdown code fences: ```json ... ``` or ``` ... ```
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", re.DOTALL)


def get_default_players() -> list[PlayerInfo]:
    return [
        PlayerInfo(name=name, model=model, avatar_color=PLAYER_COLORS.get(name, "#666"))
        for name, model in DEFAULT_MODELS.items()
    ]


@dataclass
class CallStats:
    """Track LLM call costs and usage."""
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    retries: int = 0
    failures: int = 0


class LLMPlayer:
    def __init__(self, player_info: PlayerInfo, temperature: float = 0.9):
        self.info = player_info
        self.temperature = temperature
        self.stats = CallStats()

    def call(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> dict[str, str]:
        """Call the LLM and parse JSON response. Returns dict with expected keys."""
        from litellm import completion

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        content = ""
        for attempt in range(max_retries):
            try:
                self.stats.total_calls += 1
                response = completion(
                    model=self.info.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=1024,
                )
                content = response.choices[0].message.content.strip()

                if hasattr(response, "usage") and response.usage:
                    self.stats.total_prompt_tokens += response.usage.prompt_tokens or 0
                    self.stats.total_completion_tokens += response.usage.completion_tokens or 0

                return _parse_json_response(content)
            except json.JSONDecodeError:
                self.stats.retries += 1
                logger.warning(
                    f"[{self.info.name}] Invalid JSON on attempt {attempt + 1}, retrying"
                )
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "user",
                    "content": (
                        "Your response was not valid JSON. "
                        "Respond with ONLY a JSON object, no markdown, no explanation."
                    ),
                })
            except Exception as e:
                self.stats.retries += 1
                logger.error(f"[{self.info.name}] API error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    self.stats.failures += 1
                    return _fallback_response(self.info.name)

        self.stats.failures += 1
        return _fallback_response(self.info.name)


def _parse_json_response(content: str) -> dict[str, str]:
    """Parse JSON from LLM response, handling common formatting issues."""
    fence_match = _CODE_FENCE_RE.match(content)
    if fence_match:
        content = fence_match.group(1)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first JSON object from surrounding text
    brace_start = content.find("{")
    brace_end = content.rfind("}")
    if brace_start != -1 and brace_end > brace_start:
        return json.loads(content[brace_start : brace_end + 1])

    raise json.JSONDecodeError("No valid JSON found", content, 0)


def _fallback_response(player_name: str) -> dict[str, str]:
    return {
        "public_statement": f"[{player_name} failed to respond]",
        "private_reasoning": "[API call failed after retries]",
        "vote": "",
    }
