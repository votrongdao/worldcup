import { http } from "./client";
import type { TournamentConfig, TournamentStatus } from "./types";

export const createTournament = (config: TournamentConfig) =>
  http<{ id: string }>("/tournaments", { method: "POST", body: JSON.stringify({ config }) });

export const getStatus = (id: string) =>
  http<TournamentStatus>(`/tournaments/${id}`);

/** Self-play: play every unplayed fixture in the current round in parallel. */
export const playRound = (id: string) =>
  http<{ played: number; phase: string }>(`/tournaments/${id}/play-round`, { method: "POST" });

/** Self-play: play the rest of the tournament to the end (runs server-side, poll to watch). */
export const playAll = (id: string) =>
  http<{ status: string; phase: string }>(`/tournaments/${id}/play-all`, { method: "POST" });

export const pause = (id: string) =>
  http<void>(`/tournaments/${id}/pause`, { method: "POST" });

export const resume = (id: string) =>
  http<void>(`/tournaments/${id}/resume`, { method: "POST" });
