import type { MatchEvent } from "../../api/types";
export function MatchTimeline({ events }: { events: MatchEvent[] }) {
  return <ul className="timeline">{events.map((e, i) => <li key={i}>{e.type}@{e.t.toFixed(0)}</li>)}</ul>;
}
