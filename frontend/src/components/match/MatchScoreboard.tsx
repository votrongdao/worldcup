export function MatchScoreboard({ matchId }: { matchId: string }) {
  return <div className="scoreboard" data-match={matchId}>{/* live score */}</div>;
}
