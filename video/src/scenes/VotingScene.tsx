import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Vote, PlayerInfo, CHARACTERS } from "../types/game";
import { Avatar } from "../components/Avatar";
import { DISPLAY_FONT, MONO_FONT, ensureFontsLoaded } from "../fonts";

interface VotingSceneProps {
  votes: Vote[];
  players: PlayerInfo[];
  roundNumber: number;
}

const VOTE_STAGGER = 15;

export const VotingScene: React.FC<VotingSceneProps> = ({ votes, players, roundNumber }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const alivePlayerNames = players.filter((p) => p.alive).map((p) => p.name);
  const alivePositions = alivePlayerNames.map((_, i) => {
    const spacing = 1520 / (alivePlayerNames.length + 1);
    return { x: 200 + spacing * (i + 1), y: 280 };
  });

  // Progressive vote counts — only count votes that have visually appeared
  const progressiveCounts: Record<string, number> = {};
  votes.forEach((v, i) => {
    const voteAppear = spring({
      frame: frame - i * VOTE_STAGGER,
      fps,
      config: { damping: 12 },
    });
    if (voteAppear > 0.5) {
      progressiveCounts[v.target] = (progressiveCounts[v.target] || 0) + 1;
    }
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0a0a1a 0%, #1a1025 100%)",
        fontFamily: DISPLAY_FONT,
      }}
    >
      {/* Header */}
      <div
        style={{
          position: "absolute",
          top: 40,
          width: "100%",
          textAlign: "center",
          color: "#fff",
          fontSize: 36,
          fontWeight: 700,
          letterSpacing: 4,
        }}
      >
        ROUND {roundNumber} — VOTE
      </div>

      {/* Players */}
      {alivePlayerNames.map((name, i) => {
        const pos = alivePositions[i];
        const char = CHARACTERS[name] || {
          name,
          color: "#666",
          accentColor: "#999",
          emoji: "🤖",
        };
        const count = progressiveCounts[name] || 0;

        return (
          <React.Fragment key={name}>
            <Avatar character={char} x={pos.x} y={pos.y} size={100} />
            {count > 0 && (
              <div
                style={{
                  position: "absolute",
                  left: pos.x - 20,
                  top: pos.y + 80,
                  width: 40,
                  height: 40,
                  borderRadius: "50%",
                  background: count >= 2 ? "#DC2626" : "#666",
                  color: "#fff",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 20,
                  fontWeight: 700,
                  fontFamily: MONO_FONT,
                }}
              >
                {count}
              </div>
            )}
          </React.Fragment>
        );
      })}

      {/* Vote arrows / list */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          left: 0,
          width: "100%",
          display: "flex",
          justifyContent: "center",
          gap: 40,
        }}
      >
        {votes.map((vote, i) => {
          const appear = spring({
            frame: frame - i * VOTE_STAGGER,
            fps,
            config: { damping: 12 },
          });
          const voterChar = CHARACTERS[vote.voter];
          const targetChar = CHARACTERS[vote.target];
          return (
            <div
              key={i}
              style={{
                opacity: appear,
                transform: `translateY(${(1 - appear) * 20}px)`,
                display: "flex",
                alignItems: "center",
                gap: 8,
                background: "rgba(255,255,255,0.05)",
                padding: "8px 16px",
                borderRadius: 12,
              }}
            >
              <span style={{ color: voterChar?.color || "#fff", fontSize: 16 }}>
                {vote.voter}
              </span>
              <span style={{ color: "#666", fontSize: 14 }}>→</span>
              <span style={{ color: targetChar?.color || "#fff", fontSize: 16, fontWeight: 700 }}>
                {vote.target}
              </span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
