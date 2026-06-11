import { Link, useParams } from "@tanstack/react-router";
import { useTeams } from "../hooks/useTeams";
import { TeamBadge } from "../components/common/TeamBadge";
import type { TeamSummary } from "../api/types";

export function TeamsPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data: teams = [], isLoading } = useTeams(id);

  const byGroup: Record<string, TeamSummary[]> = {};
  for (const t of teams) (byGroup[t.group || "?"] ??= []).push(t);

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }} className="back">← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>⚽ Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
      </nav>

      <h1>Teams <span className="chip" style={{ verticalAlign: "middle" }}>{teams.length}</span></h1>
      {isLoading && <p className="muted"><span className="spinner" />Loading…</p>}

      <div className="grid">
        {Object.entries(byGroup).sort(([a], [b]) => a.localeCompare(b)).map(([g, list]) => (
          <div className="card group-card hoverable" key={g}>
            <h3><span className="g-tag">{g}</span> Group {g}</h3>
            {list.map((t) => (
              <Link
                key={t.id}
                to="/tournaments/$id/teams/$teamId"
                params={{ id, teamId: t.id }}
                className="team-card-link"
              >
                <div className="team-row">
                  <TeamBadge name={t.nation} size="sm" />
                  <span className="name">{t.nation}</span>
                  <span className="chip tier">T{t.tier}</span>
                  <span className="muted" style={{ fontSize: ".74rem" }}>
                    {t.styleDna.replace("_", " ")}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
