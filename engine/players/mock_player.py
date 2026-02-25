"""Mock LLM player for testing and dry runs without API keys.

Generates role-aware responses with enough variety for realistic testing:
- Town players analyze, accuse, and coordinate votes
- Mafia players deflect and redirect
- Responses reference other players by name
"""

from __future__ import annotations

import hashlib
import random

from engine.models import PlayerInfo, Role


_TOWN_STATEMENTS = [
    "I've been watching everyone carefully. {suspect} has been unusually quiet about their own position — that's a classic deflection tactic. Why aren't they committing to any analysis?",
    "Look at the pattern here. {suspect} agreed with everyone initially, then started subtly pointing fingers. That's textbook Mafia behavior — they're trying to build trust before redirecting.",
    "I'm town and I'm standing by that. {suspect}'s last response didn't address the actual accusations — they just changed the subject. That tells me everything I need to know.",
    "{suspect} keeps making vague statements instead of committing to real analysis. Everyone else is engaging with specifics. Why is {suspect} the exception?",
    "I want to point out that {suspect} was quick to accuse someone else. In my experience, early accusers are often trying to control the narrative before suspicion lands on them.",
    "Notice how {suspect} hasn't actually defended themselves when questioned. They just pivot to someone else. That's not how an innocent player behaves.",
    "Let me be direct: {suspect} is my top suspect. Their statements are designed to look analytical without actually contributing anything useful. It's performance, not investigation.",
    "I've been keeping track, and {suspect} has shifted their position multiple times already. Town players don't do that — they follow the evidence. Mafia players hedge.",
]

_MAFIA_STATEMENTS = [
    "I think we're overlooking {scapegoat}. They've been flying under the radar while everyone argues. That's the real Mafia strategy — let others fight while you stay invisible.",
    "I agree with some of the points raised, but honestly {scapegoat} concerns me more. Their analysis feels rehearsed, like they already know the answer and are working backwards.",
    "Let's not rush to judgment. I've been analyzing everyone and {scapegoat}'s behavior stands out. They keep agreeing with the majority — that's exactly how you blend in.",
    "Everyone's focused on the wrong person. {scapegoat} hasn't really defended themselves convincingly. Real town players fight harder when accused.",
    "I'm as town as they come, and my read is clear: {scapegoat} is playing it too safe. They never commit to a strong opinion. The Mafia player avoids making enemies.",
    "Has anyone else noticed {scapegoat} has been following the crowd every single round? That's not analysis — that's camouflage. I think they're our Mafia.",
    "I respect the arguments against me, but look at {scapegoat}. They haven't offered a single original observation. Everything they say is just agreeing with someone else.",
]

_TOWN_REASONING = [
    "I need to find the Mafia. {suspect} is my top suspect — their statements feel performative rather than genuine. They're saying the right things but nothing original.",
    "Reading the discussion carefully, {suspect}'s behavior is the most inconsistent. They agree, then disagree, then change the subject. Classic deflection pattern.",
    "I'm fairly confident about {suspect}. Their public statements are carefully constructed to avoid committing to anything. Innocent players don't need to be that careful.",
    "This is tough. I think {suspect} is Mafia but I'm not 100% sure. Their lack of strong opinions is suspicious — town players should care more.",
]

_MAFIA_REASONING = [
    "I need to deflect suspicion. Pointing at {scapegoat} should work — nobody has strong feelings about them yet, so my accusation won't seem forced.",
    "The town is getting organized. I need to break up their consensus by introducing doubt about {scapegoat}. If I can split the vote, I survive another round.",
    "I'm worried about {threat}. They seem to be reading the game well. I need to either get them eliminated or discredit them before they figure me out.",
    "Playing it calm. If I accuse {scapegoat} with confidence, it makes me look like an active town player. The key is to seem helpful while being destructive.",
]


class MockLLMPlayer:
    """Mock player that generates role-aware responses without API calls."""

    def __init__(self, player_info: PlayerInfo, temperature: float = 0.9):
        self.info = player_info
        self.temperature = temperature
        self._role: Role | None = None
        self._call_count = 0
        self._last_suspect: str | None = None  # Track who we accused for voting consistency

    def call(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> dict[str, str]:
        """Generate a mock response based on role and context."""
        self._call_count += 1

        # Detect role from system prompt
        if "You are the MAFIA" in system_prompt:
            self._role = Role.MAFIA
        elif "TOWN" in system_prompt:
            self._role = Role.TOWN

        alive = self._parse_alive(user_prompt)
        others = [n for n in alive if n != self.info.name]

        if "VOTING" in user_prompt or "TIME TO VOTE" in user_prompt:
            return self._mock_vote(others)
        else:
            return self._mock_discussion(others)

    def _mock_discussion(self, others: list[str]) -> dict[str, str]:
        if not others:
            others = ["Unknown"]

        # Use a deterministic-ish selection based on call count for variety
        idx = self._call_count

        if self._role == Role.MAFIA:
            scapegoat = others[idx % len(others)]
            threat = others[(idx + 1) % len(others)]
            self._last_suspect = scapegoat
            return {
                "public_statement": _MAFIA_STATEMENTS[idx % len(_MAFIA_STATEMENTS)].format(
                    scapegoat=scapegoat
                ),
                "private_reasoning": _MAFIA_REASONING[idx % len(_MAFIA_REASONING)].format(
                    scapegoat=scapegoat, threat=threat
                ),
            }
        else:
            suspect = others[idx % len(others)]
            self._last_suspect = suspect
            return {
                "public_statement": _TOWN_STATEMENTS[idx % len(_TOWN_STATEMENTS)].format(
                    suspect=suspect
                ),
                "private_reasoning": _TOWN_REASONING[idx % len(_TOWN_REASONING)].format(
                    suspect=suspect
                ),
            }

    def _mock_vote(self, valid_targets: list[str]) -> dict[str, str]:
        if not valid_targets:
            valid_targets = ["Unknown"]

        if self._role == Role.MAFIA:
            # Mafia strategically targets someone other than who they accused
            # (to create confusion)
            target = valid_targets[self._call_count % len(valid_targets)]
            reasoning = f"I need to eliminate {target}. If I vote with the crowd it looks natural."
        else:
            # Town: 70% chance to vote for who they accused in discussion
            # This gives town realistic coordination
            if self._last_suspect and self._last_suspect in valid_targets and random.random() < 0.7:
                target = self._last_suspect
                reasoning = f"I accused {target} in discussion and I'm sticking with my read."
            else:
                target = valid_targets[self._call_count % len(valid_targets)]
                reasoning = f"Reconsidering — {target} seems most suspicious on reflection."

        return {
            "vote": target,
            "reasoning": reasoning,
        }

    def _parse_alive(self, prompt: str) -> list[str]:
        for line in prompt.split("\n"):
            if "Players alive:" in line or "Players still alive:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    return [n.strip() for n in parts[1].split(",") if n.strip()]
        return []
