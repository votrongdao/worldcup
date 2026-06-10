import { useStandings } from "../../hooks/useStandings";
import { useTeamNames } from "../../hooks/useTeams";

export function GroupTable({ tournamentId }: { tournamentId: string }) {
  const { data: groups = {}, isLoading } = useStandings(tournamentId);
  const name = useTeamNames(tournamentId);

  if (isLoading) return <p className="muted">Loading standings…</p>;
  const entries = Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  if (!entries.length) return <p className="muted">No standings yet — group stage in progress.</p>;

  return (
    <div className="grid">
      {entries.map(([group, rows]) => (
        <div className="card" key={group}>
          <h3>Group {group}</h3>
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
              {rows.map((r, i) => (
                <tr key={r.teamId} className={i < 2 ? "qualified" : undefined}>
                  <td className="team" title={`${name(r.teamId)} · ${r.gf}-${r.ga}`}>
                    {name(r.teamId)}
                  </td>
                  <td className="num">{r.played}</td><td className="num">{r.w}</td>
                  <td className="num">{r.d}</td><td className="num">{r.l}</td>
                  <td className="num">{r.gf - r.ga > 0 ? `+${r.gf - r.ga}` : r.gf - r.ga}</td>
                  <td className="num pts">{r.pts}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
