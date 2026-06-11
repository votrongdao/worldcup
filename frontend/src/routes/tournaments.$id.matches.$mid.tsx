import { useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useReplay } from "../hooks/useReplay";
import { useMatchEvents } from "../hooks/useMatchEvents";
import { useCommentary } from "../hooks/useMatches";
import { PitchReplay } from "../components/match/PitchReplay";
import { LiveMatch } from "../components/match/LiveMatch";
import { CoachReport } from "../components/match/CoachReport";
import { TeamBadge } from "../components/common/TeamBadge";

const TIMELINE_TYPES = new Set(["goal", "penalty", "et_start", "fulltime", "end"]);
const EV_IC: Record<string, string> = {
  goal: "⚽", penalty: "🎯", et_start: "⏱", fulltime: "🟥", end: "🏁",
};

export function MatchDetail() {
  const { id, mid } = useParams({ strict: false }) as { id: string; mid: string };
  const { data, isLoading } = useReplay(id, mid);
  const { data: events = [] } = useMatchEvents(mid);
  const [showC, setShowC] = useState(false);
  const [mode, setMode] = useState<"replay" | "live">("replay");
  const com = useCommentary(mid, showC);

  const timeline = events.filter((e) => TIMELINE_TYPES.has(e.type));

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id/matches" params={{ id }} className="back">← Matches</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
      </nav>

      {data && (
        <div className="scoreboard">
          <div className="side home">
            <span className="nm">{data.homeNation}</span>
            <TeamBadge name={data.homeNation} size="md" />
          </div>
          <div className="mid">
            <div className="nums">
              {data.scoreHome}<span className="dash">–</span>{data.scoreAway}
            </div>
            {data.decidedBy !== "regulation" && (
              <div className="decided">decided by {data.decidedBy.replace("_", " ")}</div>
            )}
          </div>
          <div className="side away">
            <TeamBadge name={data.awayNation} size="md" />
            <span className="nm">{data.awayNation}</span>
          </div>
        </div>
      )}

      <div className="seg">
        <button className={mode === "replay" ? "on" : ""} onClick={() => setMode("replay")}>⟲ Replay</button>
        <button className={mode === "live" ? "on" : ""} onClick={() => setMode("live")}>● Watch live</button>
      </div>

      {mode === "live" ? (
        <LiveMatch tid={id} mid={mid} />
      ) : (
        <>
          {isLoading && <p className="muted"><span className="spinner" />Generating replay…</p>}
          {data && <PitchReplay frames={data.frames} duration={data.duration} />}
        </>
      )}

      <div className="card">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>🎙 AI commentary</h3>
          <button className="ghost" onClick={() => setShowC(true)} disabled={showC}>
            {com.isFetching ? <><span className="spinner" />Thinking…</> : "Generate"}
          </button>
        </div>
        {com.data?.commentary && <p className="commentary" style={{ marginTop: 12 }}>“{com.data.commentary}”</p>}
      </div>

      <h2>Timeline</h2>
      {timeline.length === 0 ? (
        <p className="muted">No key events recorded.</p>
      ) : (
        <ul className="timeline">
          {timeline.map((e, i) => (
            <li key={i} className={e.type}>
              <span className="min">{Math.round(e.t)}'</span>
              <span className="ic">{EV_IC[e.type] ?? "•"}</span>
              <span className="ev">{e.type.replace("_", " ")}</span>
              {e.team ? <span className="muted">· {e.team}</span> : null}
            </li>
          ))}
        </ul>
      )}

      {data && <CoachReport mid={mid} homeNation={data.homeNation} awayNation={data.awayNation} />}
    </section>
  );
}
