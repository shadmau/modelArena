import React from "react";
import { interpolate, useCurrentFrame, spring, useVideoConfig } from "remotion";
import { MONO_FONT } from "../fonts";

export type TypingSpeed = "slow" | "fast" | "instant";

interface SpeechBubbleProps {
  text: string;
  x: number;
  y: number;
  color: string;
  maxWidth?: number;
  typingSpeed?: TypingSpeed;
}

const TYPING_FRAMES: Record<TypingSpeed, number> = {
  slow: 90,
  fast: 30,
  instant: 1,
};

export const SpeechBubble: React.FC<SpeechBubbleProps> = ({
  text,
  x,
  y,
  color,
  maxWidth = 400,
  typingSpeed = "slow",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const scale = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });

  const duration = TYPING_FRAMES[typingSpeed];
  const charsToShow =
    typingSpeed === "instant"
      ? text.length
      : Math.floor(
          interpolate(frame, [0, duration], [0, text.length], {
            extrapolateRight: "clamp",
          })
        );
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
          fontFamily: MONO_FONT,
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
