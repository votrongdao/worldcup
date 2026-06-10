import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { Standing } from "../api/types";

// Backend returns { "A": [...], "B": [...] } — one ordered table per group.
export const useStandings = (id: string) =>
  useQuery({
    queryKey: ["standings", id],
    queryFn: () => http<Record<string, Standing[]>>(`/tournaments/${id}/standings`),
  });
