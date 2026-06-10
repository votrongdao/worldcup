import { useQuery } from "@tanstack/react-query";
import { getEvents } from "../api/matches";

export const useMatchEvents = (id: string) =>
  useQuery({ queryKey: ["match-events", id], queryFn: () => getEvents(id) });
