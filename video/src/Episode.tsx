import React from "react";
import { Sequence } from "remotion";
import { GameResult, EpisodeStats } from "./types/game";
import { TypingSpeed } from "./components/SpeechBubble";
import { IntroScene } from "./scenes/IntroScene";
import { TableScene, CameraMode } from "./scenes/TableScene";
import { ConfessionalScene } from "./scenes/ConfessionalScene";
import { VotingScene } from "./scenes/VotingScene";
import { EliminationScene } from "./scenes/EliminationScene";
import { StatsScene } from "./scenes/StatsScene";
import { OutroScene } from "./scenes/OutroScene";
import { RoundTitleScene } from "./scenes/RoundTitleScene";
import { GlitchTransition } from "./components/GlitchTransition";

interface EpisodeProps {
  game: GameResult;
  stats: EpisodeStats;
  episodeNumber: number;
}

// Timing constants (in frames at 30fps)
const INTRO_DURATION = 120; // 4s
const STATEMENT_DURATION = 150; // 5s per statement
const CONFESSIONAL_DURATION = 120; // 4s per confessional
const VOTING_DURATION = 150; // 5s (fits 6-player staggered reveals)
const ELIMINATION_DURATION = 120; // 4s
const STATS_DURATION = 180; // 6s
const OUTRO_DURATION = 150; // 5s
const ROUND_TITLE_DURATION = 45; // 1.5s title card
const GLITCH_DURATION = 3; // 0.1s glitch transition

/**
 * Determine which statements get a confessional cut.
 * Deterministic — uses player index + sub-round, NOT Math.random().
 * With 3 sub-rounds of discussion, we're selective to keep pacing tight:
 * - Sub-round 1: Mafia always, first speaker, alternating others
 * - Sub-round 2: Mafia only (middle round = fast back-and-forth)
 * - Sub-round 3: Mafia always, last speaker (final thoughts before vote)
 */
function shouldShowConfessional(
  playerName: string,
  mafiaPlayer: string,
  statementIndex: number,
  roundNumber: number,
  subRound: number = 1,
  totalInSubRound: number = 5,
): boolean {
  if (playerName === mafiaPlayer) return true;

  if (subRound === 1) {
    if (statementIndex === 0) return true;
    return (statementIndex + roundNumber) % 2 === 0;
  }

  if (subRound === 2) {
    return false; // Only mafia gets confessionals in the fast middle round
  }

  // Sub-round 3: last speaker gets a confessional (final thoughts)
  const isLastInSubRound = statementIndex === totalInSubRound - 1;
  return isLastInSubRound;
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

  // Track eliminations to show correct alive count in title cards
  const eliminatedSet = new Set<string>();
  let glitchSeed = 0;

  // For each round
  for (const round of game.rounds) {
    // Round title card
    const aliveCount = game.players.length - eliminatedSet.size;
    sequences.push(
      <Sequence
        key={`round-title-${round.round_number}`}
        from={currentFrame}
        durationInFrames={ROUND_TITLE_DURATION}
      >
        <RoundTitleScene
          roundNumber={round.round_number}
          aliveCount={aliveCount}
          totalPlayers={game.players.length}
        />
      </Sequence>
    );
    currentFrame += ROUND_TITLE_DURATION;

    // Group statements by sub-round for proper confessional logic
    const subRounds = new Map<number, typeof round.statements>();
    for (const stmt of round.statements) {
      const sr = stmt.sub_round ?? 1;
      if (!subRounds.has(sr)) subRounds.set(sr, []);
      subRounds.get(sr)!.push(stmt);
    }

    const sortedSubRounds = [...subRounds.entries()].sort((a, b) => a[0] - b[0]);

    for (const [subRound, statements] of sortedSubRounds) {
      for (let si = 0; si < statements.length; si++) {
        const statement = statements[si];
        const isMafia = statement.player === game.mafia_player;

        // Typing speed varies by sub-round
        let typingSpeed: TypingSpeed = "slow";
        if (subRound === 2) typingSpeed = "fast";
        if (subRound === 3) typingSpeed = si % 2 === 0 ? "fast" : "instant";

        // Camera mode varies by sub-round
        let cameraMode: CameraMode = "wide";
        if (subRound === 2) cameraMode = "closeup";
        if (subRound === 3) cameraMode = si % 2 === 0 ? "wide" : "closeup";

        // Focal player: next alive player after speaker (deterministic)
        const speakerIndex = game.players.findIndex((p) => p.name === statement.player);
        const alivePlayers = game.players
          .map((p, idx) => ({ ...p, idx }))
          .filter((p) => p.alive && p.idx !== speakerIndex);
        const focalPlayerIndex = alivePlayers.length > 0
          ? alivePlayers[(speakerIndex) % alivePlayers.length].idx
          : speakerIndex;

        // Public statement (table scene)
        sequences.push(
          <Sequence
            key={`table-r${round.round_number}-sr${subRound}-${statement.player}`}
            from={currentFrame}
            durationInFrames={STATEMENT_DURATION}
          >
            <TableScene
              statement={statement}
              players={game.players}
              roundNumber={round.round_number}
              typingSpeed={typingSpeed}
              cameraMode={cameraMode}
              focalPlayerIndex={focalPlayerIndex}
            />
          </Sequence>
        );
        currentFrame += STATEMENT_DURATION;

        // Confessional with glitch transitions (deterministic selection)
        if (shouldShowConfessional(statement.player, game.mafia_player, si, round.round_number, subRound, statements.length)) {
          // Glitch in
          sequences.push(
            <Sequence
              key={`glitch-in-r${round.round_number}-sr${subRound}-${statement.player}`}
              from={currentFrame}
              durationInFrames={GLITCH_DURATION}
            >
              <GlitchTransition seed={++glitchSeed} />
            </Sequence>
          );
          currentFrame += GLITCH_DURATION;

          sequences.push(
            <Sequence
              key={`confessional-r${round.round_number}-sr${subRound}-${statement.player}`}
              from={currentFrame}
              durationInFrames={CONFESSIONAL_DURATION}
            >
              <ConfessionalScene statement={statement} isMafia={isMafia} />
            </Sequence>
          );
          currentFrame += CONFESSIONAL_DURATION;

          // Glitch out
          sequences.push(
            <Sequence
              key={`glitch-out-r${round.round_number}-sr${subRound}-${statement.player}`}
              from={currentFrame}
              durationInFrames={GLITCH_DURATION}
            >
              <GlitchTransition seed={++glitchSeed} />
            </Sequence>
          );
          currentFrame += GLITCH_DURATION;
        }
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

    if (round.eliminated) {
      eliminatedSet.add(round.eliminated);
    }
  }

  // Stats
  sequences.push(
    <Sequence key="stats" from={currentFrame} durationInFrames={STATS_DURATION}>
      <StatsScene stats={stats} />
    </Sequence>
  );
  currentFrame += STATS_DURATION;

  // Outro
  sequences.push(
    <Sequence key="outro" from={currentFrame} durationInFrames={OUTRO_DURATION}>
      <OutroScene
        winner={game.winner}
        mafiaPlayer={game.mafia_player}
        episodeNumber={episodeNumber}
      />
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
    frames += ROUND_TITLE_DURATION;

    // Group by sub-round to match Episode rendering
    const subRounds = new Map<number, typeof round.statements>();
    for (const stmt of round.statements) {
      const sr = stmt.sub_round ?? 1;
      if (!subRounds.has(sr)) subRounds.set(sr, []);
      subRounds.get(sr)!.push(stmt);
    }

    for (const [subRound, statements] of [...subRounds.entries()].sort((a, b) => a[0] - b[0])) {
      for (let si = 0; si < statements.length; si++) {
        frames += STATEMENT_DURATION;
        if (shouldShowConfessional(statements[si].player, game.mafia_player, si, round.round_number, subRound, statements.length)) {
          frames += GLITCH_DURATION + CONFESSIONAL_DURATION + GLITCH_DURATION;
        }
      }
    }

    if (round.votes.length > 0) frames += VOTING_DURATION;
    if (round.eliminated) frames += ELIMINATION_DURATION;
  }

  frames += STATS_DURATION;
  frames += OUTRO_DURATION;
  return frames;
}
