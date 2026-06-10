// TanStack Router route tree, declared programmatically and attached to the root.
import { createRouter, createRoute, createRootRoute } from "@tanstack/react-router";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./routes/index";
import { TournamentOverview } from "./routes/tournaments.$id";
import { GroupsPage } from "./routes/tournaments.$id.groups";
import { BracketPage } from "./routes/tournaments.$id.bracket";
import { MatchesPage } from "./routes/tournaments.$id.matches";

const rootRoute = createRootRoute({ component: AppShell });

const indexRoute = createRoute({
  getParentRoute: () => rootRoute, path: "/", component: Dashboard,
});
const overviewRoute = createRoute({
  getParentRoute: () => rootRoute, path: "tournaments/$id", component: TournamentOverview,
});
const groupsRoute = createRoute({
  getParentRoute: () => rootRoute, path: "tournaments/$id/groups", component: GroupsPage,
});
const bracketRoute = createRoute({
  getParentRoute: () => rootRoute, path: "tournaments/$id/bracket", component: BracketPage,
});
const matchesRoute = createRoute({
  getParentRoute: () => rootRoute, path: "tournaments/$id/matches", component: MatchesPage,
});

const routeTree = rootRoute.addChildren([
  indexRoute, overviewRoute, groupsRoute, bracketRoute, matchesRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register { router: typeof router; }
}
