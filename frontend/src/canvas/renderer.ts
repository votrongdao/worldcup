import type { Frame } from "../api/types";
const PITCH = { L: 105, W: 68 };

// Light, text-free top-down renderer (carries over the simulation's aesthetic).
export function drawFrame(ctx: CanvasRenderingContext2D, frame: Frame | undefined) {
  const { width, height } = ctx.canvas;
  ctx.clearRect(0, 0, width, height);
  if (!frame) return;
  const sx = width / PITCH.L, sy = height / PITCH.W;
  ctx.fillStyle = "#eef6ee"; ctx.fillRect(0, 0, width, height);   // pale pitch
  for (const [px, py] of frame.players) {
    ctx.beginPath(); ctx.arc(px * sx, py * sy, 8, 0, Math.PI * 2);
    ctx.fillStyle = "#2bb673"; ctx.fill();
  }
  ctx.beginPath(); ctx.arc(frame.ball[0] * sx, frame.ball[1] * sy, 4, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff"; ctx.fill();
}
