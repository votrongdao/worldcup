import type { CoachDetail } from "../../api/types";

const TRAITS: [keyof CoachDetail, string][] = [
  ["aggression", "Aggression"], ["lineHeight", "Line height"],
  ["tempo", "Tempo"], ["pressing", "Pressing"], ["directness", "Directness"],
];

export function CoachCard({ coach }: { coach: CoachDetail }) {
  return (
    <div className="card">
      <h3>🎯 Coach · {coach.formation}</h3>
      {TRAITS.map(([k, label]) => {
        const pct = Math.round((coach[k] as number) * 100);
        return (
          <div className="trait" key={k}>
            <span>{label}</span>
            <div className="bar">
              <div style={{ width: `${pct}%` }} />
            </div>
            <span className="val">{pct}</span>
          </div>
        );
      })}
    </div>
  );
}
