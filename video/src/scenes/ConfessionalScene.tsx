import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Statement, CHARACTERS } from "../types/game";
import { Avatar } from "../components/Avatar";
import { DISPLAY_FONT, MONO_FONT, ensureFontsLoaded } from "../fonts";

interface ConfessionalSceneProps {
  statement: Statement;
  isMafia: boolean;
}

export const ConfessionalScene: React.FC<ConfessionalSceneProps> = ({ statement, isMafia }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const char = CHARACTERS[statement.player] || {
    name: statement.player,
    color: "#666",
    accentColor: "#999",
    emoji: "🤖",
  };

  const textOpacity = interpolate(frame, [10, 30], [0, 1], { extrapolateRight: "clamp" });
  const charsToShow = Math.floor(
    interpolate(frame, [15, 90], [0, statement.private_reasoning.length], {
      extrapolateRight: "clamp",
    })
  );
  const displayText = statement.private_reasoning.slice(0, charsToShow);

  // Subtle vignette pulse for mafia confessionals
  const vignetteIntensity = isMafia
    ? interpolate(Math.sin(frame * 0.08), [-1, 1], [0.6, 0.8])
    : 0.4;

  return (
    <AbsoluteFill
      style={{
        background: isMafia
          ? "linear-gradient(135deg, #1a0505 0%, #2d0a0a 50%, #1a0a0a 100%)"
          : "linear-gradient(135deg, #05051a 0%, #0a0a2d 50%, #0a0a1a 100%)",
        fontFamily: DISPLAY_FONT,
      }}
    >
      {/* Vignette overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,${vignetteIntensity}) 100%)`,
        }}
      />

      {/* "CONFESSIONAL" label */}
      <div
        style={{
          position: "absolute",
          top: 32,
          right: 40,
          color: isMafia ? "#ef4444" : "#6366f1",
          fontSize: 14,
          letterSpacing: 6,
          opacity: 0.6,
        }}
      >
        {isMafia ? "☠ CONFESSIONAL" : "CONFESSIONAL"}
      </div>

      {/* Large avatar on the left */}
      <div style={{ position: "absolute", left: 120, top: 300 }}>
        <Avatar character={char} x={100} y={100} size={200} active />
      </div>

      {/* Reasoning text on the right */}
      <div
        style={{
          position: "absolute",
          right: 80,
          top: 180,
          width: 700,
          opacity: textOpacity,
        }}
      >
        {/* Player name */}
        <div
          style={{
            color: char.color,
            fontSize: 28,
            fontWeight: 700,
            fontFamily: DISPLAY_FONT,
            marginBottom: 24,
          }}
        >
          {char.name}'s thoughts
        </div>

        {/* Reasoning text */}
        <div
          style={{
            color: isMafia ? "#fca5a5" : "#c7d2fe",
            fontSize: 24,
            lineHeight: 1.7,
            fontStyle: "italic",
            fontFamily: MONO_FONT,
          }}
        >
          "{displayText}"
          {charsToShow < statement.private_reasoning.length && (
            <span style={{ opacity: frame % 20 < 10 ? 1 : 0 }}>▊</span>
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
