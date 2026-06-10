import { useLiveMatch } from "../hooks/useLiveMatch";
import { PitchCanvas } from "../components/match/PitchCanvas";
import { MatchScoreboard } from "../components/match/MatchScoreboard";

export function LiveMatch({ id }: { id: string }) {
  useLiveMatch(id);
  return <><MatchScoreboard matchId={id} /><PitchCanvas /></>;
}
