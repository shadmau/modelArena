import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { CHARACTERS } from "../types/game";
import { Avatar } from "../components/Avatar";
import { DISPLAY_FONT, ensureFontsLoaded } from "../fonts";

interface EliminationSceneProps {
  playerName: string;
  role: "mafia" | "town";
  roundNumber: number;
}

export const EliminationScene: React.FC<EliminationSceneProps> = ({
  playerName,
  role,
  roundNumber,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const char = CHARACTERS[playerName] || {
    name: playerName,
    color: "#666",
    accentColor: "#999",
    emoji: "🤖",
  };

  ensureFontsLoaded();
  const isMafia = role === "mafia";

  // Dramatic reveal timing
  const avatarScale = spring({ frame, fps, config: { damping: 8 } });
  const roleRevealOpacity = interpolate(frame, [40, 55], [0, 1], { extrapolateRight: "clamp" });
  const resultOpacity = interpolate(frame, [60, 75], [0, 1], { extrapolateRight: "clamp" });

  // Flash effect on reveal
  const flashOpacity = interpolate(frame, [38, 42, 50], [0, 0.8, 0], {
    extrapolateRight: "clamp",
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0a0a0a 0%, #1a0a0a 100%)",
        fontFamily: DISPLAY_FONT,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Flash overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: isMafia ? "#DC2626" : "#fff",
          opacity: flashOpacity,
        }}
      />

      {/* "ELIMINATED" header */}
      <div
        style={{
          fontSize: 24,
          color: "#666",
          letterSpacing: 8,
          marginBottom: 40,
        }}
      >
        ELIMINATED
      </div>

      {/* Avatar */}
      <div style={{ transform: `scale(${avatarScale})` }}>
        <Avatar character={char} x={100} y={100} size={180} showRole={roleRevealOpacity > 0.5 ? role : null} />
      </div>

      {/* Result text */}
      <div
        style={{
          marginTop: 60,
          opacity: resultOpacity,
          fontSize: 36,
          fontWeight: 700,
          color: isMafia ? "#EF4444" : "#10B981",
          textShadow: `0 0 30px ${isMafia ? "#EF4444" : "#10B981"}44`,
        }}
      >
        {isMafia ? "THE MAFIA HAS BEEN FOUND!" : "AN INNOCENT FALLS..."}
      </div>

      <div
        style={{
          marginTop: 16,
          opacity: resultOpacity,
          fontSize: 20,
          color: "#999",
        }}
      >
        {isMafia ? "Town wins!" : "The Mafia is still among them..."}
      </div>
    </AbsoluteFill>
  );
};
