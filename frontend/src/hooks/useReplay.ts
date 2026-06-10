import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { Frame } from "../api/types";

export interface ReplayData {
  matchId: string;
  homeId: string;
  awayId: string;
  homeNation: string;
  awayNation: string;
  scoreHome: number;
  scoreAway: number;
  decidedBy: string;
  duration: number;
  frames: Frame[];
}

export const useReplay = (tid: string, mid: string) =>
  useQuery({
    queryKey: ["replay", tid, mid],
    queryFn: () => http<ReplayData>(`/tournaments/${tid}/matches/${mid}/replay`),
    staleTime: Infinity,
  });
