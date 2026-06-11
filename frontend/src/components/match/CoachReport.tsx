import { useMatchReport } from "../../hooks/useMatches";
import type { CoachDecision, PlayerRating, TeamReport } from "../../api/types";

const DEC_IC: Record<string, string> = { substitution: "🔁", formation: "🔀", tactic: "🎯" };

function ratingClass(r: number): string {
  return r >= 7.5 ? "rt hi" : r >= 6.5 ? "rt ok" : r >= 5.5 ? "rt mid" : "rt lo";
}

function PlayerRow({ p }: { p: PlayerRating }) {
  const bits: string[] = [];
  if (p.goals) bits.push(`${p.goals}⚽`);
  if (p.assists) bits.push(`${p.assists}🅰`);
  if (p.saves) bits.push(`${p.saves} saves`);
  if (p.tackles) bits.push(`${p.tackles} tkl`);
  if (p.passes) bits.push(`${Math.round(p.pass_pct * 100)}% pass`);
  bits.push(`${p.distance_km}km`);
  return (
    <div className="pr-row">
      <span className={ratingClass(p.rating)}>{p.rating.toFixed(1)}</span>
      <span className="pr-shirt">#{p.shirt}</span>
      <span className={`pr-pos ${p.role}`}>{p.role}</span>
      <div className="pr-mid">
        <div className="pr-stats">{bits.join(" · ")}</div>
        {p.strengths.length > 0 && (
          <div className="pr-tags">
            {p.strengths.slice(0, 2).map((s) => <span key={s} className="tag good">{s}</span>)}
            {p.weaknesses.slice(0, 1).map((s) => <span key={s} className="tag bad">{s}</span>)}
          </div>
        )}
      </div>
      <span className="pr-min">
        {p.sub_on != null ? `▲${p.sub_on}'` : p.sub_off != null ? `▼${p.sub_off}'` : `${p.minutes}'`}
      </span>
    </div>
  );
}

function SideReport({
  rep, ratings, nation,
}: { rep?: TeamReport; ratings: PlayerRating[]; nation: string }) {
  const sorted = [...ratings].sort((a, b) => b.rating - a.rating);
  return (
    <div className="cr-side">
      <div className="cr-side-h">
        <strong>{nation}</strong>
        {rep && <span className="muted">{rep.formation_end} · {rep.style_end}</span>}
      </div>
      {rep && (
        <div className="cr-sw">
          <div><span className="sw-k good">Strengths</span> {rep.strengths.map((s) => <span key={s} className="tag good">{s}</span>)}</div>
          <div><span className="sw-k bad">Weaknesses</span> {rep.weaknesses.map((s) => <span key={s} className="tag bad">{s}</span>)}</div>
        </div>
      )}
      <div className="pr-list">
        {sorted.map((p) => <PlayerRow key={p.player_id + p.shirt} p={p} />)}
      </div>
    </div>
  );
}

export function CoachReport({ mid, homeNation, awayNation }: {
  mid: string; homeNation: string; awayNation: string;
}) {
  const { data, isLoading } = useMatchReport(mid);
  if (isLoading) return <p className="muted"><span className="spinner" />Loading performance…</p>;
  if (!data || !data.ratings.length) return null;

  const home = data.ratings.filter((r) => r.side === "home");
  const away = data.ratings.filter((r) => r.side === "away");
  const repBy = (s: string) => data.reports.find((r) => r.side === s);
  const decisions = [...data.decisions].sort((a, b) => a.t - b.t);

  return (
    <div className="coach-report">
      <h2>🧠 AI coach & player performance</h2>

      {decisions.length > 0 && (
        <div className="card">
          <h3>Coach decisions</h3>
          <ul className="cr-decisions">
            {decisions.map((d: CoachDecision, i) => (
              <li key={i} className={d.side}>
                <span className="cr-min">{Math.round(d.t)}'</span>
                <span className="cr-ic">{DEC_IC[d.kind]}</span>
                <span className={`cr-badge ${d.side}`}>{d.side === "home" ? homeNation : awayNation}</span>
                <span className="cr-sum">{d.summary}</span>
                <span className="cr-reason muted">— {d.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="cr-grid">
        <SideReport rep={repBy("home")} ratings={home} nation={homeNation} />
        <SideReport rep={repBy("away")} ratings={away} nation={awayNation} />
      </div>
    </div>
  );
}
