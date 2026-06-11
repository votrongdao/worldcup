import { useEffect } from "react";
import { Link } from "@tanstack/react-router";
import { useTournament } from "../../hooks/useTournament";
import { useTeams, useTeamNames } from "../../hooks/useTeams";
import { useStandings } from "../../hooks/useStandings";
import { useMatches } from "../../hooks/useMatches";
import { TeamBadge } from "../common/TeamBadge";
import type { MatchSummary, Phase, TeamSummary } from "../../api/types";

const KNOCKOUT_ORDER: Phase[] = ["r16", "qf", "sf", "final"];

interface Meta {
  title: string;
  ic: string;
  agent: string;
  how: string[];
  kind: "teams" | "draw" | "group" | "knockout" | "done";
  phase?: Phase;
}

const META: Record<string, Meta> = {
  gen: {
    title: "Generate AI nations", ic: "🌍", agent: "NationalTeamGenerator",
    kind: "teams",
    how: [
      "Every random choice derives from the single master seed — there is no live randomness anywhere in the core.",
      "For nation i, the engine computes a stable sub-seed sub_seed(seed, \"nation\", i) — a SHA-256 of the seed plus that path — then deterministically rolls a strength tier (1–4), a footballing Style DNA, a full squad of players (pace, shooting, passing, defending… per role) and a head coach (formation + tactical traits).",
      "Same seed ⇒ byte-identical nations, every single run.",
    ],
  },
  draw: {
    title: "Group draw", ic: "🎲", agent: "DrawAgent",
    kind: "draw",
    how: [
      "The 32 nations are seeded by strength into pots, then drawn into 8 groups of 4.",
      "The draw is reproducible from the master seed via its own namespaced sub-seed, so the bracket is identical on every replay.",
    ],
  },
  group: {
    title: "Group stage", ic: "⚽", agent: "SchedulerAgent · MatchEngine · ResultAggregator",
    kind: "group",
    how: [
      "SchedulerAgent builds a round-robin per group — every team meets the other three.",
      "Each fixture is enqueued on the MatchQueue. A worker runs the pure MatchEngine (a fixed 1/120s physics timestep), appends events to the event log, and publishes the result on the ResultBus.",
      "Results fold into the standings — 3 points for a win, 1 for a draw — and the top two of each group advance to the Round of 16.",
    ],
  },
  r16: {
    title: "Round of 16", ic: "🔥", agent: "ProgressionManager", kind: "knockout", phase: "r16",
    how: [
      "The 16 group qualifiers seed a single-elimination bracket.",
      "If a knockout tie is level after regulation, the tiebreaker chain resolves it: extra time, then a penalty shootout. The winner advances, the loser is out.",
    ],
  },
  qf: {
    title: "Quarter-finals", ic: "💥", agent: "ProgressionManager", kind: "knockout", phase: "qf",
    how: [
      "The eight R16 winners meet. Same single-elimination rules — regulation, then extra time, then penalties if still level.",
    ],
  },
  sf: {
    title: "Semi-finals", ic: "⭐", agent: "ProgressionManager", kind: "knockout", phase: "sf",
    how: [
      "The final four. Winners reach the final; the two losers contest the third-place playoff.",
    ],
  },
  final: {
    title: "Final", ic: "🥇", agent: "ProgressionManager", kind: "knockout", phase: "final",
    how: [
      "One match decides the champion. A third-place playoff is also played between the beaten semi-finalists.",
    ],
  },
  done: {
    title: "Champion crowned", ic: "🏆", agent: "RunSupervisor", kind: "done",
    how: [
      "The final winner is crowned and the full tournament read-model is snapshotted to the store.",
      "The entire run is hashed — run_hash() over the ordered event log. Equal seeds always produce equal hashes; that hash is the reproducibility guarantee.",
    ],
  },
};

function groupOf(teams: TeamSummary[]): Map<string, string> {
  return new Map(teams.map((t) => [t.id, t.group]));
}

export function StepDetail({
  tournamentId, stepKey, onClose,
}: { tournamentId: string; stepKey: string; onClose: () => void }) {
  const meta = META[stepKey];
  const { data: status } = useTournament(tournamentId);
  const { data: teams = [] } = useTeams(tournamentId);
  const { data: standings = {} } = useStandings(tournamentId);
  const { data: matches = [] } = useMatches(tournamentId);
  const name = useTeamNames(tournamentId);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!meta) return null;

  const teamGroup = groupOf(teams);

  function MatchRow({ m }: { m: MatchSummary }) {
    const homeWin = m.winnerId === m.homeId;
    const awayWin = m.winnerId === m.awayId;
    const extra = m.decidedBy && m.decidedBy !== "regulation" ? m.decidedBy.replace("_", " ") : "";
    return (
      <Link
        className="dd-match"
        to="/tournaments/$id/matches/$mid"
        params={{ id: tournamentId, mid: m.matchId }}
        onClick={onClose}
      >
        <span className="dd-side home" style={{ fontWeight: homeWin ? 700 : 500 }}>
          <span className="nm">{name(m.homeId)}</span>
          <TeamBadge name={name(m.homeId)} size="sm" />
        </span>
        <span className="dd-score">{m.scoreHome}–{m.scoreAway}</span>
        <span className="dd-side away" style={{ fontWeight: awayWin ? 700 : 500 }}>
          <TeamBadge name={name(m.awayId)} size="sm" />
          <span className="nm">{name(m.awayId)}</span>
        </span>
        {extra && <span className="dd-extra">{extra}</span>}
      </Link>
    );
  }

  function Body() {
    if (meta.kind === "teams") {
      const sorted = [...teams].sort((a, b) => b.rating - a.rating);
      return (
        <>
          <p className="muted">{teams.length} nations generated{teams.length ? ", strongest first:" : " yet."}</p>
          <div className="dd-teamgrid">
            {sorted.map((t) => (
              <Link
                key={t.id} className="dd-team"
                to="/tournaments/$id/teams/$teamId"
                params={{ id: tournamentId, teamId: t.id }} onClick={onClose}
              >
                <TeamBadge name={t.nation} size="md" />
                <div className="dd-team-info">
                  <div className="nm">{t.nation}</div>
                  <div className="muted">T{t.tier} · {t.styleDna.replace("_", " ")}</div>
                </div>
                <span className="dd-rating">{t.rating.toFixed(1)}</span>
              </Link>
            ))}
          </div>
        </>
      );
    }

    if (meta.kind === "draw") {
      const byGroup: Record<string, TeamSummary[]> = {};
      for (const t of teams) (byGroup[t.group || "?"] ??= []).push(t);
      const entries = Object.entries(byGroup).sort(([a], [b]) => a.localeCompare(b));
      if (!entries.length) return <p className="muted">Draw not completed yet.</p>;
      return (
        <div className="dd-groups">
          {entries.map(([g, list]) => (
            <div className="dd-group" key={g}>
              <div className="dd-group-h"><span className="g-tag">{g}</span> Group {g}</div>
              {list.map((t) => (
                <div className="dd-group-row" key={t.id}>
                  <TeamBadge name={t.nation} size="sm" />
                  <span className="nm">{t.nation}</span>
                  <span className="chip tier">T{t.tier}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      );
    }

    if (meta.kind === "group") {
      const groupEntries = Object.entries(standings).sort(([a], [b]) => a.localeCompare(b));
      if (!groupEntries.length) return <p className="muted">Group stage hasn’t started yet.</p>;
      const groupMatches = matches.filter((m) => m.phase === "group");
      return (
        <div className="dd-groups">
          {groupEntries.map(([g, rows]) => {
            const ms = groupMatches.filter((m) => teamGroup.get(m.homeId) === g);
            return (
              <div className="dd-group wide" key={g}>
                <div className="dd-group-h"><span className="g-tag">{g}</span> Group {g}</div>
                <table className="standings">
                  <thead><tr><th>Team</th><th className="num">P</th><th className="num">Pts</th></tr></thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={r.teamId} className={i < 2 ? "qualified" : undefined}>
                        <td className="team"><span className="team-cell">
                          <span className="rank">{i + 1}</span>
                          <TeamBadge name={name(r.teamId)} size="sm" />
                          <span className="name">{name(r.teamId)}</span>
                        </span></td>
                        <td className="num">{r.played}</td>
                        <td className="num pts">{r.pts}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {ms.length > 0 && (
                  <div className="dd-matchlist">
                    {ms.map((m) => <MatchRow key={m.matchId} m={m} />)}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      );
    }

    if (meta.kind === "knockout" && meta.phase) {
      const ms = matches.filter((m) => m.phase === meta.phase);
      if (!ms.length) return <p className="muted">This round hasn’t been played yet.</p>;
      return <div className="dd-matchlist">{ms.map((m) => <MatchRow key={m.matchId} m={m} />)}</div>;
    }

    // done
    const champId = status?.championId;
    const champ = teams.find((t) => t.id === champId);
    const path = matches
      .filter((m) => (m.homeId === champId || m.awayId === champId) && KNOCKOUT_ORDER.includes(m.phase))
      .sort((a, b) => KNOCKOUT_ORDER.indexOf(a.phase) - KNOCKOUT_ORDER.indexOf(b.phase));
    return (
      <>
        {champ ? (
          <div className="champ-banner" style={{ marginTop: 0 }}>
            <span className="cup">🏆</span>
            <div>
              <div className="label">Champion</div>
              <div className="who">{champ.nation}</div>
            </div>
            <span style={{ flex: 1 }} />
            <TeamBadge name={champ.nation} size="lg" />
          </div>
        ) : <p className="muted">No champion yet.</p>}

        {status?.runHash && (
          <div className="dd-hash">
            <span className="muted">run hash</span>
            <code>{status.runHash}</code>
          </div>
        )}

        {path.length > 0 && (
          <>
            <h3 style={{ marginTop: 18 }}>Road to the title</h3>
            <div className="dd-matchlist">{path.map((m) => <MatchRow key={m.matchId} m={m} />)}</div>
          </>
        )}
      </>
    );
  }

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} role="dialog" aria-label={meta.title}>
        <div className="drawer-head">
          <div className="drawer-title"><span className="dh-ic">{meta.ic}</span> {meta.title}</div>
          <button className="drawer-x" onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className="drawer-body">
          <div className="how-block">
            <div className="how-agent">⚙ {meta.agent}</div>
            {meta.how.map((p, i) => <p key={i}>{p}</p>)}
          </div>
          <h3>What happened</h3>
          <Body />
        </div>
      </aside>
    </div>
  );
}
