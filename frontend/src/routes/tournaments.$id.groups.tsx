import { Link, useParams } from "@tanstack/react-router";
import { GroupTable } from "../components/tournament/GroupTable";

export function GroupsPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }} className="back">← Overview</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>📅 Matches</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>🌍 Teams</Link>
      </nav>
      <h1>⚽ Group standings</h1>
      <GroupTable tournamentId={id} />
    </section>
  );
}
