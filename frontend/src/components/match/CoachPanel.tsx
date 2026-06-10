import type { LiveMeta } from "../../realtime/ws";

interface Props extends LiveMeta {
  scoreHome: number;
  scoreAway: number;
  clock: number;
}

/** Live HUD (ported from match.html): per-team formation + tactical style,
    centre score and clock. Read-only for a tournament match. */
export function CoachPanel(p: Props) {
  return (
    <div className="coach-hud">
      <div className="team-tac home">
        <div className="nat"><i className="dot home" /> {p.homeNation}</div>
        <div className="tac">{p.homeFormation} · {p.homeStyle}</div>
      </div>
      <div className="hud-mid">
        <div className="score">{p.scoreHome} – {p.scoreAway}</div>
        <div className="clock">{Math.floor(p.clock)}'</div>
      </div>
      <div className="team-tac away">
        <div className="nat">{p.awayNation} <i className="dot away" /></div>
        <div className="tac">{p.awayFormation} · {p.awayStyle}</div>
      </div>
    </div>
  );
}
