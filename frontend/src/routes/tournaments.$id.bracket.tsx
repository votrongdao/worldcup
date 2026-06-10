import { Link, useParams } from "@tanstack/react-router";
import { BracketView } from "../components/tournament/BracketView";

export function BracketPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }}>← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>Groups</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>Matches</Link>
      </nav>
      <h2>Knockout bracket</h2>
      <BracketView tournamentId={id} />
    </section>
  );
}
