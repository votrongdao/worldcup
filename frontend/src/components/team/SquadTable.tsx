import type { PlayerDetail } from "../../api/types";

const ATTRS: [keyof PlayerDetail, string][] = [
  ["pace", "PAC"], ["shooting", "SHO"], ["passing", "PAS"],
  ["dribbling", "DRI"], ["defending", "DEF"], ["stamina", "STA"],
];

export function SquadTable({ squad, xi }: { squad: PlayerDetail[]; xi: string[] }) {
  const inXi = new Set(xi);
  return (
    <table className="squad">
      <thead>
        <tr>
          <th>#</th><th>Pos</th>
          {ATTRS.map(([k, l]) => <th key={k} className="num">{l}</th>)}
        </tr>
      </thead>
      <tbody>
        {squad.map((p, i) => (
          <tr key={p.id} className={inXi.has(p.id) ? "in-xi" : undefined}>
            <td>{i + 1}{inXi.has(p.id) ? " ●" : ""}</td>
            <td>{p.role}</td>
            {ATTRS.map(([k]) => (
              <td key={k} className="num">{Math.round((p[k] as number) * 99)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
