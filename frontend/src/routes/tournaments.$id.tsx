import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useTournament } from "../hooks/useTournament";
import { useTeamNames } from "../hooks/useTeams";
import { useSummary } from "../hooks/useAi";
import { PhaseStepper } from "../components/tournament/PhaseStepper";

export function TournamentOverview() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data, isLoading } = useTournament(id);
  const name = useTeamNames(id);
  const done = data?.phase === "done";
  const [showSummary, setShowSummary] = useState(false);
  const summary = useSummary(id, showSummary && done);

  return (
    <section>
      <h1>{id}</h1>
      {isLoading && <p className="muted">Loading…</p>}
      <PhaseStepper phase={data?.phase ?? "setup"} />

      {done ? (
        <p className="champion">
          🏆 Champion:{" "}
          {data?.championId
            ? <Link to="/tournaments/$id/teams/$teamId" params={{ id, teamId: data.championId }}>
                {name(data.championId)}
              </Link>
            : "—"}
        </p>
      ) : (
        <p className="muted">Simulating… this page refreshes automatically.</p>
      )}

      <nav className="subnav">
        <Link to="/tournaments/$id/groups" params={{ id }}>Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>Bracket</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>Matches</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>Teams</Link>
      </nav>

      {done && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>AI recap</h3>
            <button className="ghost" onClick={() => setShowSummary(true)} disabled={showSummary}>
              {summary.isFetching ? "Writing…" : "Generate"}
            </button>
          </div>
          {summary.data?.text && <p className="commentary">{summary.data.text}</p>}
        </div>
      )}

      {data && (
        <p className="muted">
          {data.teams} teams · {data.groups} groups · run&nbsp;hash&nbsp;
          {data.runHash ? data.runHash.slice(0, 16) : "—"}
        </p>
      )}
    </section>
  );
}
