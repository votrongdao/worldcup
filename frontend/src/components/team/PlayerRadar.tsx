import type { PlayerDetail } from "../../api/types";

const AXES: [keyof PlayerDetail, string][] = [
  ["pace", "PAC"], ["shooting", "SHO"], ["passing", "PAS"],
  ["dribbling", "DRI"], ["defending", "DEF"], ["vision", "VIS"],
];

const CX = 90, CY = 92, R = 64;
const BLUE = "#0071e3";

function point(i: number, scale: number): [number, number] {
  const ang = -Math.PI / 2 + (i * 2 * Math.PI) / AXES.length;
  return [CX + Math.cos(ang) * R * scale, CY + Math.sin(ang) * R * scale];
}

export function PlayerRadar({ player }: { player: PlayerDetail }) {
  const grid = AXES.map((_, i) => point(i, 1).join(",")).join(" ");
  const shape = AXES.map(([k], i) => point(i, player[k] as number).join(",")).join(" ");
  return (
    <svg className="radar" width={180} height={184} viewBox="0 0 180 184">
      <polygon points={grid} fill="none" stroke="#d2d2d7" />
      <polygon points={AXES.map((_, i) => point(i, 0.66).join(",")).join(" ")} fill="none" stroke="#ececef" />
      <polygon points={AXES.map((_, i) => point(i, 0.33).join(",")).join(" ")} fill="none" stroke="#ececef" />
      {AXES.map((_, i) => {
        const [x, y] = point(i, 1);
        return <line key={i} x1={CX} y1={CY} x2={x} y2={y} stroke="#ececef" />;
      })}
      <polygon points={shape} fill={BLUE} fillOpacity={0.18} stroke={BLUE} strokeWidth={2} strokeLinejoin="round" />
      {AXES.map(([k, label], i) => {
        const [lx, ly] = point(i, 1.2);
        return (
          <text key={k} x={lx} y={ly} fontSize="9" fontWeight="600" textAnchor="middle"
            dominantBaseline="middle" fill="#6e6e73">{label}</text>
        );
      })}
    </svg>
  );
}
