import type { Frame } from "../api/types";

const PITCH = { L: 105, W: 68 };

export interface RenderOpts {
  homeColor?: string;
  awayColor?: string;
}

const HOME = "#2b6cb0";   // blue
const AWAY = "#e53e3e";   // red

function line(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

/** Top-down pitch with markings, team-coloured players, and the ball. */
export function drawFrame(ctx: CanvasRenderingContext2D, frame: Frame | undefined, opts: RenderOpts = {}) {
  const { width, height } = ctx.canvas;
  const sx = width / PITCH.L;
  const sy = height / PITCH.W;
  const home = opts.homeColor || HOME;
  const away = opts.awayColor || AWAY;

  // Turf
  ctx.fillStyle = "#3a9d5d";
  ctx.fillRect(0, 0, width, height);
  // Mowing stripes
  ctx.fillStyle = "rgba(255,255,255,0.04)";
  for (let i = 0; i < PITCH.L; i += 10) ctx.fillRect(i * sx, 0, 5 * sx, height);

  // Markings
  ctx.strokeStyle = "rgba(255,255,255,0.75)";
  ctx.lineWidth = 2;
  ctx.strokeRect(1, 1, width - 2, height - 2);
  line(ctx, width / 2, 0, width / 2, height);                       // halfway
  ctx.beginPath();
  ctx.arc(width / 2, height / 2, 9.15 * sx, 0, Math.PI * 2);        // centre circle
  ctx.stroke();
  // Penalty boxes (16.5m deep x 40.3m wide) + goal areas (5.5 x 18.3)
  const boxW = 40.3 * sy, boxD = 16.5 * sx, boxY = (PITCH.W - 40.3) / 2 * sy;
  const gaW = 18.3 * sy, gaD = 5.5 * sx, gaY = (PITCH.W - 18.3) / 2 * sy;
  ctx.strokeRect(0, boxY, boxD, boxW);
  ctx.strokeRect(width - boxD, boxY, boxD, boxW);
  ctx.strokeRect(0, gaY, gaD, gaW);
  ctx.strokeRect(width - gaD, gaY, gaD, gaW);
  // Goals
  const goalW = 7.32 * sy, goalY = (PITCH.W - 7.32) / 2 * sy;
  ctx.lineWidth = 4;
  ctx.strokeStyle = "rgba(255,255,255,0.95)";
  line(ctx, 0, goalY, 0, goalY + goalW);
  line(ctx, width, goalY, width, goalY + goalW);

  if (!frame) return;

  // Players (first 11 = home, last 11 = away)
  frame.players.forEach((p, i) => {
    ctx.beginPath();
    ctx.arc(p[0] * sx, p[1] * sy, 7, 0, Math.PI * 2);
    ctx.fillStyle = i < 11 ? home : away;
    ctx.fill();
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = "rgba(0,0,0,0.35)";
    ctx.stroke();
  });

  // Ball
  ctx.beginPath();
  ctx.arc(frame.ball[0] * sx, frame.ball[1] * sy, 5, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = "#222";
  ctx.stroke();
}
