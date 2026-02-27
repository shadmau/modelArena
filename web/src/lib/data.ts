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
  icon?: string;
  color: string;
  title: string;
  model: string;
  winRate: number;
  wins: number;
  gamesPlayed: number;
  bestGame: string;
}

// Character display config
const CHARACTER_META: Record<string, { emoji: string; icon?: string; color: string; title: string; model: string }> = {
  Claude: { emoji: "🧠", icon: "/icons/claude.svg", color: "#d4956b", title: "THE DIPLOMAT", model: "Sonnet 4.6" },
  GPT: { emoji: "⚡", icon: "/icons/openai.svg", color: "#5fba97", title: "THE DECEIVER", model: "GPT-5.2" },
  Gemini: { emoji: "💎", icon: "/icons/gemini.svg", color: "#7aafdb", title: "THE DETECTIVE", model: "3.1 Pro" },
  DeepSeek: { emoji: "🔮", icon: "/icons/deepseek.svg", color: "#8b7ec8", title: "THE WILDCARD", model: "V3.2 Chat" },
  Llama: { emoji: "🦙", icon: "/icons/meta.svg", color: "#c07070", title: "THE SCAPEGOAT", model: "4 Maverick" },
  Grok: { emoji: "⚔", icon: "/icons/grok.svg", color: "#d4d4d4", title: "THE CHALLENGER", model: "4.1 Fast" },
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
    const meta = CHARACTER_META[name] || { emoji: "🤖", color: "#666", title: "UNKNOWN", model: "Unknown" };
    const wins = ps.wins || 0;
    // Derive a "best game" summary from stats
    let bestGame = "—";
    if (ps.mafia_win_rate > 80) bestGame = "Survived as Mafia";
    else if (ps.detection_rate > 60) bestGame = "Best detective";
    else if (wins > 0 && ps.town_win_rate > 70) bestGame = "Town MVP";
    else if (wins > 0) bestGame = `${wins}W streak`;
    return {
      name,
      emoji: meta.emoji,
      icon: meta.icon,
      color: meta.color,
      title: meta.title,
      model: meta.model,
      winRate: Math.round(ps.win_rate || 0),
      wins,
      gamesPlayed: ps.games_played || 0,
      bestGame,
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
    icon: meta.icon,
    color: meta.color,
    title: meta.title,
    model: meta.model,
    winRate: 0,
    wins: 0,
    gamesPlayed: 0,
    bestGame: "—",
  }));
}

export { CHARACTER_META };
