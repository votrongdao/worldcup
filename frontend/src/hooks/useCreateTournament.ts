import { useMutation } from "@tanstack/react-query";
import { createTournament } from "../api/tournaments";
import { queryClient } from "../app/queryClient";

export function useCreateTournament() {
  return useMutation({
    mutationFn: createTournament,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tournament"] }),
  });
}
