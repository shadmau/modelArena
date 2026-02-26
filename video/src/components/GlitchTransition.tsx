import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

interface GlitchTransitionProps {
  seed: number;
}

// Simple deterministic pseudo-random from seed
function seededRandom(seed: number): () => number {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

export const GlitchTransition: React.FC<GlitchTransitionProps> = ({ seed }) => {
  const frame = useCurrentFrame();
  const rand = seededRandom(seed + frame);

  // 3 horizontal slices with displacement
  const slices = Array.from({ length: 5 }, () => ({
    top: rand() * 100,
    height: 5 + rand() * 20,
    offsetX: (rand() - 0.5) * 60,
  }));

  // Color channel separation offset
  const redOffsetX = (rand() - 0.5) * 12;
  const blueOffsetX = (rand() - 0.5) * 12;

  // Scanline intensity varies per frame
  const scanlineOpacity = 0.15 + rand() * 0.2;

  return (
    <AbsoluteFill style={{ background: "#000" }}>
      {/* Color channel separation layers */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `linear-gradient(90deg, rgba(255,0,0,0.15) 0%, transparent 30%, transparent 70%, rgba(0,0,255,0.15) 100%)`,
          transform: `translateX(${redOffsetX}px)`,
          mixBlendMode: "screen",
        }}
      />

      {/* Horizontal slice displacement */}
      {slices.map((slice, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            top: `${slice.top}%`,
            height: `${slice.height}%`,
            background: `linear-gradient(90deg,
              rgba(255,0,0,0.3) 0%,
              rgba(255,255,255,0.08) 20%,
              rgba(0,255,255,0.2) 80%,
              rgba(0,0,255,0.3) 100%)`,
            transform: `translateX(${slice.offsetX}px)`,
          }}
        />
      ))}

      {/* Channel separation bars */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255,0,0,0.06) 2px,
            rgba(255,0,0,0.06) 4px
          )`,
          transform: `translateX(${blueOffsetX}px)`,
        }}
      />

      {/* Scanline overlay */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 1px,
            rgba(0,0,0,${scanlineOpacity}) 1px,
            rgba(0,0,0,${scanlineOpacity}) 2px
          )`,
        }}
      />

      {/* Bright flash band */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: `${30 + rand() * 40}%`,
          height: 2,
          background: "rgba(255,255,255,0.6)",
        }}
      />
    </AbsoluteFill>
  );
};
