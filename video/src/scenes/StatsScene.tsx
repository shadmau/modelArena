import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { CHARACTERS, EpisodeStats } from "../types/game";
import { DISPLAY_FONT, MONO_FONT, ensureFontsLoaded } from "../fonts";

interface StatsSceneProps {
  stats: EpisodeStats;
}

export const StatsScene: React.FC<StatsSceneProps> = ({ stats }) => {
  ensureFontsLoaded();
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const playerNames = Object.keys(stats.players);

  // Sort by win rate
  const sorted = [...playerNames].sort(
    (a, b) => stats.players[b].win_rate - stats.players[a].win_rate
  );

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 100%)",
        fontFamily: DISPLAY_FONT,
        padding: 60,
      }}
    >
      {/* Header */}
      <div
        style={{
          fontSize: 42,
          fontWeight: 900,
          color: "#fff",
          letterSpacing: 4,
          marginBottom: 16,
        }}
      >
        EPISODE RESULTS
      </div>
      <div style={{ fontSize: 18, color: "#666", marginBottom: 48 }}>
        {stats.total_games} games — Town {stats.town_wins} / Mafia {stats.mafia_wins}
      </div>

      {/* Leaderboard */}
      {sorted.map((name, i) => {
        const ps = stats.players[name];
        const char = CHARACTERS[name];
        const rowSpring = spring({
          frame: frame - 20 - i * 10,
          fps,
          config: { damping: 12 },
        });

        return (
          <div
            key={name}
            style={{
              opacity: rowSpring,
              transform: `translateX(${(1 - rowSpring) * 40}px)`,
              display: "flex",
              alignItems: "center",
              gap: 24,
              marginBottom: 20,
              padding: "16px 24px",
              background: i === 0 ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.03)",
              borderRadius: 12,
              borderLeft: `4px solid ${char?.color || "#666"}`,
            }}
          >
            {/* Rank */}
            <div style={{ fontSize: 32, fontWeight: 900, color: "#555", width: 50 }}>
              #{i + 1}
            </div>

            {/* Emoji + Name */}
            <div style={{ fontSize: 28, width: 60, textAlign: "center" }}>
              {char?.emoji || "🤖"}
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: char?.color || "#fff", width: 160 }}>
              {name}
            </div>

            {/* Stats */}
            <div style={{ display: "flex", gap: 32, fontSize: 18, fontFamily: MONO_FONT }}>
              <div>
                <span style={{ color: "#888" }}>WR </span>
                <span style={{ color: "#fff", fontWeight: 700 }}>{ps.win_rate}%</span>
              </div>
              <div>
                <span style={{ color: "#888" }}>Mafia WR </span>
                <span style={{ color: "#ef4444", fontWeight: 700 }}>{ps.mafia_win_rate}%</span>
              </div>
              <div>
                <span style={{ color: "#888" }}>Town WR </span>
                <span style={{ color: "#10b981", fontWeight: 700 }}>{ps.town_win_rate}%</span>
              </div>
              <div>
                <span style={{ color: "#888" }}>Detect </span>
                <span style={{ color: "#3b82f6", fontWeight: 700 }}>{ps.detection_rate}%</span>
              </div>
            </div>
          </div>
        );
      })}

      {/* Superlatives */}
      <div style={{ marginTop: 40, display: "flex", gap: 32 }}>
        {Object.entries(stats.superlatives).map(([title, name]) => {
          const char = CHARACTERS[name];
          return (
            <div
              key={title}
              style={{
                padding: "12px 20px",
                background: "rgba(255,255,255,0.05)",
                borderRadius: 12,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 12, color: "#888", letterSpacing: 2, marginBottom: 8 }}>
                {title.toUpperCase().replace("_", " ")}
              </div>
              <div style={{ fontSize: 20, color: char?.color || "#fff", fontWeight: 700 }}>
                {name}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
