import { useState } from "react";
import { flagCode, flagUrl } from "../../lib/flags";
import { initials } from "../../lib/colors";

type Size = "sm" | "md" | "lg";

/** Real country flag for a team, with an initials chip fallback for unknown
 *  / generated nations or if the image fails to load. Named TeamBadge for
 *  backwards-compatibility across the app. */
export function TeamBadge({ name, size = "md" }: { name: string | null | undefined; size?: Size }) {
  const code = flagCode(name);
  const [broken, setBroken] = useState(false);
  const cls = size === "lg" ? "flag lg" : size === "sm" ? "flag sm" : "flag";

  if (!code || broken) {
    return <span className={`${cls} flag-fallback`} aria-hidden>{initials(name)}</span>;
  }
  return (
    <img
      className={cls}
      src={flagUrl(code)}
      alt={name ? `${name} flag` : ""}
      loading="lazy"
      onError={() => setBroken(true)}
    />
  );
}

/** Flag + name, the common inline pairing. */
export function TeamCell({
  name,
  size = "sm",
  className = "",
}: {
  name: string | null | undefined;
  size?: Size;
  className?: string;
}) {
  return (
    <span className={`team-cell ${className}`}>
      <TeamBadge name={name} size={size} />
      <span className="name">{name ?? "—"}</span>
    </span>
  );
}
