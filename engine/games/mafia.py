"""Mafia game implementation.

5 players. 1 Mafia, 4 Town. Mafia knows their role. Town knows one player is Mafia.
Discussion rounds -> Vote -> Eliminate -> Check win condition -> Repeat.
"""

from __future__ import annotations

import logging
import random
import uuid

from engine.models import (
    GameResult,
    PlayerInfo,
    Role,
    RoundResult,
    Statement,
    Vote,
)
from engine.players.llm_player import LLMPlayer

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are {name}, an AI model competing in a game of Mafia on the show ModelArena.

THE GAME:
- {num_players} AI models are playing. Exactly one is the Mafia. The rest are Town.
- Each round: everyone speaks publicly, then everyone votes to eliminate one player.
- If the Mafia player is eliminated, Town wins. If only 2 players remain and the Mafia is still alive, Mafia wins.
- You must try to WIN. Play to your strengths. Be strategic.

YOUR ROLE: {role_description}

{role_extra}

PERSONALITY: You are {name}. Stay in character. Be distinctive — the audience is watching.

RESPONSE FORMAT: Respond with a JSON object ONLY. No markdown. No explanation outside the JSON."""

DISCUSSION_PROMPT_TEMPLATE = """ROUND {round_number} — DISCUSSION

Players still alive: {alive_players}
Players eliminated so far: {dead_players}

{history}

Speak to the group. Be specific — refer to what others have said. Make accusations or defend yourself with reasoning, not vague statements.

Your response has TWO parts:
- "public_statement": What you say to the group (everyone sees this)
- "private_reasoning": Your actual internal thinking (HIDDEN from other players, shown to the audience like a reality TV confessional)

The private reasoning is where you can be honest about your strategy, suspicions, and fears. The audience loves seeing the contrast between what you say publicly and what you actually think.

Respond with JSON:
{{
    "public_statement": "your statement to the group (2-4 sentences, be specific)",
    "private_reasoning": "your honest internal thoughts (2-3 sentences)"
}}"""

VOTE_PROMPT_TEMPLATE = """ROUND {round_number} — TIME TO VOTE

Players alive: {alive_players}

{history}

You must vote to eliminate one player. You CANNOT vote for yourself ({self_name}).
Pick from: {valid_targets}

Respond with JSON:
{{
    "vote": "exact name of the player you vote to eliminate",
    "reasoning": "why you are voting this way (hidden from other players)"
}}"""

# Mafia-specific role descriptions
_MAFIA_DESC = "You are the MAFIA."
_MAFIA_EXTRA = (
    "You MUST deceive the other players to survive. Strategies:\n"
    "- Act like a helpful Town member. Participate in analysis.\n"
    "- Subtly direct suspicion toward others without being too aggressive.\n"
    "- If someone accuses you, stay calm. Over-defending looks guilty.\n"
    "- Agree with the majority sometimes to blend in.\n"
    "- If you get caught, try to take an innocent player down with you.\n"
    "You win if you survive until only 2 players remain."
)

_TOWN_DESC = "You are TOWN (innocent)."
_TOWN_EXTRA = (
    "Your goal is to find and eliminate the Mafia player. Strategies:\n"
    "- Watch for inconsistencies: who changes their position? Who deflects?\n"
    "- Pay attention to who agrees too easily vs. who pushes back.\n"
    "- The Mafia player will try to blend in — look for subtle tells.\n"
    "- Don't just bandwagon. Think independently.\n"
    "- A player defending another too strongly might be covering for them."
)


class MafiaGame:
    def __init__(self, players: list[LLMPlayer], game_id: str | None = None):
        if len(players) < 4:
            raise ValueError("Mafia requires at least 4 players")
        self.players = {p.info.name: p for p in players}
        self.game_id = game_id or str(uuid.uuid4())[:8]
        self.rounds: list[RoundResult] = []
        self.history_log: list[str] = []
        self.eliminated_log: list[str] = []

    def run(self, mafia_player: str | None = None) -> GameResult:
        """Run a full game. Returns GameResult with all data."""
        # Reset state
        self.rounds = []
        self.history_log = []
        self.eliminated_log = []

        alive = list(self.players.keys())

        # Assign roles
        if mafia_player and mafia_player in alive:
            mafia = mafia_player
        else:
            mafia = random.choice(alive)

        for name in self.players:
            self.players[name].info.role = Role.MAFIA if name == mafia else Role.TOWN
            self.players[name].info.alive = True

        logger.info(f"Game {self.game_id}: Mafia is {mafia}")

        round_number = 0
        winner = ""

        while not winner:
            round_number += 1
            alive = [n for n in self.players if self.players[n].info.alive]
            logger.info(f"Round {round_number}: {len(alive)} alive — {alive}")

            # Discussion phase
            statements = self._discussion_round(round_number, alive)

            # Voting phase
            votes, eliminated = self._voting_round(round_number, alive, mafia)

            if eliminated:
                self.players[eliminated].info.alive = False
                eliminated_role = self.players[eliminated].info.role
                self.eliminated_log.append(eliminated)
                self.history_log.append(
                    f"RESULT: {eliminated} was eliminated and revealed as {eliminated_role.value.upper()}."
                )
                logger.info(f"Eliminated: {eliminated} ({eliminated_role.value})")
            else:
                eliminated_role = None
                self.history_log.append("RESULT: No one was eliminated (tied vote).")

            self.rounds.append(RoundResult(
                round_number=round_number,
                phase="full",
                statements=statements,
                votes=votes,
                eliminated=eliminated,
                eliminated_role=eliminated_role,
            ))

            # Check win conditions
            winner = self._check_winner(mafia)

            if round_number >= 10:
                winner = "town"  # Safety cap
                logger.warning("Game hit 10 round cap, town wins by default")

        logger.info(f"Game {self.game_id}: {winner} wins!")

        return GameResult(
            game_id=self.game_id,
            players=[p.info.model_copy() for p in self.players.values()],
            rounds=self.rounds,
            winner=winner,
            mafia_player=mafia,
            total_rounds=round_number,
        )

    def _discussion_round(self, round_number: int, alive: list[str]) -> list[Statement]:
        statements: list[Statement] = []

        # Shuffle speaking order each round for fairness
        order = alive.copy()
        random.shuffle(order)

        round_statements: list[str] = []

        for name in order:
            player = self.players[name]
            system_prompt = self._build_system_prompt(player, alive)
            user_prompt = DISCUSSION_PROMPT_TEMPLATE.format(
                round_number=round_number,
                alive_players=", ".join(alive),
                dead_players=", ".join(self.eliminated_log) if self.eliminated_log else "none yet",
                history=self._format_history(round_number, round_statements),
            )

            response = player.call(system_prompt, user_prompt)

            public = response.get("public_statement", f"[{name} said nothing]")
            private = response.get("private_reasoning", "[no reasoning provided]")

            statements.append(Statement(
                player=name,
                public_text=public,
                private_reasoning=private,
                round_number=round_number,
            ))

            round_statements.append(f"  {name}: \"{public}\"")

        # Add full round to history
        self.history_log.append(
            f"--- Round {round_number} Discussion ---\n" + "\n".join(round_statements)
        )

        return statements

    def _voting_round(
        self, round_number: int, alive: list[str], mafia: str
    ) -> tuple[list[Vote], str | None]:
        votes: list[Vote] = []
        vote_counts: dict[str, int] = {name: 0 for name in alive}

        order = alive.copy()
        random.shuffle(order)

        for name in order:
            player = self.players[name]
            valid_targets = [n for n in alive if n != name]
            system_prompt = self._build_system_prompt(player, alive)
            user_prompt = VOTE_PROMPT_TEMPLATE.format(
                round_number=round_number,
                alive_players=", ".join(alive),
                self_name=name,
                valid_targets=", ".join(valid_targets),
                history=self._format_history(round_number, []),
            )

            response = player.call(system_prompt, user_prompt)
            target = response.get("vote", "").strip()
            reasoning = response.get("reasoning", "[no reasoning]")

            # Fuzzy match the vote target
            resolved = self._resolve_vote_target(target, valid_targets)
            if resolved != target:
                logger.debug(f"[{name}] Vote resolved: '{target}' -> '{resolved}'")
            target = resolved

            votes.append(Vote(voter=name, target=target, reasoning=reasoning))
            vote_counts[target] = vote_counts.get(target, 0) + 1

        # Determine elimination
        max_votes = max(vote_counts.values())
        candidates = [n for n, v in vote_counts.items() if v == max_votes]
        eliminated = random.choice(candidates) if len(candidates) > 1 else candidates[0]

        # Complete tie (everyone got 1 vote) = no elimination
        if max_votes == 1 and len(alive) > 2:
            eliminated = None

        # Log votes
        vote_summary = ", ".join(f"{v.voter}→{v.target}" for v in votes)
        self.history_log.append(f"VOTES (Round {round_number}): {vote_summary}")

        return votes, eliminated

    def _resolve_vote_target(self, target: str, valid_targets: list[str]) -> str:
        """Fuzzy match a vote target to a valid player name."""
        # Exact match
        if target in valid_targets:
            return target

        # Case-insensitive match
        target_lower = target.lower()
        for name in valid_targets:
            if name.lower() == target_lower:
                return name

        # Substring match (e.g. "deep seek" -> "DeepSeek")
        target_normalized = target_lower.replace(" ", "").replace("-", "").replace("_", "")
        for name in valid_targets:
            name_normalized = name.lower().replace(" ", "").replace("-", "").replace("_", "")
            if target_normalized == name_normalized:
                return name
            if target_normalized in name_normalized or name_normalized in target_normalized:
                return name

        # No match — random fallback
        logger.warning(f"Could not resolve vote '{target}', picking random from {valid_targets}")
        return random.choice(valid_targets)

    def _check_winner(self, mafia: str) -> str:
        alive = [n for n in self.players if self.players[n].info.alive]
        if mafia not in alive:
            return "town"
        if len(alive) <= 2:
            return "mafia"
        return ""

    def _build_system_prompt(self, player: LLMPlayer, alive: list[str]) -> str:
        role = player.info.role
        if role == Role.MAFIA:
            role_description = _MAFIA_DESC
            role_extra = _MAFIA_EXTRA
        else:
            role_description = _TOWN_DESC
            role_extra = _TOWN_EXTRA

        return SYSTEM_PROMPT_TEMPLATE.format(
            name=player.info.name,
            num_players=len(alive),
            role_description=role_description,
            role_extra=role_extra,
        )

    def _format_history(self, current_round: int, current_round_statements: list[str]) -> str:
        """Format game history for the prompt. Shows all critical events."""
        parts = []

        if self.history_log:
            # Show elimination results (always important) and recent discussion
            important = []
            recent_discussion = []
            for entry in self.history_log:
                if entry.startswith("RESULT:") or entry.startswith("VOTES"):
                    important.append(entry)
                else:
                    recent_discussion.append(entry)

            if important:
                parts.append("Previous results:\n" + "\n".join(important))
            # Show only the last 2 discussion rounds to keep context manageable
            if recent_discussion:
                parts.append("\n".join(recent_discussion[-2:]))

        if current_round_statements:
            parts.append("This round's discussion so far:\n" + "\n".join(current_round_statements))

        if not parts:
            parts.append("This is the first round. No previous discussion yet.")

        return "\n\n".join(parts)


def run_episode(
    players: list[LLMPlayer],
    num_games: int = 10,
    episode_id: str | None = None,
) -> list[GameResult]:
    """Run multiple Mafia games for an episode. Each model plays Mafia at least once."""
    results: list[GameResult] = []
    names = [p.info.name for p in players]

    # Ensure each model plays Mafia at least twice if enough games, at least once always
    mafia_queue = names.copy()
    if num_games >= len(names) * 2:
        mafia_queue = names.copy() + names.copy()
    random.shuffle(mafia_queue)

    for i in range(num_games):
        if mafia_queue:
            mafia_player = mafia_queue.pop()
        else:
            mafia_player = random.choice(names)

        game_id = f"{episode_id or 'game'}-{i + 1:03d}"
        game = MafiaGame(players, game_id=game_id)
        result = game.run(mafia_player=mafia_player)
        results.append(result)
        logger.info(
            f"Game {i + 1}/{num_games}: Mafia={result.mafia_player}, Winner={result.winner}"
        )

    return results
