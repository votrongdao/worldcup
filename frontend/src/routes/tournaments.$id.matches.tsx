import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useMatches, useCommentary } from "../hooks/useMatches";
import { useTeamNames } from "../hooks/useTeams";
import type { MatchSummary } from "../api/types";

function MatchRow({ m, name }: { m: MatchSummary; name: (id?: string | null) => string }) {
  const [show, setShow] = useState(false);
  const { data, isFetching } = useCommentary(m.matchId, show);
  const decided = m.decidedBy === "regulation" ? "" : ` (${m.decidedBy.replace("_", " ")})`;
  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <span>
          <strong>{name(m.homeId)}</strong> {m.scoreHome} – {m.scoreAway}{" "}
          <strong>{name(m.awayId)}</strong>
          <span className="muted">{decided}</span>
        </span>
        <button className="ghost" onClick={() => setShow(true)} disabled={show}>
          {isFetching ? "Thinking…" : "AI commentary"}
        </button>
      </div>
      {data?.commentary && <p className="commentary">“{data.commentary}”</p>}
    </div>
  );
}

export function MatchesPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data: matches = [], isLoading } = useMatches(id);
  const name = useTeamNames(id);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }}>← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>Bracket</Link>
      </nav>
      <h2>Matches ({matches.length})</h2>
      {isLoading && <p className="muted">Loading…</p>}
      {matches.map((m) => (
        <MatchRow key={m.matchId} m={m} name={name} />
      ))}
    </section>
  );
}
