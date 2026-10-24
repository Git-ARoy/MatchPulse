"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface AutoEventingProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AutoEventingFeed({ isOpen, onClose }: AutoEventingProps) {
  const [ballSpeed, setBallSpeed] = useState(48.2);
  const [detectedEvents, setDetectedEvents] = useState<string[]>([
    "00:14.2 — [CV] Pass Classified: Distance 22.4m, Difficulty 68/100 (Kane → Foden)",
    "00:18.8 — [CV] High Press Sprint Detected: Foden (31.2 km/h)",
    "00:22.1 — [CV] Ball Recovery Tracked: Coordinates (68, 44)",
    "00:26.5 — [CV] Shot Event Ingested: Velocity Vector 104.2 km/h",
  ]);

  useEffect(() => {
    if (!isOpen) return;
    const interval = setInterval(() => {
      setBallSpeed((prev) => +(prev + (Math.random() * 6 - 3)).toFixed(1));
    }, 1200);
    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        background: "#0f172a",
        borderRadius: "16px",
        padding: "20px",
        color: "#ffffff",
        border: "1px solid rgba(0, 255, 135, 0.4)",
        boxShadow: "0 12px 30px rgba(0, 0, 0, 0.4)",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
      }}
    >
      {/* Top Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255, 255, 255, 0.15)", paddingBottom: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ width: 10, height: 10, borderRadius: "50%", background: "#00ff87", boxShadow: "0 0 10px #00ff87" }} />
          <div>
            <div style={{ fontSize: "14px", fontWeight: 900, letterSpacing: "0.04em", color: "#00ff87" }}>
              AI COMPUTER VISION AUTO-EVENTING STREAM
            </div>
            <div style={{ fontSize: "11px", color: "rgba(255, 255, 255, 0.7)" }}>
              Extracts canonical pass, shot, and speed metrics directly from optical broadcast feed
            </div>
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{ fontSize: "11px", background: "rgba(255, 255, 255, 0.1)", padding: "4px 8px", borderRadius: "6px" }}>
            Model Inference: <strong style={{ color: "#00ff87" }}>14.2ms</strong> · 60 FPS
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#fff", cursor: "pointer", fontSize: "14px", fontWeight: 800 }}
          >
            ✕
          </button>
        </div>
      </div>

      {/* Simulated Optical Tracking Viewport */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "160px",
          background: "radial-gradient(ellipse at 50% 50%, #064e3b 0%, #022c22 100%)",
          borderRadius: "10px",
          overflow: "hidden",
          border: "1px solid rgba(255, 255, 255, 0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-around",
          padding: "20px",
        }}
      >
        {/* Computer Vision Scan Line */}
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            width: "2px",
            background: "rgba(0, 255, 135, 0.8)",
            boxShadow: "0 0 15px rgba(0, 255, 135, 1)",
            animation: "scan-line 3s linear infinite",
          }}
        />

        {/* Bounding Box Player 1 (Kane) */}
        <div style={{ border: "1.5px dashed #00ff87", padding: "6px 10px", borderRadius: "4px", background: "rgba(0, 255, 135, 0.1)" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#00ff87" }}>[ID: RU-9 KANE]</div>
          <div style={{ fontSize: "11px", fontWeight: 900 }}>Speed: 33.8 km/h</div>
          <div style={{ fontSize: "9px", color: "rgba(255, 255, 255, 0.6)" }}>Confidence: 99.4%</div>
        </div>

        {/* Bounding Box Ball */}
        <div style={{ border: "2px solid #38bdf8", padding: "6px 12px", borderRadius: "999px", background: "rgba(56, 189, 248, 0.15)", textAlign: "center" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#38bdf8" }}>⚽ BALL VECTOR</div>
          <div style={{ fontSize: "13px", fontWeight: 900 }}>{ballSpeed} km/h</div>
        </div>

        {/* Bounding Box Player 2 (Van Dijk) */}
        <div style={{ border: "1.5px dashed #f43f5e", padding: "6px 10px", borderRadius: "4px", background: "rgba(244, 63, 94, 0.1)" }}>
          <div style={{ fontSize: "10px", fontWeight: 800, color: "#f43f5e" }}>[ID: HF-4 VAN DIJK]</div>
          <div style={{ fontSize: "11px", fontWeight: 900 }}>Speed: 29.8 km/h</div>
          <div style={{ fontSize: "9px", color: "rgba(255, 255, 255, 0.6)" }}>Confidence: 98.9%</div>
        </div>
      </div>

      {/* Auto-detected Stream Log */}
      <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
        <div style={{ fontSize: "10px", fontWeight: 800, color: "rgba(255, 255, 255, 0.6)", textTransform: "uppercase" }}>
          Automated Model Event Extraction Ledger
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "4px", maxHeight: "80px", overflowY: "auto", fontSize: "11px", fontFamily: "var(--font-mono)" }}>
          {detectedEvents.map((ev, i) => (
            <div key={i} style={{ color: i === 0 ? "#00ff87" : "rgba(255, 255, 255, 0.8)" }}>
              {ev}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
