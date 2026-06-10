import { useEffect, useRef, useState } from "react";
import { drawFrame } from "../../canvas/renderer";
import { connectLive, type LiveMeta } from "../../realtime/ws";
import { CoachPanel } from "./CoachPanel";

type Status = "connecting" | "live" | "ended";

export function LiveMatch({ tid, mid }: { tid: string; mid: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [meta, setMeta] = useState<LiveMeta | null>(null);
  const [score, setScore] = useState({ h: 0, a: 0 });
  const [clock, setClock] = useState(0);
  const [status, setStatus] = useState<Status>("connecting");

  useEffect(() => {
    const ctx = ref.current?.getContext("2d") ?? null;
    if (ctx) drawFrame(ctx, undefined); // draw empty pitch immediately
    const ws = connectLive(tid, mid, {
      onMeta: (m) => { setMeta(m); setStatus("live"); },
      onFrame: (f) => {
        setScore({ h: f.scoreHome, a: f.scoreAway });
        setClock(f.clock);
        if (ctx) drawFrame(ctx, f.frame);
      },
      onEnd: (e) => { setStatus("ended"); setScore({ h: e.scoreHome, a: e.scoreAway }); },
      onClose: () => setStatus((s) => (s === "live" ? "ended" : s)),
    });
    return () => ws.close();
  }, [tid, mid]);

  return (
    <div className="pitch-wrap">
      {meta && <CoachPanel {...meta} scoreHome={score.h} scoreAway={score.a} clock={clock} />}
      <canvas ref={ref} className="pitch" width={1050} height={680} />
      <div className={`live-status ${status}`}>
        {status === "connecting" ? "Connecting…" : status === "live" ? "● LIVE" : "Full time"}
      </div>
    </div>
  );
}
