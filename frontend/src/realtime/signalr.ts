import * as signalR from "@microsoft/signalr";
import type { Frame } from "../api/types";

export function connectMatch(matchId: string, onFrame: (f: Frame) => void) {
  const conn = new signalR.HubConnectionBuilder()
    .withUrl(`/api/negotiate?match_id=${matchId}`)
    .withAutomaticReconnect()
    .build();
  conn.on("frame", onFrame);
  void conn.start();
  return conn;
}
