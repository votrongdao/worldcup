import { Outlet } from "@tanstack/react-router";
import { NavBar } from "./NavBar";
export function AppShell() { return <div><NavBar /><main><Outlet /></main></div>; }
