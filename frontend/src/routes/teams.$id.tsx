import { SquadTable } from "../components/team/SquadTable";
import { CoachCard } from "../components/team/CoachCard";
export function TeamPage({ id }: { id: string }) {
  return <><CoachCard teamId={id} /><SquadTable teamId={id} /></>;
}
