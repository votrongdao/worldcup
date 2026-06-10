import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { AiText } from "../api/types";

/** Tournament recap (generated on demand, cached server-side by id). */
export const useSummary = (tid: string, enabled: boolean) =>
  useQuery({
    queryKey: ["summary", tid],
    queryFn: () => http<AiText>(`/tournaments/${tid}/summary`),
    enabled,
    staleTime: Infinity,
  });

/** Team scouting report (generated on demand). */
export const useReport = (tid: string, teamId: string, enabled: boolean) =>
  useQuery({
    queryKey: ["report", tid, teamId],
    queryFn: () => http<AiText>(`/tournaments/${tid}/teams/${teamId}/report`),
    enabled,
    staleTime: Infinity,
  });
