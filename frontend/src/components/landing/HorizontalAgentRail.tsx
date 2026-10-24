"use client";

import { motion } from "framer-motion";

const agents = [
  {
    num: "01",
    role: "Match Analyst",
    icon: "📊",
    headline: "Statistical Momentum & Shift Detection",
    description: "Evaluates rolling 5-minute event windows and computes deterministic deltas. Never estimates numbers with an LLM.",
    spec: "Pressure-v1 composite index • Attacking-third metrics",
    color: "var(--accent-blue)",
  },
  {
    num: "02",
    role: "Tactical Analyst",
    icon: "🧭",
    headline: "Territorial Patterns & Transition Hypotheses",
    description: "Investigates pitch territory, possession sequence lengths, and transition phases. Separates observed facts from interpretations.",
    spec: "Zone classification • High-regain tracking • Ball retention",
    color: "var(--pitch-emerald)",
  },
  {
    num: "03",
    role: "Narrative Producer",
    icon: "🎙️",
    headline: "Multi-Audience Story Adaptation",
    description: "Derives distinct Fan, Analyst, and Broadcast narratives from the exact same locked evidence snapshot without introducing new claims.",
    spec: "Fan emotion • Analyst metrics • Broadcast overlay format",
    color: "var(--pl-purple)",
  },
  {
    num: "04",
    role: "Evidence Auditor",
    icon: "🛡️",
    headline: "Deterministic Factual Validation & Repair",
    description: "Checks cited event IDs, verifies exact metric deltas, and validates time boundaries. Rejects any ungrounded hallucination.",
    spec: "1-turn bounded repair • Citation check • Ledger provenance",
    color: "var(--accent-crimson)",
  },
];

export function HorizontalAgentRail() {
  return (
    <section className="showcase-pinned-wrapper">
      <div className="section-header">
        <div className="section-eyebrow">Multi-Agent Orchestration Architecture</div>
        <h2 className="section-title">Four Specialized Roles. One Evidence Ledger.</h2>
        <p style={{ color: "var(--ink-secondary)", fontSize: "16px", marginTop: "12px", maxWidth: "600px" }}>
          Built using the Microsoft Agent Framework. Each agent carries a strict input/output contract to ensure tactical narratives never fabricate facts.
        </p>
      </div>

      <div className="horizontal-scroll-container">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.role}
            className="agent-showcase-card"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.12, duration: 0.5 }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className="agent-num-tag">ROLE {agent.num}</span>
                <span style={{ fontSize: "24px" }}>{agent.icon}</span>
              </div>
              <h3 className="agent-role-title">{agent.role}</h3>
              <div style={{ fontSize: "14px", fontWeight: 700, color: agent.color, marginBottom: "8px" }}>
                {agent.headline}
              </div>
              <p className="agent-role-desc">{agent.description}</p>
            </div>

            <div className="agent-spec-chip" style={{ borderLeftColor: agent.color }}>
              {agent.spec}
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
