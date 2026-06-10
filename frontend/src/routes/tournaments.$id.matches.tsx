import { Link, useParams } from "@tanstack/react-router";
import { useMatches } from "../hooks/useMatches";
import { useTeamNames } from "../hooks/useTeams";
import type { MatchSummary, Phase } from "../api/types";

const PHASE_LABEL: Record<string, string> = {
  group: "Group stage", r16: "Round of 16", qf: "Quarter-finals",
  sf: "Semi-finals", final: "Final",
};
const ORDER: Phase[] = ["group", "r16", "qf", "sf", "final"];

export function MatchesPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data: matches = [], isLoading } = useMatches(id);
  const name = useTeamNames(id);

  const byPhase: Record<string, MatchSummary[]> = {};
  for (const m of matches) (byPhase[m.phase] ??= []).push(m);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }}>← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>Bracket</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>Teams</Link>
      </nav>
      <h2>Matches ({matches.length})</h2>
      {isLoading && <p className="muted">Loading…</p>}

      {ORDER.filter((p) => byPhase[p]).map((p) => (
        <div key={p}>
          <h3>{PHASE_LABEL[p] ?? p}</h3>
          {byPhase[p].map((m) => {
            const decided = m.decidedBy === "regulation" ? "" : ` · ${m.decidedBy.replace("_", " ")}`;
            return (
              <Link
                key={m.matchId}
                to="/tournaments/$id/matches/$mid"
                params={{ id, mid: m.matchId }}
                className="match-link"
              >
                <span>{name(m.homeId)}</span>
                <strong>{m.scoreHome} – {m.scoreAway}</strong>
                <span>{name(m.awayId)}</span>
                <span className="muted">{decided} ▸</span>
              </Link>
            );
          })}
        </div>
      ))}
    </section>
  );
}
