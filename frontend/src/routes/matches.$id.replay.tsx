import { useMatchEvents } from "../hooks/useMatchEvents";
import { PitchCanvas } from "../components/match/PitchCanvas";
import { ReplayControls } from "../components/match/ReplayControls";

export function ReplayMatch({ id }: { id: string }) {
  const { data: events } = useMatchEvents(id);
  return <><PitchCanvas /><ReplayControls events={events ?? []} /></>;
}
