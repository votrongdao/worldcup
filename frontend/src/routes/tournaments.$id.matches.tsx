import { Link, useParams } from "@tanstack/react-router";
import { useMatches } from "../hooks/useMatches";
import { useTeamNames } from "../hooks/useTeams";
import { TeamBadge } from "../components/common/TeamBadge";
import type { MatchSummary, Phase } from "../api/types";

const PHASE_LABEL: Record<string, string> = {
  group: "Group stage", r16: "Round of 16", qf: "Quarter-finals",
  sf: "Semi-finals", final: "Final",
};
const PHASE_IC: Record<string, string> = {
  group: "⚽", r16: "🔥", qf: "💥", sf: "⭐", final: "🥇",
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
        <Link to="/tournaments/$id" params={{ id }} className="back">← Overview</Link>
        <Link to="/tournaments/$id/groups" params={{ id }}>⚽ Groups</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
        <Link to="/tournaments/$id/teams" params={{ id }}>🌍 Teams</Link>
      </nav>

      <h1>Matches <span className="chip" style={{ verticalAlign: "middle" }}>{matches.length}</span></h1>
      {isLoading && <p className="muted"><span className="spinner" />Loading…</p>}

      {ORDER.filter((p) => byPhase[p]).map((p) => (
        <div key={p}>
          <div className="phase-head">
            <h3>{PHASE_IC[p]} {PHASE_LABEL[p] ?? p}</h3>
            <span className="chip">{byPhase[p].length}</span>
            <span className="rule" />
          </div>
          {byPhase[p].map((m) => {
            const decided = m.decidedBy === "regulation" ? "" : m.decidedBy.replace("_", " ");
            const homeWin = m.winnerId === m.homeId;
            const awayWin = m.winnerId === m.awayId;
            return (
              <Link
                key={m.matchId}
                to="/tournaments/$id/matches/$mid"
                params={{ id, mid: m.matchId }}
                className="match-link"
              >
                <span className="side home" style={{ fontWeight: homeWin ? 700 : 500 }}>
                  <span className="nm">{name(m.homeId)}</span>
                  <TeamBadge name={name(m.homeId)} size="sm" />
                </span>
                <span className="score">{m.scoreHome} – {m.scoreAway}</span>
                <span className="side away" style={{ fontWeight: awayWin ? 700 : 500 }}>
                  <TeamBadge name={name(m.awayId)} size="sm" />
                  <span className="nm">{name(m.awayId)}</span>
                </span>
                {decided && <span className="meta muted">decided by {decided}</span>}
              </Link>
            );
          })}
        </div>
      ))}
    </section>
  );
}
