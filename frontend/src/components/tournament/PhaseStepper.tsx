import type { Phase } from "../../api/types";

const STEPS: { phase: Phase; label: string; ic: string }[] = [
  { phase: "generating", label: "Generate", ic: "🌍" },
  { phase: "draw", label: "Draw", ic: "🎲" },
  { phase: "group", label: "Groups", ic: "⚽" },
  { phase: "r16", label: "R16", ic: "🔥" },
  { phase: "qf", label: "QF", ic: "💥" },
  { phase: "sf", label: "SF", ic: "⭐" },
  { phase: "final", label: "Final", ic: "🥇" },
  { phase: "done", label: "Done", ic: "🏆" },
];

export function PhaseStepper({ phase }: { phase: Phase }) {
  const current = STEPS.findIndex((s) => s.phase === phase);
  return (
    <ol className="phase-stepper">
      {STEPS.map((s, i) => {
        const state = i < current || phase === "done" && s.phase !== "done"
          ? "done"
          : s.phase === phase ? "active" : "";
        return (
          <li key={s.phase} className={state}>
            <span className="ic">{state === "done" ? "✓" : s.ic}</span>
            {s.label}
          </li>
        );
      })}
    </ol>
  );
}
