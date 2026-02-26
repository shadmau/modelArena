import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { GameResult, CHARACTERS } from "../types/game";
import { Avatar } from "../components/Avatar";
import { DISPLAY_FONT, ensureFontsLoaded } from "../fonts";

interface IntroSceneProps {
  game: GameResult;
  episodeNumber: number;
}

export const IntroScene: React.FC<IntroSceneProps> = ({ game, episodeNumber }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleOpacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const subtitleOpacity = interpolate(frame, [20, 40], [0, 1], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: DISPLAY_FONT,
      }}
    >
      {/* Title */}
      <div
        style={{
          opacity: titleOpacity,
          fontSize: 72,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 8,
          textShadow: "0 0 40px rgba(139, 92, 246, 0.5)",
        }}
      >
        MODEL ARENA
      </div>

      {/* Episode subtitle */}
      <div
        style={{
          opacity: subtitleOpacity,
          fontSize: 32,
          color: "#a78bfa",
          marginTop: 16,
          letterSpacing: 4,
        }}
      >
        EPISODE {episodeNumber} — MAFIA
      </div>

      {/* Player lineup */}
      <div
        style={{
          display: "flex",
          gap: 60,
          marginTop: 80,
        }}
      >
        {game.players.map((player, i) => {
          const playerSpring = spring({
            frame: frame - 40 - i * 8,
            fps,
            config: { damping: 12 },
          });
          const char = CHARACTERS[player.name] || {
            name: player.name,
            color: "#666",
            accentColor: "#999",
            emoji: "🤖",
          };
          return (
            <div
              key={player.name}
              style={{
                transform: `translateY(${(1 - playerSpring) * 50}px)`,
                opacity: playerSpring,
              }}
            >
              <Avatar character={char} x={60} y={60} size={100} />
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
