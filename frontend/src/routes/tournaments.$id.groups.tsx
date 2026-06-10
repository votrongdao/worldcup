import { Link, useParams } from "@tanstack/react-router";
import { GroupTable } from "../components/tournament/GroupTable";

export function GroupsPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }}>← Overview</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>Bracket</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>Matches</Link>
      </nav>
      <h2>Group standings</h2>
      <GroupTable tournamentId={id} />
    </section>
  );
}
