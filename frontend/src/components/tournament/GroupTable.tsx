import { useStandings } from "../../hooks/useStandings";
import { useTeamNames } from "../../hooks/useTeams";
import { TeamBadge } from "../common/TeamBadge";

export function GroupTable({ tournamentId }: { tournamentId: string }) {
  const { data: groups = {}, isLoading } = useStandings(tournamentId);
  const name = useTeamNames(tournamentId);

  if (isLoading)
    return (
      <div className="grid">
        {Array.from({ length: 4 }).map((_, i) => (
          <div className="card" key={i}>
            <div className="skeleton" style={{ height: 22, width: "40%", marginBottom: 14 }} />
            {Array.from({ length: 4 }).map((__, j) => (
              <div className="skeleton" key={j} style={{ height: 16, margin: "10px 0" }} />
            ))}
          </div>
        ))}
      </div>
    );

  const entries = Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  if (!entries.length)
    return <div className="empty"><span className="big">⚽</span>No standings yet — group stage in progress.</div>;

  return (
    <div className="grid">
      {entries.map(([group, rows]) => (
        <div className="card group-card hoverable" key={group}>
          <h3><span className="g-tag">{group}</span> Group {group}</h3>
          <table className="standings">
            <thead>
              <tr>
                <th>Team</th>
                <th className="num">P</th><th className="num">W</th>
                <th className="num">D</th><th className="num">L</th>
                <th className="num">GD</th><th className="num">Pts</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => {
                const gd = r.gf - r.ga;
                return (
                  <tr key={r.teamId} className={i < 2 ? "qualified" : undefined}>
                    <td className="team" title={`${name(r.teamId)} · ${r.gf}-${r.ga}`}>
                      <span className="team-cell">
                        <span className="rank">{i + 1}</span>
                        <TeamBadge name={name(r.teamId)} size="sm" />
                        <span className="name">{name(r.teamId)}</span>
                      </span>
                    </td>
                    <td className="num">{r.played}</td><td className="num">{r.w}</td>
                    <td className="num">{r.d}</td><td className="num">{r.l}</td>
                    <td className={`num gd ${gd > 0 ? "pos" : gd < 0 ? "neg" : ""}`}>
                      {gd > 0 ? `+${gd}` : gd}
                    </td>
                    <td className="num pts">{r.pts}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="legend-q"><i /> Top 2 advance to the knockout stage</div>
        </div>
      ))}
    </div>
  );
}
