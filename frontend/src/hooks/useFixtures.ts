import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { Fixture } from "../api/types";

/** Full schedule (played + upcoming), merged with results. Polls while any
 *  fixture is still unplayed so the group lists fill in live. */
export const useFixtures = (id: string) =>
  useQuery({
    queryKey: ["fixtures", id],
    queryFn: () => http<Fixture[]>(`/tournaments/${id}/fixtures`),
    refetchInterval: (q) =>
      q.state.data && q.state.data.length > 0 && q.state.data.every((f) => f.played)
        ? false
        : 2500,
  });
