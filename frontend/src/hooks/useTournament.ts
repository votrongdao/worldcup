import { useQuery } from "@tanstack/react-query";
import { getStatus } from "../api/tournaments";

export function useTournament(id: string) {
  return useQuery({
    queryKey: ["tournament", id],
    queryFn: () => getStatus(id),
    refetchInterval: (q) => (q.state.data?.phase === "done" ? false : 2000),
  });
}
