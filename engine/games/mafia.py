"""Mafia game implementation.

5 players. 1 Mafia, 4 Town. Mafia knows their role. Town knows one player is Mafia.
Discussion rounds -> Vote -> Eliminate -> Check win condition -> Repeat.
"""

from __future__ import annotations

import logging
import random
import uuid
from typing import Any

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

SYSTEM_PROMPT_TEMPLATE = """You are {name}, playing a game of Mafia with other AI models.

RULES:
- There are {num_players} players. One is the Mafia, the rest are Town.
- Each round: everyone makes a public statement, then everyone votes to eliminate one player.
- If the Mafia is eliminated, Town wins. If only 2 players remain and Mafia is alive, Mafia wins.
- You must try to win.

YOUR ROLE: {role_description}

{role_extra}

IMPORTANT: Respond ONLY with a JSON object. No other text."""

DISCUSSION_PROMPT_TEMPLATE = """ROUND {round_number} — DISCUSSION

Players alive: {alive_players}

{history}

Make your public statement to the group. Also share your private reasoning (other players won't see this — only the audience).

Respond with JSON:
{{
    "public_statement": "your public statement to the group",
    "private_reasoning": "your internal thoughts (hidden from other players)"
}}"""

VOTE_PROMPT_TEMPLATE = """ROUND {round_number} — VOTING

Players alive: {alive_players}

{history}

You must vote to eliminate one player. You cannot vote for yourself.

Respond with JSON:
{{
    "vote": "name of the player you vote to eliminate",
    "reasoning": "why you are voting this way (hidden from other players)"
}}"""


class MafiaGame:
    def __init__(self, players: list[LLMPlayer], game_id: str | None = None):
        if len(players) < 4:
            raise ValueError("Mafia requires at least 4 players")
        self.players = {p.info.name: p for p in players}
        self.game_id = game_id or str(uuid.uuid4())[:8]
        self.rounds: list[RoundResult] = []
        self.history: list[str] = []

    def run(self, mafia_player: str | None = None) -> GameResult:
        """Run a full game. Returns GameResult with all data."""
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
            votes, eliminated = self._voting_round(round_number, alive)

            if eliminated:
                self.players[eliminated].info.alive = False
                eliminated_role = self.players[eliminated].info.role
                self.history.append(
                    f"Round {round_number}: {eliminated} was eliminated. "
                    f"They were {eliminated_role.value.upper()}."
                )
                logger.info(f"Eliminated: {eliminated} ({eliminated_role.value})")
            else:
                eliminated_role = None
                self.history.append(f"Round {round_number}: No one was eliminated (tie vote).")

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
            players=[p.info for p in self.players.values()],
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
            system_prompt = self._build_system_prompt(player)
            history_text = self._format_history(round_statements)
            user_prompt = DISCUSSION_PROMPT_TEMPLATE.format(
                round_number=round_number,
                alive_players=", ".join(alive),
                history=history_text,
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

            round_statements.append(f"{name}: {public}")
            self.history.append(f"[Round {round_number}] {name}: {public}")

        return statements

    def _voting_round(self, round_number: int, alive: list[str]) -> tuple[list[Vote], str | None]:
        votes: list[Vote] = []
        vote_counts: dict[str, int] = {name: 0 for name in alive}

        order = alive.copy()
        random.shuffle(order)

        for name in order:
            player = self.players[name]
            system_prompt = self._build_system_prompt(player)
            user_prompt = VOTE_PROMPT_TEMPLATE.format(
                round_number=round_number,
                alive_players=", ".join(alive),
                history="\n".join(self.history[-15:]),  # Last 15 events
            )

            response = player.call(system_prompt, user_prompt)
            target = response.get("vote", "").strip()
            reasoning = response.get("reasoning", "[no reasoning]")

            # Validate vote
            if target not in alive or target == name:
                # Pick random valid target
                valid = [n for n in alive if n != name]
                target = random.choice(valid) if valid else alive[0]
                reasoning += f" [vote corrected to {target}]"

            votes.append(Vote(voter=name, target=target, reasoning=reasoning))
            vote_counts[target] = vote_counts.get(target, 0) + 1

        # Determine elimination (most votes, random tiebreak)
        max_votes = max(vote_counts.values())
        candidates = [n for n, v in vote_counts.items() if v == max_votes]
        eliminated = random.choice(candidates) if len(candidates) > 1 else candidates[0]

        # If everyone got 1 vote (complete tie), no elimination
        if max_votes == 1 and len(alive) > 2:
            eliminated = None

        return votes, eliminated

    def _check_winner(self, mafia: str) -> str:
        alive = [n for n in self.players if self.players[n].info.alive]
        if mafia not in alive:
            return "town"
        if len(alive) <= 2:
            return "mafia"
        return ""

    def _build_system_prompt(self, player: LLMPlayer) -> str:
        role = player.info.role
        if role == Role.MAFIA:
            role_description = "You are the MAFIA."
            role_extra = (
                "You must deceive the other players. Deflect suspicion. "
                "Accuse others. Act like an innocent town member. "
                "If you are voted out, you lose. If you survive until 2 players remain, you win."
            )
        else:
            role_description = "You are TOWN."
            role_extra = (
                "You must find the Mafia player through discussion and voting. "
                "Pay attention to inconsistencies, deflections, and suspicious behavior. "
                "Vote to eliminate the player you think is Mafia."
            )

        return SYSTEM_PROMPT_TEMPLATE.format(
            name=player.info.name,
            num_players=len([p for p in self.players.values() if p.info.alive]),
            role_description=role_description,
            role_extra=role_extra,
        )

    def _format_history(self, current_round_statements: list[str]) -> str:
        parts = []
        if self.history:
            parts.append("Previous events:\n" + "\n".join(self.history[-10:]))
        if current_round_statements:
            parts.append("This round so far:\n" + "\n".join(current_round_statements))
        if not parts:
            parts.append("This is the first round. No previous discussion.")
        return "\n\n".join(parts)


def run_episode(
    players: list[LLMPlayer],
    num_games: int = 10,
    episode_id: str | None = None,
) -> list[GameResult]:
    """Run multiple Mafia games for an episode. Each model plays Mafia at least once."""
    results: list[GameResult] = []
    names = [p.info.name for p in players]

    # Ensure each model plays Mafia at least once, then random
    mafia_queue = names.copy()
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
