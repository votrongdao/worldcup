// TanStack Router route tree, declared programmatically and attached to the root.
import { createRouter, createRoute, createRootRoute } from "@tanstack/react-router";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./routes/index";
import { TournamentOverview } from "./routes/tournaments.$id";
import { GroupsPage } from "./routes/tournaments.$id.groups";
import { BracketPage } from "./routes/tournaments.$id.bracket";
import { MatchesPage } from "./routes/tournaments.$id.matches";
import { MatchDetail } from "./routes/tournaments.$id.matches.$mid";
import { TeamsPage } from "./routes/tournaments.$id.teams";
import { TeamDetail } from "./routes/tournaments.$id.teams.$teamId";

const rootRoute = createRootRoute({ component: AppShell });

const r = (path: string, component: () => JSX.Element) =>
  createRoute({ getParentRoute: () => rootRoute, path, component });

const routeTree = rootRoute.addChildren([
  r("/", Dashboard),
  r("tournaments/$id", TournamentOverview),
  r("tournaments/$id/groups", GroupsPage),
  r("tournaments/$id/bracket", BracketPage),
  r("tournaments/$id/matches", MatchesPage),
  r("tournaments/$id/matches/$mid", MatchDetail),
  r("tournaments/$id/teams", TeamsPage),
  r("tournaments/$id/teams/$teamId", TeamDetail),
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register { router: typeof router; }
}
