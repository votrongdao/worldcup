// API types mirroring the backend Pydantic contracts (camelCase on the wire).
export type Phase =
  | "setup" | "generating" | "draw" | "group"
  | "r16" | "qf" | "sf" | "final" | "done";

export interface TournamentConfig {
  format: string; teams: number; groups: number; perGroup: number;
  advancePerGroup: number; thirdPlace: boolean; seed: number;
  autoPlay?: boolean;   // false = self-play (you conduct each match)
}
export interface TournamentStatus {
  id: string; phase: Phase; runHash: string;
  championId?: string | null; teams: number; groups: number;
}
export interface Standing {
  teamId: string; group: string; played: number; w: number; d: number;
  l: number; gf: number; ga: number; pts: number;
}
export interface TeamSummary {
  id: string; nation: string; tier: number; rating: number;
  styleDna: string; group: string;
}
export interface BracketSlot {
  matchId: string; phase: Phase;
  homeId?: string | null; awayId?: string | null; winnerId?: string | null;
}
export interface MatchSummary {
  matchId: string; homeId: string; awayId: string; phase: Phase;
  scoreHome: number; scoreAway: number; decidedBy: string; winnerId?: string | null;
}
export interface Fixture {
  id: string; phase: Phase; homeId: string; awayId: string;
  group: string | null; matchday: number;
  scoreHome: number | null; scoreAway: number | null;
  winnerId: string | null; played: boolean;
}
export interface MatchEvent { t: number; type: string; team?: "home" | "away"; }
export interface Frame { t: number; players: [number, number][]; ball: [number, number]; }

export interface PlayerDetail {
  id: string; role: "GK" | "DEF" | "MID" | "FWD";
  pace: number; accel: number; shooting: number; passing: number;
  dribbling: number; vision: number; defending: number; stamina: number; teamwork: number;
}
export interface CoachDetail {
  formation: string; aggression: number; lineHeight: number;
  tempo: number; pressing: number; directness: number;
}
export interface TeamDetail {
  id: string; nation: string; tier: number; rating: number; styleDna: string;
  group: string; xi: string[]; squad: PlayerDetail[]; coach: CoachDetail;
  colors: Record<string, string>;
}
export interface AiText { text: string; cached: boolean; }

// --- AI coach & player performance (per match) ---
export interface PlayerRating {
  player_id: string; side: "home" | "away"; role: string; shirt: number;
  rating: number; minutes: number; goals: number; assists: number; shots: number;
  passes: number; pass_pct: number; tackles: number; saves: number; fouls: number;
  distance_km: number; stamina_end: number;
  sub_on: number | null; sub_off: number | null;
  strengths: string[]; weaknesses: string[];
}
export interface CoachDecision {
  t: number; side: "home" | "away";
  kind: "formation" | "substitution" | "tactic";
  summary: string; reason: string;
}
export interface TeamReport {
  side: "home" | "away"; formation_end: string; style_end: string;
  strengths: string[]; weaknesses: string[];
  key_player: string | null; key_player_rating: number;
}
export interface MatchReport {
  matchId: string; ratings: PlayerRating[];
  reports: TeamReport[]; decisions: CoachDecision[];
}
