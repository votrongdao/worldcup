import { http } from "./client";
export const getTeam = (id: string) => http<unknown>(`/teams/${id}`);
