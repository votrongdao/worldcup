import { useEffect, useRef, useState } from "react";
import { drawFrame } from "../../canvas/renderer";
import { lerpFrame } from "../../canvas/interpolate";
import type { Frame } from "../../api/types";

const MIN_PER_SEC = 2.2; // playback: sim-minutes advanced per real second at 1x

export function PitchReplay({
  frames, duration, onClock,
}: { frames: Frame[]; duration: number; onClock?: (t: number) => void }) {
  const ref = useRef<HTMLCanvasElement>(null);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(1);
  const [t, setT] = useState(0);

  const tRef = useRef(0);
  const playingRef = useRef(true);
  const speedRef = useRef(1);
  const lastMinRef = useRef(-1);
  const onClockRef = useRef(onClock);
  useEffect(() => { playingRef.current = playing; }, [playing]);
  useEffect(() => { speedRef.current = speed; }, [speed]);
  useEffect(() => { onClockRef.current = onClock; }, [onClock]);

  function emitClock(v: number) {
    const m = Math.floor(v);
    if (m !== lastMinRef.current) { lastMinRef.current = m; onClockRef.current?.(v); }
  }

  function frameAt(time: number): Frame | undefined {
    if (!frames.length) return undefined;
    let i = 0;
    while (i < frames.length - 1 && frames[i + 1].t <= time) i++;
    const a = frames[i];
    const b = frames[Math.min(i + 1, frames.length - 1)];
    const span = b.t - a.t || 1;
    return lerpFrame(a, b, Math.max(0, Math.min(1, (time - a.t) / span)));
  }

  useEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (!ctx) return;
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      if (playingRef.current) {
        let nt = tRef.current + dt * MIN_PER_SEC * speedRef.current;
        if (nt >= duration) { nt = duration; setPlaying(false); }
        tRef.current = nt;
        setT(nt);
        emitClock(nt);
      }
      drawFrame(ctx, frameAt(tRef.current));
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [frames, duration]);

  const scrub = (v: number) => { setPlaying(false); tRef.current = v; setT(v); emitClock(v); };
  const restart = () => { tRef.current = 0; setT(0); lastMinRef.current = -1; emitClock(0); setPlaying(true); };

  return (
    <div className="pitch-wrap">
      <canvas ref={ref} className="pitch" width={1050} height={680} />
      <div className="replay-controls">
        <button onClick={() => setPlaying((p) => !p)}>{playing ? "⏸ Pause" : "▶ Play"}</button>
        <button className="ghost" onClick={restart}>⟲ Restart</button>
        <input
          type="range" min={0} max={duration} step={0.1} value={t}
          onChange={(e) => scrub(Number(e.target.value))}
        />
        <span className="clock">{Math.floor(t)}'</span>
        <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
          <option value={0.3}>0.3×</option>
          <option value={0.5}>0.5×</option>
          <option value={1}>1×</option>
          <option value={1.5}>1.5×</option>
          <option value={2}>2×</option>
        </select>
      </div>
      <div className="legend">
        <span><i className="dot home" /> Home</span>
        <span><i className="dot away" /> Away</span>
      </div>
    </div>
  );
}
