import { useEffect, useRef, useState } from "react";
import { drawFrame } from "../../canvas/renderer";
import { connectLive, type LiveMeta } from "../../realtime/ws";
import { CoachPanel } from "./CoachPanel";

type Status = "connecting" | "live" | "ended";
const SPEEDS = [0.3, 0.5, 1, 1.5, 2];

interface LiveEvt { t: number; type: string; team?: "home" | "away"; meta?: Record<string, unknown>; }

export function LiveMatch({ tid, mid, onClock, onEvent, onEnded }: {
  tid: string; mid: string;
  onClock?: (clock: number) => void;
  onEvent?: (e: LiveEvt) => void;
  onEnded?: () => void;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const lastMinRef = useRef(-1);
  const onClockRef = useRef(onClock);
  const onEventRef = useRef(onEvent);
  const onEndedRef = useRef(onEnded);
  useEffect(() => { onClockRef.current = onClock; }, [onClock]);
  useEffect(() => { onEventRef.current = onEvent; }, [onEvent]);
  useEffect(() => { onEndedRef.current = onEnded; }, [onEnded]);
  const [meta, setMeta] = useState<LiveMeta | null>(null);
  const [score, setScore] = useState({ h: 0, a: 0 });
  const [clock, setClock] = useState(0);
  const [status, setStatus] = useState<Status>("connecting");
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    const ctx = ref.current?.getContext("2d") ?? null;
    if (ctx) drawFrame(ctx, undefined); // empty pitch immediately
    const ws = connectLive(tid, mid, {
      onMeta: (m) => { setMeta(m); setStatus("live"); },
      onFrame: (f) => {
        setScore({ h: f.scoreHome, a: f.scoreAway });
        setClock(f.clock);
        const m = Math.floor(f.clock);
        if (m !== lastMinRef.current) { lastMinRef.current = m; onClockRef.current?.(f.clock); }
        if (ctx) drawFrame(ctx, f.frame);
      },
      onEvent: (ev) => onEventRef.current?.({ t: ev.t, type: ev.etype, team: ev.team, meta: ev.meta }),
      onEnd: (e) => {
        setStatus("ended"); setScore({ h: e.scoreHome, a: e.scoreAway });
        onEndedRef.current?.();
      },
      onClose: () => setStatus((s) => (s === "live" ? "ended" : s)),
    });
    wsRef.current = ws;
    return () => ws.close();
  }, [tid, mid]);

  const changeSpeed = (v: number) => {
    setSpeed(v);
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "speed", value: v }));
    }
  };

  return (
    <div className="pitch-wrap">
      {meta && <CoachPanel {...meta} scoreHome={score.h} scoreAway={score.a} clock={clock} />}
      <canvas ref={ref} className="pitch" width={1050} height={680} />
      <div className="replay-controls">
        <span className={`live-status ${status}`}>
          {status === "connecting" ? "Connecting…" : status === "live" ? "● LIVE" : "Full time"}
        </span>
        <span style={{ flex: 1 }} />
        <label className="muted">Speed</label>
        <select value={speed} onChange={(e) => changeSpeed(Number(e.target.value))} disabled={status !== "live"}>
          {SPEEDS.map((s) => <option key={s} value={s}>{s}×</option>)}
        </select>
      </div>
    </div>
  );
}
