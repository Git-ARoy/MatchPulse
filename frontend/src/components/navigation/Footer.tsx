import Link from "next/link";

export function Footer() {
  return (
    <footer style={{ background: "#ffffff", borderTop: "1px solid var(--line)", padding: "40px 24px", marginTop: "auto" }}>
      <div style={{ maxWidth: "1380px", margin: "0 auto", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "20px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontWeight: 900, color: "var(--pl-purple)", letterSpacing: "-0.03em" }}>MATCHPULSE</span>
            <span style={{ fontSize: "12px", color: "var(--ink-muted)" }}>• Evidence-First Football Intelligence</span>
          </div>
          <p style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "6px" }}>
            Developed for the Microsoft × Premier League <em>Inside the Game: Developer Hackathon</em>.
          </p>
          <p style={{ fontSize: "11px", color: "var(--ink-dim)", marginTop: "4px" }}>
            MatchPulse Pressure Index (pressure-v1) is a project-defined metric, not an official Premier League statistic.
          </p>
        </div>

        <div style={{ display: "flex", gap: "24px", fontSize: "13px", fontWeight: 600 }}>
          <Link href="/" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Overview</Link>
          <Link href="/dashboard" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Dashboard</Link>
          <Link href="/match/sim_match_001/analysis" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Tactical Radar</Link>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" style={{ color: "var(--pitch-emerald)", textDecoration: "none" }}>API Docs ↗</a>
        </div>
      </div>
    </footer>
  );
}
