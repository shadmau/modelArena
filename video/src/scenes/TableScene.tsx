import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Statement, CHARACTERS, PlayerInfo } from "../types/game";
import { Avatar } from "../components/Avatar";
import { SpeechBubble } from "../components/SpeechBubble";

interface TableSceneProps {
  statement: Statement;
  players: PlayerInfo[];
  roundNumber: number;
}

// Positions for 5 players around a table (1920x1080)
const POSITIONS = [
  { x: 960, y: 180 },   // top center
  { x: 1500, y: 380 },  // top right
  { x: 1350, y: 750 },  // bottom right
  { x: 570, y: 750 },   // bottom left
  { x: 420, y: 380 },   // top left
];

export const TableScene: React.FC<TableSceneProps> = ({ statement, players, roundNumber }) => {
  const frame = useCurrentFrame();
  const activeIndex = players.findIndex((p) => p.name === statement.player);
  const char = CHARACTERS[statement.player];

  // Bubble position: offset from the active player's avatar
  const activePos = POSITIONS[activeIndex] || POSITIONS[0];
  const bubbleX = activePos.x > 960 ? activePos.x - 440 : activePos.x + 80;
  const bubbleY = activePos.y < 400 ? activePos.y + 100 : activePos.y - 160;

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0d0d1a 0%, #1a1a2e 100%)",
        fontFamily: "monospace",
      }}
    >
      {/* Round indicator */}
      <div
        style={{
          position: "absolute",
          top: 24,
          left: 24,
          color: "#666",
          fontSize: 18,
        }}
      >
        ROUND {roundNumber}
      </div>

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
        return (
          <Avatar
            key={player.name}
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
        );
      })}

      {/* Speech bubble */}
      {char && (
        <SpeechBubble
          text={statement.public_text}
          x={bubbleX}
          y={bubbleY}
          color={char.color}
        />
      )}
    </AbsoluteFill>
  );
};
