import type { PlayerDetail } from "../../api/types";

const ATTRS: [keyof PlayerDetail, string][] = [
  ["pace", "PAC"], ["shooting", "SHO"], ["passing", "PAS"],
  ["dribbling", "DRI"], ["defending", "DEF"], ["stamina", "STA"],
];

function rate(v: number) {
  const n = Math.round(v * 99);
  const color = n >= 80 ? "#16a34a" : n >= 65 ? "#3a3a4d" : "#9aa0b8";
  return <span style={{ color, fontWeight: n >= 80 ? 700 : 500 }}>{n}</span>;
}

export function SquadTable({ squad, xi }: { squad: PlayerDetail[]; xi: string[] }) {
  const inXi = new Set(xi);
  return (
    <table className="squad">
      <thead>
        <tr>
          <th style={{ width: 34 }}>#</th><th>Pos</th>
          {ATTRS.map(([k, l]) => <th key={k} className="num">{l}</th>)}
        </tr>
      </thead>
      <tbody>
        {squad.map((p, i) => (
          <tr key={p.id} className={inXi.has(p.id) ? "in-xi" : undefined}>
            <td>{i + 1}{inXi.has(p.id) ? <span className="xi-dot"> ●</span> : ""}</td>
            <td><span className={`pos ${p.role}`}>{p.role}</span></td>
            {ATTRS.map(([k]) => (
              <td key={k} className="num">{rate(p[k] as number)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
