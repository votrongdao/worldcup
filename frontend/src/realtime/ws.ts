import type { Frame } from "../api/types";

export interface LiveMeta {
  matchId: string;
  homeNation: string;
  awayNation: string;
  homeFormation: string;
  awayFormation: string;
  homeStyle: string;
  awayStyle: string;
}
export interface LiveFrame {
  frame: Frame;
  clock: number;
  scoreHome: number;
  scoreAway: number;
}
export interface LiveEnd { scoreHome: number; scoreAway: number; decidedBy: string; }

export interface LiveHandlers {
  onMeta?: (m: LiveMeta) => void;
  onFrame?: (f: LiveFrame) => void;
  onEnd?: (e: LiveEnd) => void;
  onClose?: () => void;
}

/** Connect to the live match WebSocket (nginx proxies /api/ws/* to the API). */
export function connectLive(tid: string, mid: string, h: LiveHandlers): WebSocket {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/api/ws/match/${tid}/${mid}`);
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.type === "meta") h.onMeta?.(m as LiveMeta);
    else if (m.type === "frame") h.onFrame?.(m as LiveFrame);
    else if (m.type === "end") h.onEnd?.(m as LiveEnd);
  };
  ws.onclose = () => h.onClose?.();
  return ws;
}
