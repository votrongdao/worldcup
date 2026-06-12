import { Link } from "@tanstack/react-router";
import { useStandings } from "../../hooks/useStandings";
import { useFixtures } from "../../hooks/useFixtures";
import { useTeamNames } from "../../hooks/useTeams";
import { TeamBadge } from "../common/TeamBadge";
import type { Fixture } from "../../api/types";

function FixtureRow({ f, tid, name }: { f: Fixture; tid: string; name: (id?: string | null) => string }) {
  const homeWin = f.played && f.winnerId === f.homeId;
  const awayWin = f.played && f.winnerId === f.awayId;
  const inner = (
    <>
      <span className="gf-side home" style={{ fontWeight: homeWin ? 700 : 500 }}>
        <span className="nm">{name(f.homeId)}</span>
        <TeamBadge name={name(f.homeId)} size="sm" />
      </span>
      <span className={`gf-score ${f.played ? "" : "pending"}`}>
        {f.played ? `${f.scoreHome}–${f.scoreAway}` : "vs"}
      </span>
      <span className="gf-side away" style={{ fontWeight: awayWin ? 700 : 500 }}>
        <TeamBadge name={name(f.awayId)} size="sm" />
        <span className="nm">{name(f.awayId)}</span>
      </span>
    </>
  );
  return f.played ? (
    <Link className="gf-row" to="/tournaments/$id/matches/$mid" params={{ id: tid, mid: f.id }}>{inner}</Link>
  ) : (
    <div className="gf-row scheduled" title="Scheduled — not played yet">{inner}</div>
  );
}

export function GroupTable({ tournamentId }: { tournamentId: string }) {
  const { data: groups = {}, isLoading } = useStandings(tournamentId);
  const { data: fixtures = [] } = useFixtures(tournamentId);
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
  const groupFixtures = fixtures.filter((f) => f.group);
  if (!entries.length && !groupFixtures.length)
    return <div className="empty"><span className="big">⚽</span>No standings yet — group stage in progress.</div>;

  // if standings not ready yet, fall back to grouping by the fixtures' group letters
  const groupKeys = entries.length
    ? entries.map(([g]) => g)
    : [...new Set(groupFixtures.map((f) => f.group as string))].sort();

  return (
    <div className="grid">
      {groupKeys.map((group) => {
        const rows = groups[group] ?? [];
        const fx = groupFixtures
          .filter((f) => f.group === group)
          .sort((a, b) => a.matchday - b.matchday);
        const playedN = fx.filter((f) => f.played).length;
        return (
          <div className="card group-card hoverable" key={group}>
            <h3><span className="g-tag">{group}</span> Group {group}</h3>
            {rows.length > 0 && (
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
            )}
            {fx.length > 0 && (
              <div className="group-fixtures">
                <div className="gf-head">Matches <span className="muted">{playedN}/{fx.length}</span></div>
                {fx.map((f) => <FixtureRow key={f.id} f={f} tid={tournamentId} name={name} />)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
