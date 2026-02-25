import React from "react";
import { Composition } from "remotion";
import { Episode, calculateDuration } from "./Episode";
import { GameResult, EpisodeStats } from "./types/game";

// Sample data for development/preview — replace with actual game JSON
import sampleGame from "./sample-data/game.json";
import sampleStats from "./sample-data/stats.json";

const game = sampleGame as unknown as GameResult;
const stats = sampleStats as unknown as EpisodeStats;

export const RemotionRoot: React.FC = () => {
  const duration = calculateDuration(game);

  return (
    <>
      <Composition
        id="Episode"
        component={Episode as React.FC}
        durationInFrames={duration}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          game,
          stats,
          episodeNumber: 1,
        }}
      />
    </>
  );
};
