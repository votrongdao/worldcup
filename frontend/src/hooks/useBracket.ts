import { useQuery } from "@tanstack/react-query";
import { http } from "../api/client";
import type { BracketSlot } from "../api/types";

export const useBracket = (id: string) =>
  useQuery({
    queryKey: ["bracket", id],
    queryFn: () => http<BracketSlot[]>(`/tournaments/${id}/bracket`),
  });
