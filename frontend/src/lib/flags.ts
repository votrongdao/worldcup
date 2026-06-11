// Map the generated nation names (real countries) to ISO 3166-1 alpha-2 codes
// so we can show real flag images. Windows does not render flag *emoji* as
// flags, so we use flag images (flagcdn) with an initials fallback.

const ISO: Record<string, string> = {
  Brazil: "br", Argentina: "ar", France: "fr", Germany: "de", Spain: "es",
  England: "gb-eng", Italy: "it", Netherlands: "nl", Portugal: "pt", Belgium: "be",
  Croatia: "hr", Uruguay: "uy", Mexico: "mx", Colombia: "co", Denmark: "dk",
  Switzerland: "ch", "United States": "us", Japan: "jp", Senegal: "sn", Morocco: "ma",
  Poland: "pl", Serbia: "rs", "South Korea": "kr", Australia: "au", Canada: "ca",
  Ghana: "gh", Ecuador: "ec", Cameroon: "cm", Tunisia: "tn", Nigeria: "ng",
  Wales: "gb-wls", Qatar: "qa", Sweden: "se", Norway: "no", Austria: "at",
  Turkey: "tr", Egypt: "eg", Chile: "cl", Peru: "pe", Iran: "ir",
  "Ivory Coast": "ci", Algeria: "dz", Scotland: "gb-sct", Greece: "gr",
  Czechia: "cz", Ukraine: "ua", "Costa Rica": "cr", Paraguay: "py",
};

/** ISO code for a nation name, or null for generated "Nation NN" fallbacks. */
export function flagCode(name: string | null | undefined): string | null {
  if (!name) return null;
  return ISO[name] ?? null;
}

/** flagcdn SVG URL for a code (sharp at any size). */
export function flagUrl(code: string): string {
  return `https://flagcdn.com/${code}.svg`;
}
