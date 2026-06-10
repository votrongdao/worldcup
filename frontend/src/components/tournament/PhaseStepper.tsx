import type { Phase } from "../../api/types";
const ORDER: Phase[] = ["generating","draw","group","r16","qf","sf","final","done"];
export function PhaseStepper({ phase }: { phase: Phase }) {
  return <ol>{ORDER.map((p) => <li key={p} className={p === phase ? "active" : ""}>{p}</li>)}</ol>;
}
