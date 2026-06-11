import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useTournament } from "../hooks/useTournament";
import { useTeamNames } from "../hooks/useTeams";
import { useSummary } from "../hooks/useAi";
import { PhaseStepper } from "../components/tournament/PhaseStepper";
import { GenerationProgress } from "../components/tournament/GenerationProgress";
import { TeamBadge } from "../components/common/TeamBadge";

const PHASE_TEXT: Record<string, string> = {
  setup: "Setting up…", generating: "Generating 32 AI nations…",
  draw: "Drawing the groups…", group: "Group stage in progress…",
  r16: "Round of 16…", qf: "Quarter-finals…", sf: "Semi-finals…",
  final: "The final!", done: "Tournament complete",
};

const TABS = [
  { to: "/tournaments/$id/groups", label: "Groups", ic: "⚽" },
  { to: "/tournaments/$id/bracket", label: "Bracket", ic: "🏆" },
  { to: "/tournaments/$id/matches", label: "Matches", ic: "📅" },
  { to: "/tournaments/$id/teams", label: "Teams", ic: "🌍" },
] as const;

export function TournamentOverview() {
  const { id } = useParams({ strict: false }) as { id: string };
  const { data, isLoading } = useTournament(id);
  const name = useTeamNames(id);
  const done = data?.phase === "done";
  const [showSummary, setShowSummary] = useState(false);
  const summary = useSummary(id, showSummary && done);
  const champ = data?.championId;

  return (
    <section>
      <div className="hero">
        <span className="ball-bg">⚽</span>
        <span className="eyebrow">🆔 {id.slice(0, 18)}</span>
        <h1>World Cup</h1>
        <p className="sub">
          {isLoading ? "Loading…" : PHASE_TEXT[data?.phase ?? "setup"]}
          {!done && " — this page refreshes automatically."}
        </p>
      </div>

      <PhaseStepper phase={data?.phase ?? "setup"} />

      {done && champ && (
        <div className="champ-banner">
          <span className="cup">🏆</span>
          <div>
            <div className="label">Champion</div>
            <div className="who">
              <Link to="/tournaments/$id/teams/$teamId" params={{ id, teamId: champ }}>
                {name(champ)}
              </Link>
            </div>
          </div>
          <span style={{ flex: 1 }} />
          <TeamBadge name={name(champ)} size="lg" />
        </div>
      )}

      <nav className="subnav" style={{ marginTop: 18 }}>
        {TABS.map((t) => (
          <Link key={t.label} to={t.to} params={{ id }}>{t.ic} {t.label}</Link>
        ))}
      </nav>

      {data && (
        <div className="stat-grid">
          <div className="stat"><div className="k">Teams</div><div className="v">{data.teams}</div></div>
          <div className="stat"><div className="k">Groups</div><div className="v">{data.groups}</div></div>
          <div className="stat"><div className="k">Stage</div>
            <div className="v" style={{ fontSize: "1.1rem", textTransform: "capitalize" }}>
              {(data.phase ?? "—").replace("_", " ")}
            </div></div>
          <div className="stat"><div className="k">Run hash</div>
            <div className="v mono">{data.runHash ? data.runHash.slice(0, 10) : "—"}</div></div>
        </div>
      )}

      {done && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>🎙 AI tournament recap</h3>
            <button className="ghost" onClick={() => setShowSummary(true)} disabled={showSummary}>
              {summary.isFetching ? <><span className="spinner" />Writing…</> : "Generate"}
            </button>
          </div>
          {summary.data?.text && <p className="commentary" style={{ marginTop: 12 }}>{summary.data.text}</p>}
        </div>
      )}

      <GenerationProgress tournamentId={id} />
    </section>
  );
}
