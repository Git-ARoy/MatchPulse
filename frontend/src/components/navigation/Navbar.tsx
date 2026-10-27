"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { ChartMultipleRegular, PersonRegular, PulseRegular } from "@fluentui/react-icons";

const demoMatch = "synthetic_ridge_harbor";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Close mobile drawer whenever route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Prevent background scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  return (
    <header className="top-navbar">
      <div className="nav-container">
        <Link href="/" className="brand-link" aria-label="MatchPulse Home">
          <span className="brand-crest">
            <PulseRegular />
          </span>
          <span className="brand-text">
            <strong className="brand-title">MATCHPULSE</strong>
            <small className="brand-sub">Football intelligence studio</small>
          </span>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="nav-links" aria-label="Primary navigation">
          <Link href="/" className={`nav-item ${pathname === "/" ? "active" : ""}`}>
            Overview
          </Link>
          <Link href="/dashboard" className={`nav-item ${pathname === "/dashboard" ? "active" : ""}`}>
            Live demo
          </Link>
          <Link
            href={`/match/${demoMatch}/analysis`}
            className={`nav-item ${pathname.includes("/analysis") ? "active" : ""}`}
          >
            Tactical radar
          </Link>
        </nav>

        {/* Desktop Actions */}
        <div className="nav-actions">
          <span className="engine-status">
            <span className="semantic-live-dot" />
            Synthetic pipeline
          </span>
          <Link href="/login" className="nav-login">
            <PersonRegular />
            Sign in
          </Link>
          <Link href="/dashboard" className="nav-launch">
            <ChartMultipleRegular />
            Open studio
          </Link>
        </div>

        {/* Mobile Menu Toggle Button */}
        <button
          type="button"
          className="mobile-menu-btn"
          aria-expanded={mobileMenuOpen}
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          onClick={() => setMobileMenuOpen((prev) => !prev)}
        >
          {mobileMenuOpen ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" y1="7" x2="20" y2="7" />
              <line x1="4" y1="12" x2="20" y2="12" />
              <line x1="4" y1="17" x2="20" y2="17" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile Menu Drawer Overlay */}
      {mobileMenuOpen && (
        <div className="mobile-nav-backdrop" onClick={() => setMobileMenuOpen(false)}>
          <div
            className="mobile-nav-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Mobile Navigation"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mobile-nav-status">
              <span className="semantic-live-dot" />
              <span>Synthetic Pipeline Active (Azure)</span>
            </div>

            <nav className="mobile-nav-links" aria-label="Mobile primary navigation">
              <Link
                href="/"
                className={`mobile-nav-item ${pathname === "/" ? "active" : ""}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                <span>🏠</span>
                <span>Overview</span>
              </Link>
              <Link
                href="/dashboard"
                className={`mobile-nav-item ${pathname === "/dashboard" ? "active" : ""}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                <span>⚡</span>
                <span>Live Studio Demo</span>
              </Link>
              <Link
                href={`/match/${demoMatch}/analysis`}
                className={`mobile-nav-item ${pathname.includes("/analysis") ? "active" : ""}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                <span>🎯</span>
                <span>Tactical Event Radar</span>
              </Link>
            </nav>

            <div className="mobile-nav-footer">
              <Link
                href="/login"
                className="mobile-login-btn"
                onClick={() => setMobileMenuOpen(false)}
              >
                <PersonRegular />
                <span>Sign in</span>
              </Link>
              <Link
                href="/dashboard"
                className="mobile-launch-btn"
                onClick={() => setMobileMenuOpen(false)}
              >
                <ChartMultipleRegular />
                <span>Open Studio</span>
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
