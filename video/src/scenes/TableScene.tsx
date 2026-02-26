import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { Statement, CHARACTERS, PlayerInfo } from "../types/game";
import { Avatar } from "../components/Avatar";
import { SpeechBubble, TypingSpeed } from "../components/SpeechBubble";
import { DISPLAY_FONT, MONO_FONT, ensureFontsLoaded } from "../fonts";

export type CameraMode = "wide" | "closeup";

interface TableSceneProps {
  statement: Statement;
  players: PlayerInfo[];
  roundNumber: number;
  typingSpeed?: TypingSpeed;
  cameraMode?: CameraMode;
  focalPlayerIndex?: number;
}

// Positions for 6 players around a table (1920x1080) — hexagon layout
const POSITIONS = [
  { x: 960, y: 150 },   // top center
  { x: 1440, y: 330 },  // upper right
  { x: 1440, y: 690 },  // lower right
  { x: 960, y: 870 },   // bottom center
  { x: 480, y: 690 },   // lower left
  { x: 480, y: 330 },   // upper left
];

const CLOSEUP_SCALE = 1.8;

export const TableScene: React.FC<TableSceneProps> = ({
  statement,
  players,
  roundNumber,
  typingSpeed = "slow",
  cameraMode = "wide",
  focalPlayerIndex,
}) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const activeIndex = players.findIndex((p) => p.name === statement.player);
  const char = CHARACTERS[statement.player];

  // Bubble position: offset from the active player's avatar
  const activePos = POSITIONS[activeIndex] || POSITIONS[0];
  const bubbleX = activePos.x > 960 ? activePos.x - 440 : activePos.x + 80;
  const bubbleY = activePos.y < 400 ? activePos.y + 100 : activePos.y - 160;

  // Camera zoom animation
  const isCloseup = cameraMode === "closeup";
  const zoomSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 80 },
    durationInFrames: 15,
  });
  const zoom = isCloseup ? interpolate(zoomSpring, [0, 1], [1, CLOSEUP_SCALE]) : 1;

  // Closeup: center on midpoint between speaker and focal player
  let translateX = 0;
  let translateY = 0;
  if (isCloseup && focalPlayerIndex !== undefined) {
    const focalPos = POSITIONS[focalPlayerIndex] || POSITIONS[0];
    const centerX = (activePos.x + focalPos.x) / 2;
    const centerY = (activePos.y + focalPos.y) / 2;
    // Translate so the midpoint is at screen center (960, 540)
    translateX = (960 - centerX) * (zoom - 1);
    translateY = (540 - centerY) * (zoom - 1);
  }

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0d0d1a 0%, #1a1a2e 100%)",
        fontFamily: DISPLAY_FONT,
      }}
    >
      {/* Round indicator (outside zoom) */}
      <div
        style={{
          position: "absolute",
          top: 24,
          left: 24,
          color: "#666",
          fontSize: 18,
          zIndex: 10,
        }}
      >
        ROUND {roundNumber}
      </div>

      {/* Zoomable container for table + players */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `scale(${zoom}) translate(${translateX / zoom}px, ${translateY / zoom}px)`,
          transformOrigin: "center center",
        }}
      >
        {/* Table (subtle circle) */}
        <div
          style={{
            position: "absolute",
            left: 960 - 300,
            top: 480 - 200,
            width: 600,
            height: 400,
            borderRadius: "50%",
            border: "1px solid rgba(255,255,255,0.05)",
            background: "rgba(255,255,255,0.02)",
          }}
        />

        {/* Players */}
        {players.map((player, i) => {
          const pos = POSITIONS[i];
          const isActive = player.name === statement.player;
          // In closeup mode, dim non-speaker, non-focal players
          const isDimmed =
            isCloseup && !isActive && i !== focalPlayerIndex;
          const dimOpacity = isDimmed
            ? interpolate(zoomSpring, [0, 1], [1, 0.15])
            : 1;

          return (
            <div key={player.name} style={{ opacity: dimOpacity }}>
              <Avatar
                character={
                  CHARACTERS[player.name] || {
                    name: player.name,
                    color: "#666",
                    accentColor: "#999",
                    emoji: "🤖",
                  }
                }
                x={pos.x}
                y={pos.y}
                active={isActive}
                eliminated={!player.alive}
              />
            </div>
          );
        })}
      </div>

      {/* Speech bubble (outside zoom to stay readable) */}
      {char && (
        <SpeechBubble
          text={statement.public_text}
          x={bubbleX}
          y={bubbleY}
          color={char.color}
          typingSpeed={typingSpeed}
        />
      )}
    </AbsoluteFill>
  );
};
