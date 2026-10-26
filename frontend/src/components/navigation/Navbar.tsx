"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChartMultipleRegular, PersonRegular, PulseRegular } from "@fluentui/react-icons";

const demoMatch = "synthetic_ridge_harbor";

export function Navbar() {
  const pathname = usePathname();
  return <header className="top-navbar"><div className="nav-container">
    <Link href="/" className="brand-link"><span className="brand-mark"><PulseRegular /></span><span><strong>MATCHPULSE</strong><small>Football intelligence studio</small></span></Link>
    <nav className="nav-links" aria-label="Primary navigation"><Link href="/" className={pathname === "/" ? "active" : ""}>Overview</Link><Link href="/dashboard" className={pathname === "/dashboard" ? "active" : ""}>Live demo</Link><Link href={`/match/${demoMatch}/analysis`} className={pathname.includes("/analysis") ? "active" : ""}>Tactical radar</Link></nav>
    <div className="nav-actions"><span className="engine-status"><span className="semantic-live-dot" />Synthetic pipeline</span><Link href="/login" className="nav-login"><PersonRegular />Sign in</Link><Link href="/dashboard" className="nav-launch"><ChartMultipleRegular />Open studio</Link></div>
  </div></header>;
}
