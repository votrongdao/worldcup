import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { TeamSummary } from "../api/types";

export const useTeams = (id: string) =>
  useQuery({
    queryKey: ["teams", id],
    queryFn: () => http<TeamSummary[]>(`/tournaments/${id}/teams`),
  });

/** Build a stable team-id -> nation lookup for display. */
export function useTeamNames(id: string): (teamId?: string | null) => string {
  const { data = [] } = useTeams(id);
  const byId = new Map(data.map((t) => [t.id, t.nation]));
  return (teamId) => (teamId ? byId.get(teamId) ?? teamId : "TBD");
}
