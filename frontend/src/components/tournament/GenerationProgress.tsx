import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { http } from "../../api/client";
import { useTournament } from "../../hooks/useTournament";
import { TeamBadge } from "../common/TeamBadge";
import { StepDetail } from "./StepDetail";
import type { MatchSummary, Phase, TeamSummary } from "../../api/types";

// Lifecycle order used to compare a step against the live phase.
const ORDER: Phase[] = ["setup", "generating", "draw", "group", "r16", "qf", "sf", "final", "done"];

type StepKind = "teams" | "draw" | "matches" | "done";
interface Step {
  key: string;
  label: string;
  ic: string;
  at: Phase;        // the lifecycle phase this step belongs to
  kind: StepKind;
  phase?: Phase;    // for match steps: which match phase to count
}

const STEPS: Step[] = [
  { key: "gen", label: "Generate AI nations", ic: "🌍", at: "generating", kind: "teams" },
  { key: "draw", label: "Group draw", ic: "🎲", at: "draw", kind: "draw" },
  { key: "group", label: "Group stage", ic: "⚽", at: "group", kind: "matches", phase: "group" },
  { key: "r16", label: "Round of 16", ic: "🔥", at: "r16", kind: "matches", phase: "r16" },
  { key: "qf", label: "Quarter-finals", ic: "💥", at: "qf", kind: "matches", phase: "qf" },
  { key: "sf", label: "Semi-finals", ic: "⭐", at: "sf", kind: "matches", phase: "sf" },
  { key: "final", label: "Final", ic: "🥇", at: "final", kind: "matches", phase: "final" },
  { key: "done", label: "Champion crowned", ic: "🏆", at: "done", kind: "done" },
];

/** Expected match count per phase, derived from the format. */
function expectedFor(phase: Phase, teams: number, groups: number): number {
  const perGroup = groups ? Math.round(teams / groups) : 4;
  if (phase === "group") return groups * (perGroup * (perGroup - 1)) / 2;
  const knockoutTeams = groups * 2; // top 2 advance
  const sizes: Record<string, number> = {
    r16: knockoutTeams / 2, qf: knockoutTeams / 4, sf: knockoutTeams / 8, final: knockoutTeams / 16,
  };
  return Math.max(1, Math.round(sizes[phase] ?? 1));
}

export function GenerationProgress({ tournamentId }: { tournamentId: string }) {
  const { data: status } = useTournament(tournamentId);
  const live = !!status && status.phase !== "done";

  // Poll teams + matches while the tournament is still running so the detail
  // updates in real time. Same query keys as the page hooks → shared cache.
  const { data: teams = [] } = useQuery({
    queryKey: ["teams", tournamentId],
    queryFn: () => http<TeamSummary[]>(`/tournaments/${tournamentId}/teams`),
    refetchInterval: live ? 1500 : false,
  });
  const { data: matches = [] } = useQuery({
    queryKey: ["matches", tournamentId],
    queryFn: () => http<MatchSummary[]>(`/tournaments/${tournamentId}/matches`),
    refetchInterval: live ? 1500 : false,
  });

  const [openStep, setOpenStep] = useState<string | null>(null);

  if (!status) return null;

  const curIdx = ORDER.indexOf(status.phase);
  const totalTeams = status.teams || 32;
  const groups = status.groups || 8;
  const played: Record<string, number> = {};
  for (const m of matches) played[m.phase] = (played[m.phase] ?? 0) + 1;

  // Overall % across all expected matches.
  const matchPhases: Phase[] = ["group", "r16", "qf", "sf", "final"];
  const expectedTotal = matchPhases.reduce((s, p) => s + expectedFor(p, totalTeams, groups), 0);
  const playedTotal = matchPhases.reduce((s, p) => s + Math.min(played[p] ?? 0, expectedFor(p, totalTeams, groups)), 0);
  const pct = status.phase === "done" ? 100 : Math.round((playedTotal / expectedTotal) * 100);

  function rowFor(step: Step) {
    const stepIdx = ORDER.indexOf(step.at);
    const state = curIdx > stepIdx ? "done" : curIdx === stepIdx ? "active" : "pending";

    let detail: ReactNode = null;
    let barPct: number | null = null;

    if (step.kind === "teams") {
      const n = teams.length;
      detail = state === "pending" ? "waiting…" : `${n} / ${totalTeams} teams`;
      barPct = state === "done" ? 100 : Math.round((n / totalTeams) * 100);
    } else if (step.kind === "draw") {
      detail = state === "pending" ? "waiting…" : `${groups} groups drawn`;
      barPct = state === "pending" ? 0 : 100;
    } else if (step.kind === "matches" && step.phase) {
      const exp = expectedFor(step.phase, totalTeams, groups);
      const done = Math.min(played[step.phase] ?? 0, exp);
      detail = state === "pending" ? "waiting…" : `${done} / ${exp} matches`;
      barPct = state === "done" ? 100 : Math.round((done / exp) * 100);
    } else if (step.kind === "done") {
      if (status!.phase === "done" && status!.championId) {
        const champ = teams.find((t) => t.id === status!.championId);
        detail = (
          <span className="prog-champ">
            <TeamBadge name={champ?.nation} size="sm" /> {champ?.nation ?? "—"}
          </span>
        );
      } else {
        detail = "waiting…";
      }
    }

    return (
      <li key={step.key} className={`prog-step ${state}`}>
        <button type="button" className="prog-rowbtn" onClick={() => setOpenStep(step.key)}>
          <span className="prog-mark">
            {state === "done" ? "✓" : state === "active" ? <span className="spinner" /> : step.ic}
          </span>
          <div className="prog-body">
            <div className="prog-line">
              <span className="prog-label">{step.label}</span>
              <span className="prog-detail">{detail}</span>
            </div>
            {barPct != null && (
              <div className="prog-bar"><div style={{ width: `${barPct}%` }} /></div>
            )}
          </div>
          <span className="prog-chevron" aria-hidden>›</span>
        </button>
      </li>
    );
  }

  return (
    <>
      <div className="card prog-card">
        <div className="row" style={{ justifyContent: "space-between", alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Live progress</h3>
          <span className={`live-status ${live ? "live" : "ended"}`}>
            {live ? "Simulating" : "Complete"} · {pct}%
          </span>
        </div>
        <div className="prog-overall"><div style={{ width: `${pct}%` }} /></div>
        <p className="muted" style={{ margin: "10px 0 0", fontSize: ".82rem" }}>
          Tap any step to see how the system builds it.
        </p>
        <ol className="prog-list">{STEPS.map(rowFor)}</ol>
      </div>
      {openStep && (
        <StepDetail tournamentId={tournamentId} stepKey={openStep} onClose={() => setOpenStep(null)} />
      )}
    </>
  );
}
