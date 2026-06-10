import { useBracket } from "../../hooks/useBracket";
import { useTeamNames } from "../../hooks/useTeams";
import type { BracketSlot, Phase } from "../../api/types";

const ROUNDS: { phase: Phase; label: string }[] = [
  { phase: "r16", label: "Round of 16" },
  { phase: "qf", label: "Quarter-finals" },
  { phase: "sf", label: "Semi-finals" },
  { phase: "final", label: "Final" },
];

export function BracketView({ tournamentId }: { tournamentId: string }) {
  const { data: slots = [], isLoading } = useBracket(tournamentId);
  const name = useTeamNames(tournamentId);

  if (isLoading) return <p className="muted">Loading bracket…</p>;
  if (!slots.length) return <p className="muted">No knockout matches yet.</p>;

  return (
    <div className="grid">
      {ROUNDS.map(({ phase, label }) => {
        const ties = slots.filter((s) => s.phase === phase);
        if (!ties.length) return null;
        return (
          <div className="card bracket-round" key={phase}>
            <h3>{label}</h3>
            {ties.map((tie: BracketSlot) => (
              <div className="bracket-tie" key={tie.matchId}>
                <span className={tie.winnerId === tie.homeId ? "win" : ""}>{name(tie.homeId)}</span>
                {" v "}
                <span className={tie.winnerId === tie.awayId ? "win" : ""}>{name(tie.awayId)}</span>
              </div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
