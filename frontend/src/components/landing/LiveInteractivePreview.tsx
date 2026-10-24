"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

export function LiveInteractivePreview() {
  const [activeScenario, setActiveScenario] = useState<"pressure" | "goal" | "quiet">("pressure");

  const scenarios = {
    pressure: {
      title: "Pressure Surge (+41.0 Δ)",
      clock: "72:14",
      score: "1 - 0",
      headline: "Ridge United surge – pressure index spikes",
      why: "Ridge United generated 8 consecutive attacking-third entries and 3 high regains in 300 seconds.",
      metric: "72.0 / 100 Pressure Index",
      badge: "VERIFIED BY AUDITOR",
      color: "var(--pitch-emerald)",
    },
    goal: {
      title: "Goal Sequence",
      clock: "84:30",
      score: "2 - 0",
      headline: "GOAL! Ridge United find the net",
      why: "The scoreline changed following a penalty box penetration at minute 84.",
      metric: "Score Updated: 2 - 0",
      badge: "VERIFIED SCORELINE",
      color: "var(--pl-purple)",
    },
    quiet: {
      title: "Quiet Midfield Play",
      clock: "34:10",
      score: "0 - 0",
      headline: "No significant moment detected",
      why: "Routine passes in the middle third remain below threshold. The system deliberately suppresses output.",
      metric: "18.0 / 100 Stable Intensity",
      badge: "RESTRAINT MAINTAINED",
      color: "var(--ink-muted)",
    },
  };

  const current = scenarios[activeScenario];

  return (
    <section style={{ maxWidth: "1380px", margin: "80px auto", padding: "0 24px" }}>
      <div style={{ background: "linear-gradient(135deg, rgba(56,0,60,0.03) 0%, rgba(5,150,105,0.03) 100%)", border: "1px solid var(--line)", borderRadius: "24px", padding: "48px 36px", boxShadow: "var(--shadow-sm)" }}>
        <div style={{ textAlign: "center", marginBottom: "36px" }}>
          <div className="section-eyebrow">Interactive Live Simulator</div>
          <h2 style={{ fontSize: "36px", fontWeight: 900, color: "var(--pl-purple)", letterSpacing: "-0.04em" }}>
            Experience the Intelligence Pipeline Live
          </h2>
          <p style={{ color: "var(--ink-secondary)", fontSize: "16px", marginTop: "8px" }}>
            Click a scenario below to see how MatchPulse detects, audits, and presents moments in real time.
          </p>

          <div style={{ display: "inline-flex", background: "var(--surface-subtle)", padding: "4px", borderRadius: "12px", marginTop: "24px", gap: "6px" }}>
            {(["pressure", "goal", "quiet"] as const).map((key) => (
              <button
                key={key}
                onClick={() => setActiveScenario(key)}
                style={{
                  padding: "10px 20px",
                  fontSize: "14px",
                  fontWeight: 800,
                  border: "none",
                  borderRadius: "9px",
                  cursor: "pointer",
                  background: activeScenario === key ? "#ffffff" : "transparent",
                  color: activeScenario === key ? "var(--pl-purple)" : "var(--ink-secondary)",
                  boxShadow: activeScenario === key ? "var(--shadow-sm)" : "none",
                  transition: "all 0.15s ease",
                }}
              >
                {scenarios[key].title}
              </button>
            ))}
          </div>
        </div>

        {/* Live Simulation Box */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeScenario}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.25 }}
            style={{
              background: "#ffffff",
              border: "1px solid var(--line)",
              borderRadius: "18px",
              padding: "32px",
              boxShadow: "var(--shadow-lg)",
              maxWidth: "960px",
              margin: "0 auto",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px", paddingBottom: "20px", borderBottom: "1px solid var(--line)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span className="live-pill">
                  <span className="live-blip" />
                  <span>SIMULATED FEED</span>
                </span>
                <span style={{ fontSize: "14px", fontWeight: 700, color: "var(--ink-secondary)" }}>
                  Ridge United vs Harbor FC
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <span className="match-timer">⏱️ {current.clock}</span>
                <span style={{ fontSize: "22px", fontWeight: 900, color: "var(--pl-purple)" }}>{current.score}</span>
              </div>
            </div>

            <div style={{ marginTop: "24px", display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: "32px" }}>
              <div>
                <span style={{ fontSize: "11px", fontWeight: 800, color: current.color, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                  {current.badge}
                </span>
                <h3 style={{ fontSize: "24px", fontWeight: 900, color: "var(--pl-purple)", marginTop: "6px", marginBottom: "12px", letterSpacing: "-0.03em" }}>
                  {current.headline}
                </h3>
                <p style={{ fontSize: "15px", lineHeight: "1.6", color: "var(--ink-secondary)" }}>
                  {current.why}
                </p>
              </div>

              <div style={{ background: "var(--surface-subtle)", borderRadius: "14px", padding: "20px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontSize: "12px", fontWeight: 700, color: "var(--ink-muted)", textTransform: "uppercase" }}>Deterministic Metric</div>
                  <div style={{ fontSize: "20px", fontWeight: 900, color: "var(--pl-purple)", marginTop: "4px" }}>{current.metric}</div>
                </div>

                <Link href="/dashboard" className="btn-primary" style={{ marginTop: "20px", width: "100%", textAlign: "center" }}>
                  View In Full Match Console →
                </Link>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
