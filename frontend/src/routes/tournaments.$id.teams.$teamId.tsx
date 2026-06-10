import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useTeamDetail } from "../hooks/useTeamDetail";
import { useReport } from "../hooks/useAi";
import { SquadTable } from "../components/team/SquadTable";
import { CoachCard } from "../components/team/CoachCard";
import { PlayerRadar } from "../components/team/PlayerRadar";
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

  if (isLoading || !data) return <p className="muted">Loading team…</p>;
  const star = standout(data.squad, data.xi);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id/teams" params={{ id }}>← Teams</Link>
        {data.group && <Link to="/tournaments/$id/groups" params={{ id }}>Group {data.group}</Link>}
      </nav>

      <h1>{data.nation}</h1>
      <p className="muted">
        Tier {data.tier} · {data.styleDna.replace("_", " ")} · {data.coach.formation}
        {data.group ? ` · Group ${data.group}` : ""} · rating {data.rating.toFixed(2)}
      </p>

      <div className="row" style={{ alignItems: "flex-start", gap: 16 }}>
        <CoachCard coach={data.coach} />
        {star && (
          <div className="card">
            <h3>Standout ({star.role})</h3>
            <PlayerRadar player={star} />
          </div>
        )}
      </div>

      <div className="row" style={{ marginTop: 8 }}>
        <button className="ghost" onClick={() => setShowR(true)} disabled={showR}>
          {report.isFetching ? "Scouting…" : "🔎 AI scouting report"}
        </button>
        {report.data?.text && <p className="commentary" style={{ margin: 0 }}>{report.data.text}</p>}
      </div>

      <h2>Squad</h2>
      <div className="card">
        <SquadTable squad={data.squad} xi={data.xi} />
      </div>
    </section>
  );
}
