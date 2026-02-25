import React from "react";
import { Sequence, useVideoConfig } from "remotion";
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
    // Discussion: show each statement + confessional for interesting ones
    for (const statement of round.statements) {
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

      // Confessional (show for mafia player always, others occasionally)
      const isMafia = statement.player === game.mafia_player;
      const showConfessional = isMafia || Math.random() < 0.4;

      if (showConfessional) {
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
 */
export function calculateDuration(game: GameResult): number {
  let frames = INTRO_DURATION;

  for (const round of game.rounds) {
    frames += round.statements.length * STATEMENT_DURATION;
    // Estimate confessionals (~60% of statements get one)
    frames += Math.ceil(round.statements.length * 0.6) * CONFESSIONAL_DURATION;
    if (round.votes.length > 0) frames += VOTING_DURATION;
    if (round.eliminated) frames += ELIMINATION_DURATION;
  }

  frames += STATS_DURATION;
  return frames;
}
