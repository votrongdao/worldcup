import type { PlayerDetail } from "../../api/types";

const AXES: [keyof PlayerDetail, string][] = [
  ["pace", "PAC"], ["shooting", "SHO"], ["passing", "PAS"],
  ["dribbling", "DRI"], ["defending", "DEF"], ["vision", "VIS"],
];

const CX = 90, CY = 92, R = 64;

function point(i: number, scale: number): [number, number] {
  const ang = -Math.PI / 2 + (i * 2 * Math.PI) / AXES.length;
  return [CX + Math.cos(ang) * R * scale, CY + Math.sin(ang) * R * scale];
}

export function PlayerRadar({ player }: { player: PlayerDetail }) {
  const grid = AXES.map((_, i) => point(i, 1).join(",")).join(" ");
  const shape = AXES.map(([k], i) => point(i, player[k] as number).join(",")).join(" ");
  return (
    <svg className="radar" width={180} height={184} viewBox="0 0 180 184">
      <polygon points={grid} fill="none" stroke="#dfe6df" />
      <polygon points={AXES.map((_, i) => point(i, 0.5).join(",")).join(" ")} fill="none" stroke="#eef3ee" />
      <polygon points={shape} fill="rgba(43,182,115,0.28)" stroke="#2bb673" strokeWidth={2} />
      {AXES.map(([k, label], i) => {
        const [lx, ly] = point(i, 1.18);
        return (
          <text key={k} x={lx} y={ly} fontSize="9" textAnchor="middle"
            dominantBaseline="middle" fill="#6b756b">{label}</text>
        );
      })}
    </svg>
  );
}
