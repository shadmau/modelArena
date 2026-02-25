import React from "react";
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";

interface SpeechBubbleProps {
  text: string;
  x: number;
  y: number;
  color: string;
  maxWidth?: number;
}

export const SpeechBubble: React.FC<SpeechBubbleProps> = ({
  text,
  x,
  y,
  color,
  maxWidth = 400,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });

  // Typewriter effect
  const charsToShow = Math.floor(interpolate(frame, [0, 60], [0, text.length], {
    extrapolateRight: "clamp",
  }));
  const displayText = text.slice(0, charsToShow);

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `scale(${scale})`,
        transformOrigin: "top left",
        maxWidth,
      }}
    >
      <div
        style={{
          background: "rgba(20, 20, 30, 0.9)",
          border: `2px solid ${color}`,
          borderRadius: 16,
          padding: "16px 20px",
          color: "#fff",
          fontSize: 20,
          lineHeight: 1.5,
          fontFamily: "monospace",
          boxShadow: `0 0 20px ${color}33`,
        }}
      >
        {displayText}
        {charsToShow < text.length && (
          <span style={{ opacity: frame % 20 < 10 ? 1 : 0 }}>▊</span>
        )}
      </div>
    </div>
  );
};
