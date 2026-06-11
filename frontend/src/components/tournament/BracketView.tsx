import { Link } from "@tanstack/react-router";
import { useBracket } from "../../hooks/useBracket";
import { useTeamNames } from "../../hooks/useTeams";
import { TeamBadge } from "../common/TeamBadge";
import type { BracketSlot, Phase } from "../../api/types";

const ROUNDS: { phase: Phase; label: string }[] = [
  { phase: "r16", label: "Round of 16" },
  { phase: "qf", label: "Quarter-finals" },
  { phase: "sf", label: "Semi-finals" },
  { phase: "final", label: "Final" },
];

function Side({
  id, name, winnerId, decided,
}: { id?: string | null; name: string; winnerId?: string | null; decided: boolean }) {
  const isWin = decided && winnerId != null && winnerId === id;
  const isLose = decided && winnerId != null && id != null && winnerId !== id;
  return (
    <div className={`side ${isWin ? "win" : ""} ${isLose ? "lose" : ""}`}>
      <TeamBadge name={id ? name : "?"} size="sm" />
      <span className="nm">{id ? name : "TBD"}</span>
      {isWin && <span className="sc">✓</span>}
    </div>
  );
}

export function BracketView({ tournamentId }: { tournamentId: string }) {
  const { data: slots = [], isLoading } = useBracket(tournamentId);
  const name = useTeamNames(tournamentId);

  if (isLoading) return <p className="muted"><span className="spinner" />Loading bracket…</p>;
  if (!slots.length)
    return <div className="empty"><span className="big">🏆</span>No knockout matches yet — finish the group stage.</div>;

  return (
    <div className="bracket">
      {ROUNDS.map(({ phase, label }) => {
        const ties = slots.filter((s) => s.phase === phase);
        if (!ties.length) return null;
        const isFinal = phase === "final";
        return (
          <div className="bracket-col" key={phase}>
            <h3>{label}</h3>
            {ties.map((tie: BracketSlot) => {
              const decided = tie.winnerId != null;
              return (
                <Link
                  className={`bracket-tie ${isFinal ? "bracket-final-tie" : ""}`}
                  key={tie.matchId}
                  to="/tournaments/$id/matches/$mid"
                  params={{ id: tournamentId, mid: tie.matchId }}
                >
                  <Side id={tie.homeId} name={name(tie.homeId)} winnerId={tie.winnerId} decided={decided} />
                  <Side id={tie.awayId} name={name(tie.awayId)} winnerId={tie.winnerId} decided={decided} />
                </Link>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
