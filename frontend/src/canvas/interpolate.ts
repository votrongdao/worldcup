import type { Frame } from "../api/types";
// Linearly interpolate between two frames for smooth 60fps rendering.
export function lerpFrame(a: Frame, b: Frame, t: number): Frame {
  const mix = (p: [number, number], q: [number, number]): [number, number] =>
    [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t];
  return {
    t: a.t + (b.t - a.t) * t,
    ball: mix(a.ball, b.ball),
    players: a.players.map((p, i) => mix(p, b.players[i] ?? p)),
  };
}
