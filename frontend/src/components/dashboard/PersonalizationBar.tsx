"use client";

import { useState } from "react";

export type AudienceModeType = "fan" | "analyst" | "broadcast" | "novice";
export type ClubBiasType = "neutral" | "ridge" | "harbor";
export type LanguageType = "en" | "es" | "pt" | "de" | "fr" | "it" | "nl" | "ar" | "tr" | "ja";

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
    <div className="personalization-bar-card">
      {/* Top Controls Row */}
      <div className="personalization-top-row">
        {/* Left: Section Title & Personalization Tag */}
        <div className="personalization-brand-group">
          <div className="personalization-icon-badge" aria-hidden="true">
            ⚡
          </div>
          <div>
            <div className="personalization-kicker">
              Stage (e) Personalization Engine
            </div>
            <div className="personalization-title">
              Personalized Premier League Studio Feed
            </div>
          </div>
        </div>

        {/* Right: Quick Studio Action Buttons */}
        <div className="personalization-action-buttons">
          {/* Broadcast Overlay Toggle */}
          <button
            type="button"
            onClick={() => setBroadcastOverlay(!broadcastOverlay)}
            className={`tv-overlay-toggle-btn ${broadcastOverlay ? "active" : ""}`}
            aria-pressed={broadcastOverlay}
          >
            <span>📺</span>
            <span>{broadcastOverlay ? "Hide TV Overlay" : "Live TV Overlay"}</span>
          </button>

          {/* Automated Match Recap Button */}
          <button
            type="button"
            onClick={onOpenRecapModal}
            className="btn-emerald recap-open-btn"
          >
            <span>📋 Generate Match Recap</span>
          </button>
        </div>
      </div>

      {/* Selectors Grid: Audience Mode, Club Focus, Player Focus, Language */}
      <div className="personalization-selects-grid">
        {/* 1. Audience Mode Selector */}
        <div className="personalization-select-col">
          <label className="select-label">
            Audience Experience
          </label>
          <select
            value={audience}
            onChange={(e) => setAudience(e.target.value as AudienceModeType)}
            className="personalization-select"
            aria-label="Audience Experience"
          >
            <option value="fan">🎉 Casual Fan (Emotion & Story)</option>
            <option value="analyst">📊 Tactical Analyst (Deep Metrics)</option>
            <option value="broadcast">🎙️ Broadcast Commentator (TV Points)</option>
            <option value="novice">🌱 Kids / Tactical Novice (Simplified)</option>
          </select>
        </div>

        {/* 2. Club Affiliation */}
        <div className="personalization-select-col">
          <label className="select-label">
            Club Perspective
          </label>
          <select
            value={club}
            onChange={(e) => setClub(e.target.value as ClubBiasType)}
            className="personalization-select"
            aria-label="Club Perspective"
          >
            <option value="neutral">⚖️ Neutral & Balanced</option>
            <option value="ridge">🟢 Ridge United (Home Bias)</option>
            <option value="harbor">🔵 Harbor FC (Away Bias)</option>
          </select>
        </div>

        {/* 3. Player Focused Cam */}
        <div className="personalization-select-col">
          <label className="select-label">
            Player Focus Mode (Cam)
          </label>
          <select
            value={selectedPlayerId || ""}
            onChange={(e) => setSelectedPlayerId(e.target.value || null)}
            className="personalization-select"
            aria-label="Player Focus Mode"
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
        <div className="personalization-select-col">
          <label className="select-label">
            Multi-Language Narration
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value as LanguageType)}
            className="personalization-select"
            aria-label="Multi-Language Narration"
          >
            <option value="en">🇬🇧 English (Global Studio)</option>
            <option value="es">🇪🇸 Español (La Liga Feed)</option>
            <option value="pt">🇧🇷 Português (Brasileirão / Seleção)</option>
            <option value="de">🇩🇪 Deutsch (Sky Sport DE)</option>
            <option value="fr">🇫🇷 Français (Diffusion PL)</option>
            <option value="it">🇮🇹 Italiano (Serie A / Calcio)</option>
            <option value="nl">🇳🇱 Nederlands (Eredivisie / Oranje)</option>
            <option value="ar">🇸🇦 العربية (beIN Sports)</option>
            <option value="tr">🇹🇷 Türkçe (Süper Lig)</option>
            <option value="ja">🇯🇵 日本語 (U-NEXT Studio)</option>
          </select>
        </div>
      </div>

      {/* Dynamic Player Focus Telemetry HUD */}
      {activePlayer && (
        <div className="personalization-player-hud">
          <div className="hud-header-group">
            <span className="hud-target-icon">🎯</span>
            <div>
              <div className="hud-player-title">
                FOCUS ACTIVE: {activePlayer.name} ({activePlayer.team})
              </div>
              <div className="hud-player-sub">
                Real-time tracking enabled with threshold alarms
              </div>
            </div>
          </div>

          <div className="personalization-hud-facts">
            <div className="hud-stat-box">
              <span className="stat-name">Sprint Peak</span>
              <strong className="stat-val crimson">{activePlayer.speed}</strong>
            </div>
            <div className="hud-stat-box">
              <span className="stat-name">Total Distance</span>
              <strong className="stat-val purple">{activePlayer.dist}</strong>
            </div>
            <div className="hud-stat-box">
              <span className="stat-name">Pass Accuracy</span>
              <strong className="stat-val emerald">{activePlayer.passAcc}</strong>
            </div>
            <button
              type="button"
              onClick={() => setSelectedPlayerId(null)}
              className="hud-clear-btn"
            >
              Clear Focus
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
