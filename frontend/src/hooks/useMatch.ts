import { useQuery } from "@tanstack/react-query";
import { getMatch } from "../api/matches";

export const useMatch = (id: string) =>
  useQuery({ queryKey: ["match", id], queryFn: () => getMatch(id) });
