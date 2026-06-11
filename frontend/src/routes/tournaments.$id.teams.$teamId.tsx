import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useTeamDetail } from "../hooks/useTeamDetail";
import { useReport } from "../hooks/useAi";
import { SquadTable } from "../components/team/SquadTable";
import { CoachCard } from "../components/team/CoachCard";
import { PlayerRadar } from "../components/team/PlayerRadar";
import { TeamBadge } from "../components/common/TeamBadge";
import type { PlayerDetail } from "../api/types";

function standout(squad: PlayerDetail[], xi: string[]): PlayerDetail | undefined {
  const pool = squad.filter((p) => xi.includes(p.id) && p.role !== "GK");
  return (pool.length ? pool : squad).slice().sort(
    (a, b) =>
      (b.shooting + b.passing + b.dribbling + b.pace + b.vision) -
      (a.shooting + a.passing + a.dribbling + a.pace + a.vision),
  )[0];
}

export function TeamDetail() {
  const { id, teamId } = useParams({ strict: false }) as { id: string; teamId: string };
  const { data, isLoading } = useTeamDetail(id, teamId);
  const [showR, setShowR] = useState(false);
  const report = useReport(id, teamId, showR);

  if (isLoading || !data) return <p className="muted"><span className="spinner" />Loading team…</p>;
  const star = standout(data.squad, data.xi);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id/teams" params={{ id }} className="back">← Teams</Link>
        {data.group && <Link to="/tournaments/$id/groups" params={{ id }}>⚽ Group {data.group}</Link>}
      </nav>

      <div className="team-hero">
        <div className="top">
          <TeamBadge name={data.nation} size="lg" />
          <div>
            <h1>{data.nation}</h1>
            <div className="tags">
              <span className="chip">Tier {data.tier}</span>
              <span className="chip">{data.styleDna.replace("_", " ")}</span>
              <span className="chip">{data.coach.formation}</span>
              {data.group && <span className="chip">Group {data.group}</span>}
              <span className="chip">★ {data.rating.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        <CoachCard coach={data.coach} />
        {star && (
          <div className="card">
            <h3>⭐ Standout · {star.role}</h3>
            <PlayerRadar player={star} />
          </div>
        )}
      </div>

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>🔎 AI scouting report</h3>
          <button className="ghost" onClick={() => setShowR(true)} disabled={showR}>
            {report.isFetching ? <><span className="spinner" />Scouting…</> : "Generate"}
          </button>
        </div>
        {report.data?.text && <p className="commentary" style={{ marginTop: 12 }}>{report.data.text}</p>}
      </div>

      <h2>Squad</h2>
      <div className="card">
        <SquadTable squad={data.squad} xi={data.xi} />
      </div>
    </section>
  );
}
