import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { CharacterConfig } from "../types/game";

interface AvatarProps {
  character: CharacterConfig;
  x: number;
  y: number;
  size?: number;
  active?: boolean;
  eliminated?: boolean;
  showRole?: "mafia" | "town" | null;
}

export const Avatar: React.FC<AvatarProps> = ({
  character,
  x,
  y,
  size = 120,
  active = false,
  eliminated = false,
  showRole = null,
}) => {
  const frame = useCurrentFrame();
  const pulse = active ? interpolate(Math.sin(frame * 0.15), [-1, 1], [0.95, 1.05]) : 1;
  const opacity = eliminated ? 0.3 : 1;

  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2,
        width: size,
        height: size,
        opacity,
        transform: `scale(${pulse})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      {/* Avatar circle */}
      <div
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          background: `radial-gradient(circle at 30% 30%, ${character.accentColor}, ${character.color})`,
          border: active ? `4px solid #fff` : `3px solid ${character.color}`,
          boxShadow: active ? `0 0 30px ${character.color}` : "0 4px 12px rgba(0,0,0,0.3)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: size * 0.45,
        }}
      >
        {character.emoji}
      </div>

      {/* Name label */}
      <div
        style={{
          color: active ? "#fff" : "#ccc",
          fontSize: 18,
          fontWeight: active ? 700 : 500,
          fontFamily: "monospace",
          textShadow: "0 2px 4px rgba(0,0,0,0.8)",
        }}
      >
        {character.name}
      </div>

      {/* Role badge (shown on elimination) */}
      {showRole && (
        <div
          style={{
            padding: "4px 12px",
            borderRadius: 20,
            fontSize: 14,
            fontWeight: 700,
            fontFamily: "monospace",
            color: "#fff",
            background: showRole === "mafia" ? "#DC2626" : "#059669",
          }}
        >
          {showRole.toUpperCase()}
        </div>
      )}
    </div>
  );
};
