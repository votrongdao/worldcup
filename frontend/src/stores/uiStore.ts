// Minimal local UI state (selected entities, theme). Swap for TanStack Store/Zustand.
import { useState } from "react";
export const useUiStore = () => {
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null);
  return { selectedMatch, setSelectedMatch };
};
