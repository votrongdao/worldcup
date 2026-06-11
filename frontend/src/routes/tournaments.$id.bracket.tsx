import { Link, useParams } from "@tanstack/react-router";
import { BracketView } from "../components/tournament/BracketView";

export function BracketPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }} className="back">← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>⚽ Groups</Link>
        <Link to="/tournaments/$id/matches" params={{ id }}>📅 Matches</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>🌍 Teams</Link>
      </nav>
      <h1>🏆 Knockout bracket</h1>
      <BracketView tournamentId={id} />
    </section>
  );
}
