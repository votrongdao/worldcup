import { Link, useParams } from "@tanstack/react-router";
import { useTournament } from "../hooks/useTournament";
import { useTeamNames } from "../hooks/useTeams";
import { PhaseStepper } from "../components/tournament/PhaseStepper";

export function TournamentOverview() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data, isLoading } = useTournament(id);
  const name = useTeamNames(id);

  return (
    <section>
      <h1>{id}</h1>
      {isLoading && <p className="muted">Loading…</p>}
      <PhaseStepper phase={data?.phase ?? "setup"} />

      {data?.phase === "done" ? (
        <p className="champion">🏆 Champion: {name(data.championId)}</p>
      ) : (
        <p className="muted">Simulating… this page refreshes automatically.</p>
      )}

      <nav className="subnav">
        <Link to="/tournaments/$id/groups" params={{ id }}>Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>Bracket</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>Matches</Link>
      </nav>

      {data && (
        <p className="muted">
          {data.teams} teams · {data.groups} groups · run&nbsp;hash&nbsp;
          {data.runHash ? data.runHash.slice(0, 16) : "—"}
        </p>
      )}
    </section>
  );
}
