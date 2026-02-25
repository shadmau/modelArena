import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { CHARACTERS } from "../types/game";

interface OutroSceneProps {
  winner: "mafia" | "town";
  mafiaPlayer: string;
  episodeNumber: number;
}

export const OutroScene: React.FC<OutroSceneProps> = ({ winner, mafiaPlayer, episodeNumber }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fadeIn = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const textSpring = spring({ frame: frame - 10, fps, config: { damping: 14 } });
  const ctaSpring = spring({ frame: frame - 60, fps, config: { damping: 12 } });

  const mafiaChar = CHARACTERS[mafiaPlayer];
  const winColor = winner === "mafia" ? "#ef4444" : "#10b981";

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "monospace",
      }}
    >
      {/* Winner banner */}
      <div
        style={{
          opacity: fadeIn,
          transform: `scale(${textSpring})`,
          fontSize: 52,
          fontWeight: 900,
          color: winColor,
          letterSpacing: 6,
          textShadow: `0 0 40px ${winColor}66`,
          marginBottom: 24,
        }}
      >
        {winner === "town" ? "TOWN WINS" : "MAFIA WINS"}
      </div>

      {/* Mafia reveal */}
      <div
        style={{
          opacity: textSpring,
          fontSize: 24,
          color: "#888",
          marginBottom: 80,
        }}
      >
        The Mafia was{" "}
        <span style={{ color: mafiaChar?.color || "#fff", fontWeight: 700 }}>
          {mafiaPlayer}
        </span>{" "}
        {mafiaChar?.emoji || "🤖"}
      </div>

      {/* Next episode teaser */}
      <div
        style={{
          opacity: ctaSpring,
          transform: `translateY(${(1 - ctaSpring) * 30}px)`,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: 18,
            color: "#a78bfa",
            letterSpacing: 4,
            marginBottom: 16,
          }}
        >
          NEXT WEEK ON MODEL ARENA
        </div>
        <div style={{ fontSize: 28, color: "#fff", fontWeight: 700 }}>
          Episode {episodeNumber + 1}
        </div>
      </div>

      {/* Branding */}
      <div
        style={{
          position: "absolute",
          bottom: 60,
          opacity: interpolate(frame, [80, 100], [0, 0.6], { extrapolateRight: "clamp" }),
          fontSize: 16,
          color: "#555",
          letterSpacing: 3,
        }}
      >
        MODELARENA.GG
      </div>
    </AbsoluteFill>
  );
};
