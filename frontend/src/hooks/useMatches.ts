import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { MatchSummary } from "../api/types";

export const useMatches = (id: string) =>
  useQuery({
    queryKey: ["matches", id],
    queryFn: () => http<MatchSummary[]>(`/tournaments/${id}/matches`),
  });

/** AI commentary for one match — fetched on demand (enabled flag). */
export const useCommentary = (matchId: string, enabled: boolean) =>
  useQuery({
    queryKey: ["commentary", matchId],
    queryFn: () =>
      http<{ matchId: string; scoreHome: number; scoreAway: number; commentary: string }>(
        `/matches/${matchId}/commentary`,
      ),
    enabled,
    staleTime: Infinity,
  });
