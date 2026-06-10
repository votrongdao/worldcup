import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useReplay } from "../hooks/useReplay";
import { useMatchEvents } from "../hooks/useMatchEvents";
import { useCommentary } from "../hooks/useMatches";
import { PitchReplay } from "../components/match/PitchReplay";

const TIMELINE_TYPES = new Set(["goal", "penalty", "et_start", "fulltime", "end"]);

export function MatchDetail() {
  const { id, mid } = useParams({ strict: false }) as { id: string; mid: string };
  const { data, isLoading } = useReplay(id, mid);
  const { data: events = [] } = useMatchEvents(mid);
  const [showC, setShowC] = useState(false);
  const com = useCommentary(mid, showC);

  const timeline = events.filter((e) => TIMELINE_TYPES.has(e.type));

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id/matches" params={{ id }}>← Matches</Link>
      </nav>

      {data && (
        <div className="scoreboard-big">
          <span className="side home">{data.homeNation}</span>
          <strong>{data.scoreHome} – {data.scoreAway}</strong>
          <span className="side away">{data.awayNation}</span>
        </div>
      )}
      {data && data.decidedBy !== "regulation" && (
        <p className="muted" style={{ textAlign: "center" }}>
          decided by {data.decidedBy.replace("_", " ")}
        </p>
      )}

      {isLoading && <p className="muted">Generating replay…</p>}
      {data && <PitchReplay frames={data.frames} duration={data.duration} />}

      <div className="row" style={{ marginTop: 12 }}>
        <button className="ghost" onClick={() => setShowC(true)} disabled={showC}>
          {com.isFetching ? "Thinking…" : "🎙 AI commentary"}
        </button>
        {com.data?.commentary && <p className="commentary" style={{ margin: 0 }}>“{com.data.commentary}”</p>}
      </div>

      <h2>Timeline</h2>
      <ul className="timeline">
        {timeline.map((e, i) => (
          <li key={i}>
            <span className="min">{Math.round(e.t)}'</span>
            <b>{e.type.replace("_", " ")}</b>
            {e.team ? <span className="muted"> · {e.team}</span> : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
