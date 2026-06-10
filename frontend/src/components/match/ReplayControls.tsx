import type { MatchEvent } from "../../api/types";
export function ReplayControls({ events }: { events: MatchEvent[] }) {
  return <div className="replay-controls">{/* TODO: scrub through {events.length} events */}</div>;
}
