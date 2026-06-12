import { Link, useParams } from "@tanstack/react-router";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useFixtures } from "../hooks/useFixtures";
import { useTeamNames } from "../hooks/useTeams";
import { playRound, playAll } from "../api/tournaments";
import { TeamBadge } from "../components/common/TeamBadge";
import type { Fixture, Phase } from "../api/types";

const PHASE_LABEL: Record<string, string> = {
  group: "Group stage", r16: "Round of 16", qf: "Quarter-finals",
  sf: "Semi-finals", final: "Final", third_place: "Third-place playoff",
};
const PHASE_IC: Record<string, string> = {
  group: "⚽", r16: "🔥", qf: "💥", sf: "⭐", final: "🥇", third_place: "🥉",
};
const ORDER: Phase[] = ["group", "r16", "qf", "sf", "third_place", "final"];

function FixtureRow({ f, tid, name }: { f: Fixture; tid: string; name: (id?: string | null) => string }) {
  const homeWin = f.played && f.winnerId === f.homeId;
  const awayWin = f.played && f.winnerId === f.awayId;
  return (
    <Link
      to="/tournaments/$id/matches/$mid" params={{ id: tid, mid: f.id }}
      className={`match-link ${f.played ? "" : "scheduled"}`}
      title={f.played ? undefined : "Not played — click to conduct live"}
    >
      <span className="side home" style={{ fontWeight: homeWin ? 700 : 500 }}>
        <span className="nm">{name(f.homeId)}</span>
        <TeamBadge name={name(f.homeId)} size="sm" />
      </span>
      <span className={`score ${f.played ? "" : "pending"}`}>
        {f.played ? `${f.scoreHome} – ${f.scoreAway}` : "▶"}
      </span>
      <span className="side away" style={{ fontWeight: awayWin ? 700 : 500 }}>
        <TeamBadge name={name(f.awayId)} size="sm" />
        <span className="nm">{name(f.awayId)}</span>
      </span>
    </Link>
  );
}

export function MatchesPage() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data: fixtures = [], isLoading } = useFixtures(id);
  const name = useTeamNames(id);
  const qc = useQueryClient();
  const round = useMutation({
    mutationFn: () => playRound(id),
    onSuccess: () => qc.invalidateQueries(),
  });
  const all = useMutation({
    mutationFn: () => playAll(id),
    onSuccess: () => qc.invalidateQueries(),
  });

  const byPhase: Record<string, Fixture[]> = {};
  for (const f of fixtures) (byPhase[f.phase] ??= []).push(f);
  const unplayed = fixtures.filter((f) => !f.played).length;

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id" params={{ id }} className="back">← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>⚽ Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>🌍 Teams</Link>
      </nav>

      <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline" }}>
        <h1>Schedule <span className="chip" style={{ verticalAlign: "middle" }}>
          {fixtures.length - unplayed}/{fixtures.length}
        </span></h1>
        {unplayed > 0 && (
          <div className="row">
            <button className="ghost" onClick={() => round.mutate()} disabled={round.isPending || all.isPending}>
              {round.isPending ? <><span className="spinner" />Playing round…</> : "▶ Play next round"}
            </button>
            <button onClick={() => all.mutate()} disabled={all.isPending}>
              {all.isPending ? <><span className="spinner" />Playing…</> : "⏩ Play to end"}
            </button>
          </div>
        )}
      </div>
      {isLoading && <p className="muted"><span className="spinner" />Loading…</p>}
      {!isLoading && !fixtures.length && (
        <div className="empty"><span className="big">📅</span>No fixtures yet — drawing groups.</div>
      )}

      {ORDER.filter((p) => byPhase[p]).map((p) => {
        const items = byPhase[p];
        const days = [...new Set(items.map((f) => f.matchday))].sort((a, b) => a - b);
        const useDays = p === "group" && days.length > 1;
        return (
          <div key={p}>
            <div className="phase-head">
              <h3>{PHASE_IC[p]} {PHASE_LABEL[p] ?? p}</h3>
              <span className="chip">{items.filter((f) => f.played).length}/{items.length}</span>
              <span className="rule" />
            </div>
            {useDays ? (
              days.map((d) => (
                <div key={d} style={{ marginBottom: 10 }}>
                  <div className="matchday-label">Matchday {d}</div>
                  {items.filter((f) => f.matchday === d).map((f) => (
                    <FixtureRow key={f.id} f={f} tid={id} name={name} />
                  ))}
                </div>
              ))
            ) : (
              items.map((f) => <FixtureRow key={f.id} f={f} tid={id} name={name} />)
            )}
          </div>
        );
      })}
    </section>
  );
}
