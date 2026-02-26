/**
 * Load episode data from results/ JSON files at build time.
 * Astro runs this at build, so it reads from the filesystem.
 */

import fs from "node:fs";
import path from "node:path";

const RESULTS_DIR = path.resolve(import.meta.dirname, "../../../results");

interface EpisodeMeta {
  id: string;
  title: string;
  game_type: string;
  timestamp: string;
  totalGames: number;
  townWins: number;
  mafiaWins: number;
}

interface PlayerStandings {
  name: string;
  emoji: string;
  color: string;
  title: string;
  winRate: number;
  mafiaWR: number;
  townWR: number;
  detection: number;
  record: string;
  gamesPlayed: number;
}

// Character display config
const CHARACTER_META: Record<string, { emoji: string; color: string; title: string }> = {
  Claude: { emoji: "🧠", color: "#c8a960", title: "THE DIPLOMAT" },
  GPT: { emoji: "⚡", color: "#6db880", title: "THE DECEIVER" },
  Gemini: { emoji: "💎", color: "#6a9ec0", title: "THE DETECTIVE" },
  DeepSeek: { emoji: "🔮", color: "#9a80c0", title: "THE WILDCARD" },
  Llama: { emoji: "🦙", color: "#c07070", title: "THE SCAPEGOAT" },
};

/**
 * List all episode directories in results/
 */
export function listEpisodes(): EpisodeMeta[] {
  if (!fs.existsSync(RESULTS_DIR)) return [];

  const dirs = fs.readdirSync(RESULTS_DIR, { withFileTypes: true })
    .filter(d => d.isDirectory() && d.name.startsWith("ep"))
    .sort((a, b) => a.name.localeCompare(b.name));

  return dirs.map(d => {
    const epFile = path.join(RESULTS_DIR, d.name, "episode.json");
    if (!fs.existsSync(epFile)) return null;

    const ep = JSON.parse(fs.readFileSync(epFile, "utf-8"));
    return {
      id: d.name,
      title: ep.episode_title || `Episode ${d.name}`,
      game_type: ep.game_type || "mafia",
      timestamp: ep.timestamp,
      totalGames: ep.stats?.total_games || ep.games?.length || 0,
      townWins: ep.stats?.town_wins || 0,
      mafiaWins: ep.stats?.mafia_wins || 0,
    };
  }).filter(Boolean) as EpisodeMeta[];
}

/**
 * Load full episode data (episode.json)
 */
export function loadEpisode(episodeId: string): any | null {
  const epFile = path.join(RESULTS_DIR, episodeId, "episode.json");
  if (!fs.existsSync(epFile)) return null;
  return JSON.parse(fs.readFileSync(epFile, "utf-8"));
}

/**
 * Load stats for an episode
 */
export function loadStats(episodeId: string): any | null {
  const statsFile = path.join(RESULTS_DIR, episodeId, "stats.json");
  if (!fs.existsSync(statsFile)) return null;
  return JSON.parse(fs.readFileSync(statsFile, "utf-8"));
}

/**
 * Load a specific game file
 */
export function loadGame(episodeId: string, gameId: string): any | null {
  const gameFile = path.join(RESULTS_DIR, episodeId, `${gameId}.json`);
  if (!fs.existsSync(gameFile)) return null;
  return JSON.parse(fs.readFileSync(gameFile, "utf-8"));
}

/**
 * List all game files in an episode
 */
export function listGames(episodeId: string): string[] {
  const dir = path.join(RESULTS_DIR, episodeId);
  if (!fs.existsSync(dir)) return [];

  return fs.readdirSync(dir)
    .filter(f => f.startsWith(episodeId + "-") && f.endsWith(".json"))
    .map(f => f.replace(".json", ""))
    .sort();
}

/**
 * Get latest stats and build player standings for leaderboard.
 * Uses the most recent episode's stats.
 */
export function getPlayerStandings(): PlayerStandings[] {
  const episodes = listEpisodes();
  if (episodes.length === 0) return getDefaultStandings();

  const latest = episodes[episodes.length - 1];
  const stats = loadStats(latest.id);
  if (!stats?.players) return getDefaultStandings();

  return Object.entries(stats.players).map(([name, ps]: [string, any]) => {
    const meta = CHARACTER_META[name] || { emoji: "🤖", color: "#666", title: "UNKNOWN" };
    const wins = ps.wins || 0;
    const losses = (ps.games_played || 0) - wins;
    return {
      name,
      emoji: meta.emoji,
      color: meta.color,
      title: meta.title,
      winRate: Math.round(ps.win_rate || 0),
      mafiaWR: Math.round(ps.mafia_win_rate || 0),
      townWR: Math.round(ps.town_win_rate || 0),
      detection: Math.round(ps.detection_rate || 0),
      record: `${wins}-${losses}`,
      gamesPlayed: ps.games_played || 0,
    };
  }).sort((a, b) => b.winRate - a.winRate);
}

/**
 * Fallback standings when no results exist yet
 */
function getDefaultStandings(): PlayerStandings[] {
  return Object.entries(CHARACTER_META).map(([name, meta]) => ({
    name,
    emoji: meta.emoji,
    color: meta.color,
    title: meta.title,
    winRate: 0,
    mafiaWR: 0,
    townWR: 0,
    detection: 0,
    record: "0-0",
    gamesPlayed: 0,
  }));
}

export { CHARACTER_META };
