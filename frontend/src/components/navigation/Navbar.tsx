"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

export function Navbar() {
  const pathname = usePathname();
  const [matchId, setMatchId] = useState("sim_match_001");

  return (
    <header className="top-navbar">
      <div className="nav-container">
        {/* Brand */}
        <Link href="/" className="brand-link">
          <div className="brand-crest">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#00FF87" />
            </svg>
          </div>
          <div>
            <div className="brand-title">MATCHPULSE</div>
            <div className="brand-sub">Premier League × Microsoft</div>
          </div>
        </Link>

        {/* Navigation Links */}
        <nav className="nav-links">
          <Link href="/" className={`nav-item ${pathname === "/" || pathname === "/welcome" ? "active" : ""}`}>
            Overview
          </Link>
          <Link href="/dashboard" className={`nav-item ${pathname === "/dashboard" ? "active" : ""}`}>
            Live Console
          </Link>
          <Link href={`/match/${matchId}/analysis`} className={`nav-item ${pathname.includes("/analysis") ? "active" : ""}`}>
            2D Pitch Radar
          </Link>
        </nav>

        {/* Status & Auth Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div className="live-pill">
            <span className="live-blip" />
            <span>Live Engine</span>
          </div>

          <Link href="/login" className="btn-secondary" style={{ padding: "8px 14px", fontSize: "13px" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
            <span>Sign In</span>
          </Link>

          <Link href="/dashboard" className="btn-primary" style={{ padding: "8px 16px", fontSize: "13px" }}>
            Launch Console
          </Link>
        </div>
      </div>
    </header>
  );
}
