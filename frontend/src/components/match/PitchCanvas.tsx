import { useRef, useEffect, useState } from "react";
import { drawFrame } from "../../canvas/renderer";
import { useSimStore } from "../../stores/simStore";

export function PitchCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);
  const store = useSimStore((s) => s);
  const [, force] = useState(0);
  useEffect(() => store.subscribe(() => force((n) => n + 1)), [store]);
  useEffect(() => {
    const ctx = ref.current?.getContext("2d");
    if (!ctx) return;
    let raf = requestAnimationFrame(function loop() {
      drawFrame(ctx, store.current());
      raf = requestAnimationFrame(loop);
    });
    return () => cancelAnimationFrame(raf);
  }, [store]);
  return <canvas ref={ref} className="pitch" width={1050} height={680} />;
}
