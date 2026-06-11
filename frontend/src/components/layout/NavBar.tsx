import { Link } from "@tanstack/react-router";

export function NavBar() {
  return (
    <nav className="navbar">
      <Link to="/" className="brand">
        <span className="ball">⚽</span>
        <span>
          AI Agentic <span className="grad-text">World Cup</span>
        </span>
      </Link>
      <span className="spacer" />
      <Link to="/" className="pill-link">+ New tournament</Link>
    </nav>
  );
}
