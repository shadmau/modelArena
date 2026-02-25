import React from "react";
import { Sequence } from "remotion";
import { GameResult, EpisodeStats } from "./types/game";
import { IntroScene } from "./scenes/IntroScene";
import { TableScene } from "./scenes/TableScene";
import { ConfessionalScene } from "./scenes/ConfessionalScene";
import { VotingScene } from "./scenes/VotingScene";
import { EliminationScene } from "./scenes/EliminationScene";
import { StatsScene } from "./scenes/StatsScene";

interface EpisodeProps {
  game: GameResult;
  stats: EpisodeStats;
  episodeNumber: number;
}

// Timing constants (in frames at 30fps)
const INTRO_DURATION = 120; // 4s
const STATEMENT_DURATION = 150; // 5s per statement
const CONFESSIONAL_DURATION = 120; // 4s per confessional
const VOTING_DURATION = 120; // 4s
const ELIMINATION_DURATION = 120; // 4s
const STATS_DURATION = 180; // 6s

/**
 * Determine which statements get a confessional cut.
 * Deterministic — uses player index + round number, NOT Math.random().
 * Rules:
 * - Mafia player ALWAYS gets a confessional (the audience needs to see them scheme)
 * - First speaker of each round gets one (sets the tone)
 * - Every other non-mafia player gets one (keeps pacing)
 */
function shouldShowConfessional(
  playerName: string,
  mafiaPlayer: string,
  statementIndex: number,
  roundNumber: number,
): boolean {
  if (playerName === mafiaPlayer) return true;
  if (statementIndex === 0) return true;
  // Alternate: show for odd indices in odd rounds, even indices in even rounds
  return (statementIndex + roundNumber) % 2 === 0;
}

export const Episode: React.FC<EpisodeProps> = ({ game, stats, episodeNumber }) => {
  let currentFrame = 0;
  const sequences: React.ReactNode[] = [];

  // Intro
  sequences.push(
    <Sequence key="intro" from={currentFrame} durationInFrames={INTRO_DURATION}>
      <IntroScene game={game} episodeNumber={episodeNumber} />
    </Sequence>
  );
  currentFrame += INTRO_DURATION;

  // For each round
  for (const round of game.rounds) {
    // Discussion: each statement + confessional for selected players
    for (let si = 0; si < round.statements.length; si++) {
      const statement = round.statements[si];
      const isMafia = statement.player === game.mafia_player;

      // Public statement (table scene)
      sequences.push(
        <Sequence
          key={`table-r${round.round_number}-${statement.player}`}
          from={currentFrame}
          durationInFrames={STATEMENT_DURATION}
        >
          <TableScene
            statement={statement}
            players={game.players}
            roundNumber={round.round_number}
          />
        </Sequence>
      );
      currentFrame += STATEMENT_DURATION;

      // Confessional (deterministic selection)
      if (shouldShowConfessional(statement.player, game.mafia_player, si, round.round_number)) {
        sequences.push(
          <Sequence
            key={`confessional-r${round.round_number}-${statement.player}`}
            from={currentFrame}
            durationInFrames={CONFESSIONAL_DURATION}
          >
            <ConfessionalScene statement={statement} isMafia={isMafia} />
          </Sequence>
        );
        currentFrame += CONFESSIONAL_DURATION;
      }
    }

    // Voting
    if (round.votes.length > 0) {
      sequences.push(
        <Sequence
          key={`voting-r${round.round_number}`}
          from={currentFrame}
          durationInFrames={VOTING_DURATION}
        >
          <VotingScene
            votes={round.votes}
            players={game.players}
            roundNumber={round.round_number}
          />
        </Sequence>
      );
      currentFrame += VOTING_DURATION;
    }

    // Elimination
    if (round.eliminated && round.eliminated_role) {
      sequences.push(
        <Sequence
          key={`elimination-r${round.round_number}`}
          from={currentFrame}
          durationInFrames={ELIMINATION_DURATION}
        >
          <EliminationScene
            playerName={round.eliminated}
            role={round.eliminated_role}
            roundNumber={round.round_number}
          />
        </Sequence>
      );
      currentFrame += ELIMINATION_DURATION;
    }
  }

  // Stats
  sequences.push(
    <Sequence key="stats" from={currentFrame} durationInFrames={STATS_DURATION}>
      <StatsScene stats={stats} />
    </Sequence>
  );

  return <>{sequences}</>;
};

/**
 * Calculate total duration for a game in frames.
 * Must match the logic in Episode component exactly.
 */
export function calculateDuration(game: GameResult): number {
  let frames = INTRO_DURATION;

  for (const round of game.rounds) {
    for (let si = 0; si < round.statements.length; si++) {
      frames += STATEMENT_DURATION;
      if (shouldShowConfessional(round.statements[si].player, game.mafia_player, si, round.round_number)) {
        frames += CONFESSIONAL_DURATION;
      }
    }
    if (round.votes.length > 0) frames += VOTING_DURATION;
    if (round.eliminated) frames += ELIMINATION_DURATION;
  }

  frames += STATS_DURATION;
  return frames;
}
