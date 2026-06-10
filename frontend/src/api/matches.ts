import { http } from "./client";
import type { MatchEvent } from "./types";

export const getMatch = (id: string) => http<unknown>(`/matches/${id}`);
export const getEvents = (id: string) => http<MatchEvent[]>(`/matches/${id}/events`);
