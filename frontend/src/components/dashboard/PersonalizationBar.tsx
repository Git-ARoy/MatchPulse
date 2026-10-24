"use client";

import { useState } from "react";

export type AudienceModeType = "fan" | "analyst" | "broadcast" | "novice";
export type ClubBiasType = "neutral" | "ridge" | "harbor";
export type LanguageType = "en" | "es" | "fr" | "de" | "ar" | "ja";

interface PersonalizationProps {
  audience: AudienceModeType;
  setAudience: (m: AudienceModeType) => void;
  club: ClubBiasType;
  setClub: (c: ClubBiasType) => void;
  language: LanguageType;
  setLanguage: (l: LanguageType) => void;
  selectedPlayerId: string | null;
  setSelectedPlayerId: (id: string | null) => void;
  broadcastOverlay: boolean;
  setBroadcastOverlay: (b: boolean) => void;
  onOpenRecapModal: () => void;
}

const PLAYERS = [
  { id: "h10", name: "M. Vance (#9, ST)", team: "Ridge United", speed: "33.8 km/h", dist: "10.4 km", passAcc: "86%", rating: "8.9" },
  { id: "h7", name: "L. Thorne (#8, CM)", team: "Ridge United", speed: "32.4 km/h", dist: "11.8 km", passAcc: "91%", rating: "8.7" },
  { id: "h8", name: "A. Silva (#10, AM)", team: "Ridge United", speed: "31.2 km/h", dist: "10.6 km", passAcc: "89%", rating: "8.4" },
  { id: "h9", name: "K. Mercer (#7, RW)", team: "Ridge United", speed: "34.5 km/h", dist: "10.1 km", passAcc: "87%", rating: "8.6" },
  { id: "h6", name: "C. Sterling (#4, DM)", team: "Ridge United", speed: "30.1 km/h", dist: "12.2 km", passAcc: "94%", rating: "8.5" },
  { id: "a1", name: "E. Keller (#1, GK)", team: "Harbor FC", speed: "17.4 km/h", dist: "4.8 km", passAcc: "78%", rating: "7.9" },
  { id: "a3", name: "R. Faulkner (#4, CB)", team: "Harbor FC", speed: "29.8 km/h", dist: "9.2 km", passAcc: "90%", rating: "7.8" },
  { id: "a9", name: "T. Lindqvist (#10, AM)", team: "Harbor FC", speed: "31.5 km/h", dist: "11.1 km", passAcc: "88%", rating: "7.6" },
];

export function PersonalizationBar({
  audience,
  setAudience,
  club,
  setClub,
  language,
  setLanguage,
  selectedPlayerId,
  setSelectedPlayerId,
  broadcastOverlay,
  setBroadcastOverlay,
  onOpenRecapModal,
}: PersonalizationProps) {
  const activePlayer = PLAYERS.find((p) => p.id === selectedPlayerId);

  return (
    <div style={{ background: "#ffffff", border: "1px solid var(--line)", borderRadius: "16px", padding: "18px 24px", boxShadow: "var(--shadow-sm)", display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Top Controls Row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        {/* Left: Section Title & Personalization Tag */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: "linear-gradient(135deg, var(--pl-purple) 0%, var(--pitch-emerald) 100%)", display: "grid", placeItems: "center", color: "#fff", fontWeight: 900, fontSize: "16px" }}>
            ⚡
          </div>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--pitch-emerald)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Stage (e) Personalization Engine
            </div>
            <div style={{ fontSize: "16px", fontWeight: 900, color: "var(--pl-purple)", letterSpacing: "-0.02em" }}>
              Personalized Premier League Studio Feed
            </div>
          </div>
        </div>

        {/* Right: Quick Studio Action Buttons */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Broadcast Overlay Toggle */}
          <button
            type="button"
            onClick={() => setBroadcastOverlay(!broadcastOverlay)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "8px 14px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 800,
              cursor: "pointer",
              border: broadcastOverlay ? "1px solid var(--accent-crimson)" : "1px solid var(--line)",
              background: broadcastOverlay ? "rgba(225, 29, 72, 0.1)" : "var(--surface-subtle)",
              color: broadcastOverlay ? "var(--accent-crimson)" : "var(--ink-secondary)",
              transition: "all 0.15s ease",
            }}
          >
            <span>📺</span>
            <span>{broadcastOverlay ? "Hide TV Overlay" : "Live TV Overlay"}</span>
          </button>

          {/* Automated Match Recap Button */}
          <button
            type="button"
            onClick={onOpenRecapModal}
            className="btn-emerald"
            style={{ padding: "8px 16px", fontSize: "12px" }}
          >
            <span>📋 Generate Match Recap</span>
          </button>
        </div>
      </div>

      {/* Selectors Grid: Audience Mode, Club Focus, Player Focus, Language */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px", paddingTop: "12px", borderTop: "1px solid var(--line)" }}>
        {/* 1. Audience Mode Selector */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>
            Audience Experience
          </label>
          <select
            value={audience}
            onChange={(e) => setAudience(e.target.value as AudienceModeType)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--line-strong)", fontSize: "13px", fontWeight: 700, color: "var(--pl-purple)", background: "#fff", cursor: "pointer" }}
          >
            <option value="fan">🎉 Casual Fan (Emotion & Story)</option>
            <option value="analyst">📊 Tactical Analyst (Deep Metrics)</option>
            <option value="broadcast">🎙️ Broadcast Commentator (TV Points)</option>
            <option value="novice">🌱 Kids / Tactical Novice (Simplified)</option>
          </select>
        </div>

        {/* 2. Club Affiliation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>
            Club Perspective
          </label>
          <select
            value={club}
            onChange={(e) => setClub(e.target.value as ClubBiasType)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--line-strong)", fontSize: "13px", fontWeight: 700, color: "var(--pl-purple)", background: "#fff", cursor: "pointer" }}
          >
            <option value="neutral">⚖️ Neutral & Balanced</option>
            <option value="ridge">🟢 Ridge United (Home Bias)</option>
            <option value="harbor">🔵 Harbor FC (Away Bias)</option>
          </select>
        </div>

        {/* 3. Player Focused Cam */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>
            Player Focus Mode (Cam)
          </label>
          <select
            value={selectedPlayerId || ""}
            onChange={(e) => setSelectedPlayerId(e.target.value || null)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--line-strong)", fontSize: "13px", fontWeight: 700, color: "var(--pl-purple)", background: "#fff", cursor: "pointer" }}
          >
            <option value="">Full Match Overview (All Players)</option>
            {PLAYERS.map((p) => (
              <option key={p.id} value={p.id}>
                ⭐ {p.name} — {p.team}
              </option>
            ))}
          </select>
        </div>

        {/* 4. Multi-Language Storytelling */}
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <label style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>
            Multi-Language Narration
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as LanguageType)}
            style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid var(--line-strong)", fontSize: "13px", fontWeight: 700, color: "var(--pl-purple)", background: "#fff", cursor: "pointer" }}
          >
            <option value="en">🇬🇧 English (Global Studio)</option>
            <option value="es">🇪🇸 Español (La Liga Feed)</option>
            <option value="fr">🇫🇷 Français (Diffusion PL)</option>
            <option value="de">🇩🇪 Deutsch (Sky Sport DE)</option>
            <option value="ar">🇸🇦 العربية (beIN Sports)</option>
            <option value="ja">🇯🇵 日本語 (U-NEXT Studio)</option>
          </select>
        </div>
      </div>

      {/* Dynamic Player Focus Telemetry HUD */}
      {activePlayer && (
        <div style={{ background: "rgba(5, 150, 105, 0.05)", border: "1px solid rgba(5, 150, 105, 0.2)", borderRadius: "12px", padding: "12px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "20px" }}>🎯</span>
            <div>
              <div style={{ fontSize: "13px", fontWeight: 900, color: "var(--pl-purple)" }}>
                FOCUS ACTIVE: {activePlayer.name} ({activePlayer.team})
              </div>
              <div style={{ fontSize: "11px", color: "var(--ink-secondary)" }}>
                Real-time tracking enabled with threshold alarms
              </div>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px", flexWrap: "wrap" }}>
            <div>
              <span style={{ color: "var(--ink-muted)" }}>Sprint Peak: </span>
              <strong style={{ color: "var(--accent-crimson)", fontWeight: 900 }}>{activePlayer.speed}</strong>
            </div>
            <div>
              <span style={{ color: "var(--ink-muted)" }}>Total Distance: </span>
              <strong style={{ color: "var(--pl-purple)", fontWeight: 900 }}>{activePlayer.dist}</strong>
            </div>
            <div>
              <span style={{ color: "var(--ink-muted)" }}>Pass Accuracy: </span>
              <strong style={{ color: "var(--pitch-emerald)", fontWeight: 900 }}>{activePlayer.passAcc}</strong>
            </div>
            <button
              type="button"
              onClick={() => setSelectedPlayerId(null)}
              style={{ background: "none", border: "none", color: "var(--ink-muted)", cursor: "pointer", fontSize: "12px", fontWeight: 700, textDecoration: "underline" }}
            >
              Clear Focus
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
