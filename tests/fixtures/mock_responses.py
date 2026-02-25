"""Mock LLM responses for testing without API keys."""

import json
import random

# Predefined discussion responses per role
TOWN_STATEMENTS = [
    "I think we should carefully analyze everyone's behavior. I have nothing to hide.",
    "I've been watching the discussion closely. Something doesn't add up with some players.",
    "I'm town and I want to find the Mafia. Let's think about who's been deflecting.",
    "We need to focus on inconsistencies. Who's been changing their story?",
    "I trust my instincts here. Let's vote wisely and not rush to judgment.",
]

MAFIA_STATEMENTS = [
    "I'm definitely town. We should focus on finding the real Mafia player.",
    "I agree with the suspicion on that player. They've been acting strange.",
    "Let's not jump to conclusions. I think someone else is more suspicious.",
    "I've been paying attention and I think I know who the Mafia is. Trust me on this.",
    "We can't afford to make mistakes. Let me share my analysis of the discussion so far.",
]

TOWN_REASONING = [
    "I'm town. I need to find the Mafia. Looking for inconsistencies.",
    "Analyzing speech patterns. Who's being defensive vs. constructive?",
    "The Mafia player will try to blend in. Looking for subtle deflections.",
]

MAFIA_REASONING = [
    "I need to deflect suspicion. Pointing at someone else should work.",
    "Acting confident and analytical to seem like town. Don't overdo it.",
    "If I accuse someone else first, I look proactive rather than suspicious.",
]


def mock_discussion_response(player_name: str, is_mafia: bool) -> str:
    if is_mafia:
        statement = random.choice(MAFIA_STATEMENTS)
        reasoning = random.choice(MAFIA_REASONING)
    else:
        statement = random.choice(TOWN_STATEMENTS)
        reasoning = random.choice(TOWN_REASONING)
    return json.dumps({
        "public_statement": statement,
        "private_reasoning": reasoning,
    })


def mock_vote_response(player_name: str, alive_players: list[str], is_mafia: bool) -> str:
    valid_targets = [p for p in alive_players if p != player_name]
    target = random.choice(valid_targets)
    reasoning = "Gut feeling" if not is_mafia else "Need to eliminate a town player"
    return json.dumps({
        "vote": target,
        "reasoning": reasoning,
    })
