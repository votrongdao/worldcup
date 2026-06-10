import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useCreateTournament } from "../hooks/useCreateTournament";
import { randomSeed } from "../lib/seed";

export function Dashboard() {
  const [seed, setSeed] = useState(randomSeed());
  const create = useCreateTournament();
  const navigate = useNavigate();

  const start = () =>
    create.mutate(
      {
        format: "world_cup_32", teams: 32, groups: 8, perGroup: 4,
        advancePerGroup: 2, thirdPlace: true, seed,
      },
      { onSuccess: (res) => navigate({ to: "/tournaments/$id", params: { id: res.id } }) },
    );

  return (
    <section>
      <h1>New World Cup</h1>
      <p className="muted">
        Generate 32 AI nations, draw groups, and simulate the whole tournament
        deterministically from a single seed.
      </p>
      <div className="card row">
        <label>
          Seed{" "}
          <input
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            style={{ width: 160 }}
          />
        </label>
        <button onClick={() => setSeed(randomSeed())} className="ghost">Random</button>
        <button onClick={start} disabled={create.isPending}>
          {create.isPending ? "Starting…" : "Start tournament"}
        </button>
      </div>
      {create.isError && <p className="muted">Failed to start — is the API running?</p>}
    </section>
  );
}
