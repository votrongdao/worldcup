import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useCreateTournament } from "../hooks/useCreateTournament";
import { randomSeed } from "../lib/seed";

const STEPS = [
  { ic: "🌍", t: "32 AI nations", d: "Generated with squads, coaches & tactical DNA" },
  { ic: "🎲", t: "Group draw", d: "Eight groups, seeded from your master seed" },
  { ic: "⚽", t: "Live matches", d: "Deterministic 2D physics, watch or replay" },
  { ic: "🏆", t: "One champion", d: "Round-robin → knockout → glory" },
];

export function Dashboard() {
  const [seed, setSeed] = useState(randomSeed());
  const [selfPlay, setSelfPlay] = useState(false);
  const create = useCreateTournament();
  const navigate = useNavigate();

  const start = () =>
    create.mutate(
      {
        format: "world_cup_32", teams: 32, groups: 8, perGroup: 4,
        advancePerGroup: 2, thirdPlace: true, seed, autoPlay: !selfPlay,
      },
      { onSuccess: (res) => navigate({ to: "/tournaments/$id", params: { id: res.id } }) },
    );

  return (
    <section>
      <div className="hero">
        <span className="ball-bg">⚽</span>
        <span className="eyebrow">⚡ Deterministic · Reproducible · Agentic</span>
        <h1>Kick off a new World Cup</h1>
        <p className="sub">
          Generate 32 AI nations, draw the groups, and simulate an entire
          tournament — fully deterministic from a single master seed. Same seed,
          same World Cup, every time.
        </p>
      </div>

      <div className="card">
        <h3>Master seed</h3>
        <div className="row" style={{ justifyContent: "space-between" }}>
          <div className="row">
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              style={{ width: 200, fontFamily: "ui-monospace, monospace", fontWeight: 600 }}
            />
            <button onClick={() => setSeed(randomSeed())} className="ghost">🎲 Random</button>
          </div>
          <button onClick={start} disabled={create.isPending} className="big">
            {create.isPending ? <><span className="spinner" />Starting…</> : "Start tournament →"}
          </button>
        </div>
        <label className="selfplay-toggle">
          <input type="checkbox" checked={selfPlay} onChange={(e) => setSelfPlay(e.target.checked)} />
          <span>🎮 <strong>Self-play</strong> — schedule the fixtures and conduct each match
            yourself (live), instead of auto-simulating the whole tournament.</span>
        </label>
        {create.isError && (
          <p className="muted" style={{ marginBottom: 0, color: "var(--away)" }}>
            ⚠ Failed to start — is the API running?
          </p>
        )}
      </div>

      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))" }}>
        {STEPS.map((s, i) => (
          <div className="card hoverable" key={i} style={{ margin: 0 }}>
            <div style={{ fontSize: "1.7rem", marginBottom: 6 }}>{s.ic}</div>
            <div style={{ fontWeight: 700, fontFamily: "Sora, sans-serif" }}>{s.t}</div>
            <div className="muted" style={{ marginTop: 2 }}>{s.d}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
