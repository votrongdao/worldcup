import { useMemo } from "react";
import type { MatchEvent } from "../../api/types";

interface Moment {
  t: number;
  side?: "home" | "away";
  ic: string;
  text: string;
  big?: boolean;
}

// Short, AI-style commentary lines built deterministically from the event log.
const GOAL_LINES = [
  "drives it home", "finds the net", "makes no mistake", "buries the chance",
  "lights up the scoreboard", "with a clinical finish",
];

function build(events: MatchEvent[], home: string, away: string): Moment[] {
  const team = (s?: string) => (s === "home" ? home : s === "away" ? away : "");
  const out: Moment[] = [];
  let gi = 0;
  for (const e of events) {
    const m = (e as MatchEvent & { meta?: Record<string, unknown> }).meta ?? {};
    const side = e.team;
    switch (e.type) {
      case "kickoff":
        out.push({ t: e.t, ic: "🟢", text: `Kick-off — ${home} vs ${away}.` });
        break;
      case "goal": {
        const sc = (m.score as number[]) ?? [];
        const line = GOAL_LINES[gi++ % GOAL_LINES.length];
        out.push({
          t: e.t, side, ic: "⚽", big: true,
          text: `GOAL! ${team(side)} ${line}${sc.length ? ` — ${sc[0]}–${sc[1]}` : ""}.`,
        });
        break;
      }
      case "penalty":
        out.push({ t: e.t, side, ic: "🎯", text: `Penalty to ${team(side)}!` });
        break;
      case "substitution":
        out.push({
          t: e.t, side, ic: "🔁", big: true,
          text: `${team(side)} make a change — ${m.summary ?? "substitution"}${m.reason ? ` (${m.reason})` : ""}.`,
        });
        break;
      case "formation_change":
        out.push({
          t: e.t, side, ic: "🔀", big: true,
          text: `${team(side)} reshape: ${m.summary ?? "new formation"}${m.reason ? ` — ${m.reason}` : ""}.`,
        });
        break;
      case "tactic_change":
        out.push({
          t: e.t, side, ic: "🎯",
          text: `${team(side)} switch tactics — ${m.summary ?? "new approach"}.`,
        });
        break;
      case "et_start":
        out.push({ t: e.t, ic: "⏱", text: "We go to extra time." });
        break;
      case "fulltime": {
        const sc = (m.score as number[]) ?? [];
        out.push({
          t: e.t, ic: "🏁", big: true,
          text: `Full time${sc.length ? ` — ${home} ${sc[0]}–${sc[1]} ${away}` : ""}.`,
        });
        break;
      }
      default:
        break; // shots/saves/report are too frequent / not narrative
    }
  }
  return out.sort((a, b) => a.t - b.t);
}

export function MatchCommentary({
  events, clock, homeNation, awayNation, live,
}: {
  events: MatchEvent[]; clock: number;
  homeNation: string; awayNation: string; live?: boolean;
}) {
  const moments = useMemo(() => build(events, homeNation, awayNation), [events, homeNation, awayNation]);
  // reveal moments up to the current clock; if nothing is playing yet, show all
  const shown = clock > 0 ? moments.filter((m) => m.t <= clock + 0.01) : moments;
  const latest = shown[shown.length - 1];
  const feed = [...shown].reverse();

  if (!moments.length) return null;

  return (
    <div className="commentary-box">
      <div className="cb-head">
        <span className="cb-title">🎙 AI Commentary</span>
        {live && <span className="chip live"><span className="dot" />LIVE</span>}
      </div>
      {latest && (
        <div className={`cb-latest ${latest.side ?? ""}`} key={`${latest.t}-${latest.text}`}>
          <span className="cb-ic">{latest.ic}</span>
          <span className="cb-min">{Math.round(latest.t)}'</span>
          <span className="cb-text">{latest.text}</span>
        </div>
      )}
      <ul className="cb-feed">
        {feed.slice(0, 30).map((mo, i) => (
          <li key={`${mo.t}-${i}`} className={mo.big ? "big" : ""}>
            <span className="cb-min">{Math.round(mo.t)}'</span>
            <span className="cb-ic">{mo.ic}</span>
            <span className="cb-text">{mo.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
