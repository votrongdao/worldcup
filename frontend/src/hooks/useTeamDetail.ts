import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { TeamDetail } from "../api/types";

export const useTeamDetail = (tid: string, teamId: string) =>
  useQuery({
    queryKey: ["team-detail", tid, teamId],
    queryFn: () => http<TeamDetail>(`/tournaments/${tid}/teams/${teamId}`),
  });
