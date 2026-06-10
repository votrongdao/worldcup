import { useEffect } from "react";
import { connectMatch } from "../realtime/signalr";
import { useSimStore } from "../stores/simStore";

export function useLiveMatch(matchId: string) {
  const pushFrame = useSimStore((s) => s.pushFrame);
  useEffect(() => {
    const conn = connectMatch(matchId, pushFrame);
    return () => void conn.stop();
  }, [matchId, pushFrame]);
}
