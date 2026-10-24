"use client";

import { motion } from "framer-motion";

interface BroadcastOverlayProps {
  score: string;
  clock: string;
  headline: string;
  whyItMatters: string;
  shotSpeedKph?: number;
  passDifficulty?: number;
  pressureIndex: number;
  onClose: () => void;
}

export function BroadcastOverlay({
  score,
  clock,
  headline,
  whyItMatters,
  shotSpeedKph = 104.2,
  passDifficulty = 74,
  pressureIndex,
  onClose,
}: BroadcastOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 30 }}
      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: "fixed",
        bottom: "24px",
        left: "50%",
        transform: "translateX(-50%)",
        width: "calc(100% - 48px)",
        maxWidth: "1100px",
        zIndex: 9999,
        background: "rgba(36, 0, 38, 0.94)",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        borderRadius: "16px",
        padding: "18px 24px",
        boxShadow: "0 25px 60px rgba(0, 0, 0, 0.5), 0 0 0 2px rgba(0, 255, 135, 0.3)",
        color: "#ffffff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        {/* Left: Official Premier League Studio Score Bug */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          {/* PL Lion Brand Badge */}
          <div style={{ width: "38px", height: "38px", borderRadius: "8px", background: "var(--pl-purple-light)", display: "grid", placeItems: "center" }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#00FF87" />
            </svg>
          </div>

          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "11px", fontWeight: 900, letterSpacing: "0.08em", color: "#00FF87", textTransform: "uppercase" }}>
                PL PRODUCTIONS · LIVE OVERLAY
              </span>
              <span style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.6)" }}>• 1080p50 SYNCHRONIZED</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "2px" }}>
              <span style={{ fontSize: "20px", fontWeight: 900, letterSpacing: "-0.03em" }}>RIDGE {score} HARBOR</span>
              <span style={{ background: "rgba(255, 255, 255, 0.15)", padding: "2px 8px", borderRadius: "6px", fontSize: "12px", fontWeight: 800, color: "#00FF87" }}>
                ⏱ {clock}
              </span>
            </div>
          </div>
        </div>

        {/* Center: Live Lower-Third Machine-Readable Graphic Copy */}
        <div style={{ flex: 1, minWidth: "300px", padding: "0 16px", borderLeft: "1px solid rgba(255, 255, 255, 0.15)", borderRight: "1px solid rgba(255, 255, 255, 0.15)" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "#00FF87", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            MOMENTUM ALERT (PRESSURE-V1: {pressureIndex.toFixed(1)})
          </div>
          <div style={{ fontSize: "14px", fontWeight: 800, color: "#ffffff", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {headline}
          </div>
          <div style={{ fontSize: "12px", color: "rgba(255, 255, 255, 0.75)", marginTop: "2px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
            {whyItMatters}
          </div>
        </div>

        {/* Right: Broadcast Telemetry Badges & Close Button */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{ display: "flex", gap: "10px" }}>
            <div style={{ background: "rgba(0, 255, 135, 0.12)", border: "1px solid rgba(0, 255, 135, 0.3)", borderRadius: "8px", padding: "6px 10px", textAlign: "center" }}>
              <div style={{ fontSize: "9px", color: "#00FF87", fontWeight: 800 }}>SHOT SPEED</div>
              <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff" }}>{shotSpeedKph} km/h</div>
            </div>

            <div style={{ background: "rgba(2, 132, 199, 0.15)", border: "1px solid rgba(2, 132, 199, 0.4)", borderRadius: "8px", padding: "6px 10px", textAlign: "center" }}>
              <div style={{ fontSize: "9px", color: "#38bdf8", fontWeight: 800 }}>PASS DIFFICULTY</div>
              <div style={{ fontSize: "13px", fontWeight: 900, color: "#ffffff" }}>{passDifficulty}/100</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close Broadcast Overlay"
            style={{
              width: "28px",
              height: "28px",
              borderRadius: "50%",
              background: "rgba(255, 255, 255, 0.1)",
              border: "none",
              color: "#ffffff",
              fontSize: "14px",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
            }}
          >
            ✕
          </button>
        </div>
      </div>
    </motion.div>
  );
}
