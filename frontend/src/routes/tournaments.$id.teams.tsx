import { Link, useParams } from "@tanstack/react-router";
import { useTeams } from "../hooks/useTeams";
import type { TeamSummary } from "../api/types";

export function TeamsPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data: teams = [], isLoading } = useTeams(id);

  const byGroup: Record<string, TeamSummary[]> = {};
  for (const t of teams) (byGroup[t.group || "?"] ??= []).push(t);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }}>← Overview</Link>
      </nav>
      <h2>Teams</h2>
      {isLoading && <p className="muted">Loading…</p>}
      <div className="grid">
        {Object.entries(byGroup).sort(([a], [b]) => a.localeCompare(b)).map(([g, list]) => (
          <div className="card" key={g}>
            <h3>Group {g}</h3>
            {list.map((t) => (
              <div key={t.id} className="team-row">
                <Link to="/tournaments/$id/teams/$teamId" params={{ id, teamId: t.id }}>
                  {t.nation}
                </Link>
                <span className="muted">T{t.tier} · {t.styleDna.replace("_", " ")}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
