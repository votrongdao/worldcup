// Deterministic team-colour theming. The lists/groups/bracket only carry a
// nation *name*, so we derive a stable, vibrant gradient + initials from it —
// every screen shows the same colour for the same team (FIFA-style team hues).

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export interface TeamColors {
  c1: string; // primary
  c2: string; // secondary (gradient end)
  hue: number;
}

/** Stable, well-saturated two-colour gradient for a team name. */
export function teamColors(name: string | null | undefined): TeamColors {
  const h = hash(name || "—");
  const hue = h % 360;
  const hue2 = (hue + 28 + (h % 40)) % 360;
  return {
    c1: `hsl(${hue} 70% 48%)`,
    c2: `hsl(${hue2} 74% 56%)`,
    hue,
  };
}

/** 2–3 letter monogram from a nation name ("Côte d'Azuria" -> "CA"). */
export function initials(name: string | null | undefined): string {
  if (!name) return "—";
  const words = name.replace(/[^\p{L}\s]/gu, " ").split(/\s+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  const w = words[0] ?? name;
  return w.slice(0, 3).toUpperCase();
}
