"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";

export function HeroSection() {
  const { scrollY } = useScroll();
  const ballY = useTransform(scrollY, [0, 600], [0, 140]);
  const ballRotate = useTransform(scrollY, [0, 600], [0, 45]);
  const glowOpacity = useTransform(scrollY, [0, 400], [1, 0.3]);

  return (
    <section className="hero-backdrop">
      {/* Ambient Stadium Lighting Canopy */}
      <div className="hero-stadium-canopy" aria-hidden="true">
        <div className="floodlight-beam beam-left" style={{ opacity: 0.45 }} />
        <div className="floodlight-beam beam-right" style={{ opacity: 0.45 }} />
        <svg className="hero-stadium-svg" viewBox="0 0 1200 600" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Subtle Stadium Bowl Architecture Outline */}
          <path d="M50 550 C 300 480, 900 480, 1150 550" stroke="rgba(56, 0, 60, 0.08)" strokeWidth="3" />
          <path d="M150 510 C 350 450, 850 450, 1050 510" stroke="rgba(5, 150, 105, 0.08)" strokeWidth="2" />
          <path d="M250 470 C 420 420, 780 420, 950 470" stroke="rgba(56, 0, 60, 0.06)" strokeWidth="1.5" />
          {/* Floodlight Rig Silhouettes */}
          <line x1="80" y1="120" x2="200" y2="480" stroke="rgba(5, 150, 105, 0.12)" strokeWidth="1" strokeDasharray="4 4" />
          <line x1="1120" y1="120" x2="1000" y2="480" stroke="rgba(56, 0, 60, 0.12)" strokeWidth="1" strokeDasharray="4 4" />
          <circle cx="80" cy="120" r="16" fill="rgba(5, 150, 105, 0.15)" />
          <circle cx="1120" cy="120" r="16" fill="rgba(56, 0, 60, 0.15)" />
        </svg>
      </div>

      {/* Left: Content */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className="hero-badge-pill">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
          </svg>
          <span>Microsoft × Premier League · Inside the Game</span>
        </div>

        <h1 className="hero-headline">
          Every Play Measured. <span>Every Claim Verified.</span>
        </h1>

        <p className="hero-subtitle">
          The evidence-first multi-agent football intelligence platform. Transforms live match events into explainable narratives with zero fabricated statistics.
        </p>

        <div className="hero-cta-group">
          <Link href="/dashboard" className="btn-primary" style={{ padding: "14px 28px", fontSize: "16px" }}>
            <span>Launch Live Console</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </Link>

          <Link href="/match/sim_match_001/analysis" className="btn-secondary" style={{ padding: "14px 24px", fontSize: "16px" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
            <span>2D Tactical Field Radar</span>
          </Link>
        </div>
      </motion.div>

      {/* Right: Authentic Animated Football Visual */}
      <div className="ball-stage">
        <motion.div style={{ opacity: glowOpacity }} className="pitch-graphic-ring" />

        {/* Floating Telemetry Badge 1 */}
        <motion.div
          className="floating-telemetry-card card-pos-1"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--pitch-emerald)" }} />
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>Pressure-v1 Delta</div>
            <div style={{ fontSize: "15px", fontWeight: 900, color: "var(--pl-purple)" }}>+41.0 Intensity Spike</div>
          </div>
        </motion.div>

        {/* Floating Telemetry Badge 2 */}
        <motion.div
          className="floating-telemetry-card card-pos-2"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
        >
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "var(--accent-crimson)" }} />
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>Evidence Auditor</div>
            <div style={{ fontSize: "15px", fontWeight: 900, color: "var(--pitch-emerald)" }}>100% Fact Checked</div>
          </div>
        </motion.div>

        {/* Floating Telemetry Badge 3 */}
        <motion.div
          className="floating-telemetry-card card-pos-3"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
        >
          <div style={{ fontSize: "18px" }}>⚡</div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>Latency</div>
            <div style={{ fontSize: "15px", fontWeight: 900, color: "var(--pl-purple)" }}>0.88ms Real-Time</div>
          </div>
        </motion.div>

        {/* 3D Styled SVG Football */}
        <motion.div
          style={{ y: ballY, rotate: ballRotate }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <svg width="280" height="280" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ filter: "drop-shadow(0 25px 35px rgba(56, 0, 60, 0.25))" }}>
            <circle cx="100" cy="100" r="95" fill="url(#ballShading)" stroke="#CBD5E1" strokeWidth="3" />
            <polygon points="100,60 125,78 115,108 85,108 75,78" fill="#1E293B" />
            <polygon points="100,20 115,38 95,50 75,38 85,20" fill="#334155" />
            <polygon points="155,50 170,70 150,85 130,70 140,50" fill="#334155" />
            <polygon points="150,135 170,145 155,165 135,155 135,135" fill="#334155" />
            <polygon points="65,155 45,165 30,145 50,135 55,145" fill="#334155" />
            <polygon points="30,70 45,50 60,70 50,85 30,85" fill="#334155" />
            <line x1="100" y1="60" x2="95" y2="50" stroke="#64748B" strokeWidth="2.5" />
            <line x1="125" y1="78" x2="130" y2="70" stroke="#64748B" strokeWidth="2.5" />
            <line x1="115" y1="108" x2="135" y2="135" stroke="#64748B" strokeWidth="2.5" />
            <line x1="85" y1="108" x2="55" y2="145" stroke="#64748B" strokeWidth="2.5" />
            <line x1="75" y1="78" x2="50" y2="85" stroke="#64748B" strokeWidth="2.5" />
            <defs>
              <radialGradient id="ballShading" cx="30%" cy="30%" r="70%">
                <stop offset="0%" stopColor="#FFFFFF" />
                <stop offset="70%" stopColor="#F1F5F9" />
                <stop offset="100%" stopColor="#CBD5E1" />
              </radialGradient>
            </defs>
          </svg>
        </motion.div>
      </div>
    </section>
  );
}
