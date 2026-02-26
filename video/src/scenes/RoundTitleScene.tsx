import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { DISPLAY_FONT, ensureFontsLoaded } from "../fonts";

interface RoundTitleSceneProps {
  roundNumber: number;
  aliveCount: number;
  totalPlayers: number;
}

export const RoundTitleScene: React.FC<RoundTitleSceneProps> = ({
  roundNumber,
  aliveCount,
  totalPlayers,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleSpring = spring({ frame: frame - 5, fps, config: { damping: 14 } });
  const subtitleSpring = spring({ frame: frame - 12, fps, config: { damping: 14 } });
  const lineSpring = spring({ frame: frame - 8, fps, config: { damping: 12, stiffness: 80 } });

  // Fade out in final 8 frames (total duration = 45 frames)
  const fadeOut = interpolate(frame, [37, 45], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0a0a1a 0%, #12081e 50%, #0a0a1a 100%)",
        fontFamily: DISPLAY_FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity: fadeOut,
      }}
    >
      {/* Round number */}
      <div
        style={{
          fontSize: 80,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 12,
          transform: `scale(${titleSpring})`,
          opacity: titleSpring,
          textShadow: "0 0 40px rgba(139, 92, 246, 0.4)",
        }}
      >
        ROUND {roundNumber}
      </div>

      {/* Animated accent line */}
      <div
        style={{
          width: interpolate(lineSpring, [0, 1], [0, 200]),
          height: 3,
          background: "linear-gradient(90deg, transparent, #a78bfa, transparent)",
          marginTop: 20,
          marginBottom: 20,
        }}
      />

      {/* Player count subtitle */}
      <div
        style={{
          fontSize: 24,
          color: "#888",
          letterSpacing: 4,
          transform: `translateY(${(1 - subtitleSpring) * 15}px)`,
          opacity: subtitleSpring,
        }}
      >
        {aliveCount} OF {totalPlayers} PLAYERS REMAIN
      </div>
    </AbsoluteFill>
  );
};
