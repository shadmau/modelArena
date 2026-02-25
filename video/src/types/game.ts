// Types matching the Python engine's JSON output

export interface PlayerInfo {
  name: string;
  model: string;
  role: "mafia" | "town" | null;
  alive: boolean;
  avatar_color: string;
}

export interface Statement {
  player: string;
  public_text: string;
  private_reasoning: string;
  round_number: number;
}

export interface Vote {
  voter: string;
  target: string;
  reasoning: string;
}

export interface RoundResult {
  round_number: number;
  phase: string;
  statements: Statement[];
  votes: Vote[];
  eliminated: string | null;
  eliminated_role: "mafia" | "town" | null;
}

export interface GameResult {
  game_id: string;
  game_type: string;
  timestamp: string;
  players: PlayerInfo[];
  rounds: RoundResult[];
  winner: "mafia" | "town";
  mafia_player: string;
  total_rounds: number;
}

export interface EpisodeStats {
  total_games: number;
  town_wins: number;
  mafia_wins: number;
  players: Record<string, PlayerStats>;
  superlatives: Record<string, string>;
}

export interface PlayerStats {
  games_played: number;
  wins: number;
  win_rate: number;
  times_mafia: number;
  times_town: number;
  mafia_win_rate: number;
  town_win_rate: number;
  detection_rate: number;
  times_eliminated: number;
  times_first_eliminated: number;
  votes_received: number;
}

// Character visual config
export interface CharacterConfig {
  name: string;
  color: string;
  accentColor: string;
  emoji: string;
}

export const CHARACTERS: Record<string, CharacterConfig> = {
  Claude: { name: "Claude", color: "#D97706", accentColor: "#FCD34D", emoji: "🧠" },
  GPT: { name: "GPT", color: "#10B981", accentColor: "#6EE7B7", emoji: "⚡" },
  Gemini: { name: "Gemini", color: "#3B82F6", accentColor: "#93C5FD", emoji: "💎" },
  DeepSeek: { name: "DeepSeek", color: "#8B5CF6", accentColor: "#C4B5FD", emoji: "🔮" },
  Llama: { name: "Llama", color: "#EF4444", accentColor: "#FCA5A5", emoji: "🦙" },
};
