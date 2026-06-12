import { useMemo, useState } from "react";
import { Link, useParams } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useReplay } from "../hooks/useReplay";
import { useMatchEvents } from "../hooks/useMatchEvents";
import { useCommentary } from "../hooks/useMatches";
import { useFixtures } from "../hooks/useFixtures";
import { useTeamNames } from "../hooks/useTeams";
import { PitchReplay } from "../components/match/PitchReplay";
import { LiveMatch } from "../components/match/LiveMatch";
import { CoachReport } from "../components/match/CoachReport";
import { MatchCommentary } from "../components/match/MatchCommentary";
import { TeamBadge } from "../components/common/TeamBadge";
import type { MatchEvent } from "../api/types";

const TIMELINE_TYPES = new Set([
  "goal", "penalty", "substitution", "formation_change", "tactic_change", "et_start", "fulltime", "end",
]);
const EV_IC: Record<string, string> = {
  goal: "⚽", penalty: "🎯", substitution: "🔁", formation_change: "🔀",
  tactic_change: "🎯", et_start: "⏱", fulltime: "🟥", end: "🏁",
};

export function MatchDetail() {
  const { id, mid } = useParams({ strict: false }) as { id: string; mid: string };
  const qc = useQueryClient();
  const { data: fixtures = [] } = useFixtures(id);
  const fx = useMemo(() => fixtures.find((f) => f.id === mid), [fixtures, mid]);
  const { data: replay, isLoading } = useReplay(id, mid);
  const { data: events = [] } = useMatchEvents(mid);
  const name = useTeamNames(id);

  const [showC, setShowC] = useState(false);
  const [clock, setClock] = useState(0);
  const [started, setStarted] = useState(false);
  const [liveEvents, setLiveEvents] = useState<MatchEvent[]>([]);
  const com = useCommentary(mid, showC);

  // Played? prefer the fixture flag; fall back to whether a replay exists.
  const isPlayed = fx ? fx.played : !!replay;
  const homeNation = replay?.homeNation ?? name(fx?.homeId);
  const awayNation = replay?.awayNation ?? name(fx?.awayId);

  const onLiveEnded = () => {
    // the match was just recorded server-side — refresh everything
    qc.invalidateQueries();
  };

  const commentaryEvents = !isPlayed ? liveEvents : events;
  const timeline = (isPlayed ? events : liveEvents).filter((e) => TIMELINE_TYPES.has(e.type));

  return (
    <section>
      <nav className="subnav">
        <Link to="/tournaments/$id/matches" params={{ id }} className="back">← Matches</Link>
        <Link to="/tournaments/$id/bracket" params={{ id }}>🏆 Bracket</Link>
      </nav>

      <div className="scoreboard">
        <div className="side home">
          <span className="nm">{homeNation}</span>
          <TeamBadge name={homeNation} size="md" />
        </div>
        <div className="mid">
          <div className="nums">
            {isPlayed && replay
              ? <>{replay.scoreHome}<span className="dash">–</span>{replay.scoreAway}</>
              : <span className="dash">vs</span>}
          </div>
          {isPlayed && replay && replay.decidedBy !== "regulation" && (
            <div className="decided">decided by {replay.decidedBy.replace("_", " ")}</div>
          )}
          {!isPlayed && <div className="decided">{fx ? `${fx.phase} · not played` : "scheduled"}</div>}
        </div>
        <div className="side away">
          <TeamBadge name={awayNation} size="md" />
          <span className="nm">{awayNation}</span>
        </div>
      </div>

      <div className="match-stage">
        <div className="stage-pitch">
          {isPlayed ? (
            <>
              {isLoading && <p className="muted"><span className="spinner" />Generating replay…</p>}
              {replay && <PitchReplay frames={replay.frames} duration={replay.duration} onClock={setClock} />}
            </>
          ) : started ? (
            <LiveMatch
              tid={id} mid={mid} onClock={setClock} onEnded={onLiveEnded}
              onEvent={(e) => setLiveEvents((p) => [...p, e as MatchEvent])}
            />
          ) : (
            <div className="play-gate">
              <div className="pg-emoji">🎮</div>
              <div className="pg-title">{homeNation} vs {awayNation}</div>
              <p className="muted">This fixture hasn’t been played yet. Conduct it live — the AI
                coaches will pick tactics and substitutions, and the result is recorded.</p>
              <button className="big" onClick={() => setStarted(true)}>▶ Conduct match — live</button>
            </div>
          )}
        </div>
        <MatchCommentary
          events={commentaryEvents} clock={clock}
          homeNation={homeNation} awayNation={awayNation} live={!isPlayed && started}
        />
      </div>

      {isPlayed && (
        <div className="card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>🤖 AI match summary</h3>
            <button className="ghost" onClick={() => setShowC(true)} disabled={showC}>
              {com.isFetching ? <><span className="spinner" />Thinking…</> : "Generate"}
            </button>
          </div>
          {com.data?.commentary && <p className="commentary" style={{ marginTop: 12 }}>“{com.data.commentary}”</p>}
        </div>
      )}

      <h2>Timeline</h2>
      {timeline.length === 0 ? (
        <p className="muted">{isPlayed ? "No key events recorded." : "Play the match to see the timeline."}</p>
      ) : (
        <ul className="timeline">
          {timeline.map((e, i) => (
            <li key={i} className={e.type}>
              <span className="min">{Math.round(e.t)}'</span>
              <span className="ic">{EV_IC[e.type] ?? "•"}</span>
              <span className="ev">{e.type.replace(/_/g, " ")}</span>
              {e.team ? <span className="muted">· {e.team}</span> : null}
            </li>
          ))}
        </ul>
      )}

      {isPlayed && <CoachReport mid={mid} homeNation={homeNation} awayNation={awayNation} />}
    </section>
  );
}
