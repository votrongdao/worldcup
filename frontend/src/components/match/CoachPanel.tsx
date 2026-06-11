import type { LiveMeta } from "../../realtime/ws";
import { TeamBadge } from "../common/TeamBadge";

interface Props extends LiveMeta {
  scoreHome: number;
  scoreAway: number;
  clock: number;
}

/** Live HUD: per-team formation + tactical style, centre score and clock. */
export function CoachPanel(p: Props) {
  return (
    <div className="coach-hud">
      <div className="team-tac home">
        <div className="nat"><TeamBadge name={p.homeNation} size="sm" /> {p.homeNation}</div>
        <div className="tac">{p.homeFormation} · {p.homeStyle}</div>
      </div>
      <div className="hud-mid">
        <div className="score">{p.scoreHome} – {p.scoreAway}</div>
        <div className="clock">{Math.floor(p.clock)}'</div>
      </div>
      <div className="team-tac away">
        <div className="nat">{p.awayNation} <TeamBadge name={p.awayNation} size="sm" /></div>
        <div className="tac">{p.awayFormation} · {p.awayStyle}</div>
      </div>
    </div>
  );
}
