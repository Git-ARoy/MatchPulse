"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

interface PlayerPos {
  id: string;
  num: number;
  name: string;
  team: "home" | "away";
  pos: string;
  x: number; // 0 - 100 percentage
  y: number; // 0 - 100 percentage
  stats: { passes: number; accuracy: string; speed: string };
}

// 4-3-3 Attacking Phase for Ridge United (Home - Emerald)
const HOME_PLAYERS_ATTACK: PlayerPos[] = [
  { id: "h1", num: 1, name: "Pickford", team: "home", pos: "GK", x: 6, y: 50, stats: { passes: 22, accuracy: "84%", speed: "18.2 km/h" } },
  { id: "h2", num: 2, name: "Walker", team: "home", pos: "RB", x: 48, y: 15, stats: { passes: 54, accuracy: "91%", speed: "32.1 km/h" } },
  { id: "h3", num: 5, name: "Stones", team: "home", pos: "CB", x: 38, y: 38, stats: { passes: 68, accuracy: "95%", speed: "27.4 km/h" } },
  { id: "h4", num: 6, name: "Dias", team: "home", pos: "CB", x: 38, y: 62, stats: { passes: 72, accuracy: "93%", speed: "28.0 km/h" } },
  { id: "h5", num: 3, name: "Shaw", team: "home", pos: "LB", x: 52, y: 85, stats: { passes: 49, accuracy: "88%", speed: "30.5 km/h" } },
  { id: "h6", num: 4, name: "Rice", team: "home", pos: "DM", x: 50, y: 50, stats: { passes: 61, accuracy: "92%", speed: "29.1 km/h" } },
  { id: "h7", num: 8, name: "Bellingham", team: "home", pos: "CM", x: 65, y: 34, stats: { passes: 45, accuracy: "89%", speed: "31.8 km/h" } },
  { id: "h8", num: 10, name: "Foden", team: "home", pos: "AM", x: 68, y: 66, stats: { passes: 51, accuracy: "87%", speed: "30.2 km/h" } },
  { id: "h9", num: 7, name: "Saka", team: "home", pos: "RW", x: 78, y: 20, stats: { passes: 38, accuracy: "85%", speed: "33.4 km/h" } },
  { id: "h10", num: 9, name: "Kane", team: "home", pos: "ST", x: 82, y: 50, stats: { passes: 29, accuracy: "82%", speed: "28.9 km/h" } },
  { id: "h11", num: 11, name: "Gordon", team: "home", pos: "LW", x: 79, y: 80, stats: { passes: 34, accuracy: "86%", speed: "34.1 km/h" } },
];

// 4-2-3-1 Low Defensive Block for Harbor FC (Away - Royal Blue)
const AWAY_PLAYERS_DEFENSE: PlayerPos[] = [
  { id: "a1", num: 1, name: "Alisson", team: "away", pos: "GK", x: 94, y: 50, stats: { passes: 19, accuracy: "79%", speed: "16.5 km/h" } },
  { id: "a2", num: 2, name: "Trippier", team: "away", pos: "RB", x: 84, y: 22, stats: { passes: 32, accuracy: "76%", speed: "29.4 km/h" } },
  { id: "a3", num: 4, name: "Van Dijk", team: "away", pos: "CB", x: 86, y: 40, stats: { passes: 44, accuracy: "89%", speed: "27.8 km/h" } },
  { id: "a4", num: 5, name: "Saliba", team: "away", pos: "CB", x: 86, y: 60, stats: { passes: 41, accuracy: "90%", speed: "28.5 km/h" } },
  { id: "a5", num: 3, name: "Robertson", team: "away", pos: "LB", x: 83, y: 78, stats: { passes: 36, accuracy: "81%", speed: "31.0 km/h" } },
  { id: "a6", num: 6, name: "Rodri", team: "away", pos: "DM", x: 72, y: 42, stats: { passes: 52, accuracy: "92%", speed: "28.3 km/h" } },
  { id: "a7", num: 8, name: "Guimaraes", team: "away", pos: "DM", x: 73, y: 58, stats: { passes: 47, accuracy: "88%", speed: "29.7 km/h" } },
  { id: "a8", num: 7, name: "Bowen", team: "away", pos: "RM", x: 62, y: 25, stats: { passes: 24, accuracy: "74%", speed: "32.6 km/h" } },
  { id: "a9", num: 10, name: "Odegaard", team: "away", pos: "AM", x: 64, y: 50, stats: { passes: 39, accuracy: "84%", speed: "30.1 km/h" } },
  { id: "a10", num: 11, name: "Martinelli", team: "away", pos: "LM", x: 63, y: 75, stats: { passes: 28, accuracy: "77%", speed: "33.8 km/h" } },
  { id: "a11", num: 9, name: "Watkins", team: "away", pos: "ST", x: 54, y: 50, stats: { passes: 18, accuracy: "70%", speed: "33.2 km/h" } },
];

export default function AnalysisPage() {
  const params = useParams();
  const matchId = (params?.id as string) || "sim_match_001";

  const [tacticalPhase, setTacticalPhase] = useState<"attack" | "transition" | "defense">("attack");
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerPos | null>(HOME_PLAYERS_ATTACK[9]); // Kane selected by default
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [timelineSec, setTimelineSec] = useState(4450); // ~74:10
  const [isPlaying, setIsPlaying] = useState(true);

  // Ball coordinate tracking
  const [ballPos, setBallPos] = useState({ x: 78, y: 35 });

  // Playhead scrubber
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setTimelineSec((prev) => (prev >= 5400 ? 0 : prev + 1));
      // Dynamic micro movement for ball
      setBallPos((prev) => ({
        x: Math.min(92, Math.max(10, prev.x + (Math.random() * 4 - 2))),
        y: Math.min(88, Math.max(12, prev.y + (Math.random() * 4 - 2))),
      }));
    }, 1000);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const formatTime = (totalSec: number) => {
    const mins = Math.floor(totalSec / 60);
    const secs = totalSec % 60;
    return `${mins}:${secs < 10 ? `0${secs}` : secs}`;
  };

  return (
    <main style={{ maxWidth: "1440px", margin: "0 auto", padding: "28px 24px 60px", display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Top Header & Breadcrumbs */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", fontWeight: 600, color: "var(--ink-muted)", marginBottom: "4px" }}>
            <Link href="/" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Overview</Link>
            <span>/</span>
            <Link href="/dashboard" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Live Console</Link>
            <span>/</span>
            <span style={{ color: "var(--pl-purple)", fontWeight: 700 }}>2D Tactical Pitch Radar</span>
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 900, color: "var(--pl-purple)", letterSpacing: "-0.04em" }}>
            Tactical Pitch Radar & Player Tracking
          </h1>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div className="live-pill">
            <span className="live-blip" />
            <span>22 PLAYERS TRACKED</span>
          </div>

          <button
            type="button"
            onClick={() => setShowHeatmap(!showHeatmap)}
            className="btn-secondary"
            style={{ fontSize: "13px", padding: "8px 14px", background: showHeatmap ? "rgba(5, 150, 105, 0.12)" : "#fff" }}
          >
            🔥 {showHeatmap ? "Hide Heatmap" : "Territory Heatmap"}
          </button>

          <Link href="/dashboard" className="btn-primary" style={{ fontSize: "13px", padding: "8px 16px" }}>
            ← Return to Console
          </Link>
        </div>
      </div>

      {/* Main Radar Layout: Pitch on Left (75%), Tactical Intel on Right (25%) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.45fr 0.55fr", gap: "24px", alignItems: "start" }}>
        {/* Left: The Authentic 2D Pitch */}
        <div className="pitch-radar-card" style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Pitch Sub-header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--pitch-emerald)" }} />
                <span style={{ fontSize: "13px", fontWeight: 800, color: "var(--pl-purple)" }}>Ridge United (4-3-3)</span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ width: 12, height: 12, borderRadius: "50%", background: "var(--accent-blue)" }} />
                <span style={{ fontSize: "13px", fontWeight: 800, color: "var(--ink-secondary)" }}>Harbor FC (4-2-3-1)</span>
              </div>
            </div>

            {/* Tactical Phase Selector */}
            <div style={{ display: "flex", background: "var(--surface-subtle)", padding: "3px", borderRadius: "8px", gap: "4px" }}>
              {(["attack", "transition", "defense"] as const).map((phase) => (
                <button
                  key={phase}
                  type="button"
                  onClick={() => setTacticalPhase(phase)}
                  style={{
                    padding: "4px 10px",
                    fontSize: "11px",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    background: tacticalPhase === phase ? "#ffffff" : "transparent",
                    color: tacticalPhase === phase ? "var(--pl-purple)" : "var(--ink-muted)",
                    boxShadow: tacticalPhase === phase ? "var(--shadow-sm)" : "none",
                  }}
                >
                  {phase}
                </button>
              ))}
            </div>
          </div>

          {/* The Standard 105m x 68m Football Pitch */}
          <div className="pitch-boundary" role="region" aria-label="Premier League 2D Tactical Pitch">
            {/* Ambient Heatmap Layer */}
            {showHeatmap && (
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "radial-gradient(ellipse 40% 50% at 75% 45%, rgba(239, 68, 68, 0.45) 0%, rgba(245, 158, 11, 0.35) 40%, rgba(16, 185, 129, 0.15) 70%, transparent 100%)",
                  pointerEvents: "none",
                  zIndex: 2,
                }}
              />
            )}

            {/* Pitch Lines Markings */}
            <div className="pitch-line pitch-halfway" />
            <div className="pitch-line pitch-center-circle" />
            <div className="pitch-line pitch-center-spot" />

            {/* Left Penalty & Goal Area (Home) */}
            <div className="pitch-line penalty-box-left" />
            <div className="pitch-line goal-box-left" />
            <div className="pitch-line penalty-arc-left" />
            <div style={{ position: "absolute", top: "50%", left: "11%", width: 6, height: 6, background: "#fff", borderRadius: "50%", transform: "translate(-50%, -50%)" }} />

            {/* Right Penalty & Goal Area (Away) */}
            <div className="pitch-line penalty-box-right" />
            <div className="pitch-line goal-box-right" />
            <div className="pitch-line penalty-arc-right" />
            <div style={{ position: "absolute", top: "50%", right: "11%", width: 6, height: 6, background: "#fff", borderRadius: "50%", transform: "translate(50%, -50%)" }} />

            {/* Home Players */}
            {HOME_PLAYERS_ATTACK.map((player) => (
              <motion.div
                key={player.id}
                className="player-token token-home"
                style={{ left: `${player.x}%`, top: `${player.y}%` }}
                animate={{
                  left: `${player.x + (tacticalPhase === "defense" ? -10 : tacticalPhase === "attack" ? 4 : 0)}%`,
                  top: `${player.y}%`,
                }}
                transition={{ type: "spring", stiffness: 120, damping: 18 }}
                onClick={() => setSelectedPlayer(player)}
                whileHover={{ scale: 1.25, zIndex: 30 }}
                title={`${player.num}. ${player.name} (${player.pos})`}
              >
                <span>{player.num}</span>
              </motion.div>
            ))}

            {/* Away Players */}
            {AWAY_PLAYERS_DEFENSE.map((player) => (
              <motion.div
                key={player.id}
                className="player-token token-away"
                style={{ left: `${player.x}%`, top: `${player.y}%` }}
                animate={{
                  left: `${player.x + (tacticalPhase === "defense" ? -5 : tacticalPhase === "attack" ? -8 : 0)}%`,
                  top: `${player.y}%`,
                }}
                transition={{ type: "spring", stiffness: 120, damping: 18 }}
                onClick={() => setSelectedPlayer(player)}
                whileHover={{ scale: 1.25, zIndex: 30 }}
                title={`${player.num}. ${player.name} (${player.pos})`}
              >
                <span>{player.num}</span>
              </motion.div>
            ))}

            {/* Ball Marker */}
            <motion.div
              className="ball-token"
              animate={{ left: `${ballPos.x}%`, top: `${ballPos.y}%` }}
              transition={{ type: "spring", stiffness: 180, damping: 20 }}
            />
          </div>

          {/* Timeline & Match Scrubber Bar */}
          <div style={{ display: "flex", alignItems: "center", gap: "16px", padding: "12px 16px", background: "var(--surface-subtle)", borderRadius: "12px" }}>
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                background: "var(--pl-purple)",
                color: "#fff",
                border: "none",
                display: "grid",
                placeItems: "center",
                cursor: "pointer",
                fontWeight: 800,
              }}
            >
              {isPlaying ? "❚❚" : "▶"}
            </button>

            <span className="font-mono tabular-nums" style={{ fontSize: "14px", fontWeight: 800, color: "var(--pl-purple)", minWidth: "50px" }}>
              {formatTime(timelineSec)}
            </span>

            <input
              type="range"
              min="0"
              max="5400"
              value={timelineSec}
              onChange={(e) => setTimelineSec(Number(e.target.value))}
              style={{ flex: 1, accentColor: "var(--pitch-emerald)", cursor: "pointer" }}
            />

            <span style={{ fontSize: "12px", color: "var(--ink-muted)", fontWeight: 700 }}>90:00</span>
          </div>
        </div>

        {/* Right: Tactical Inspector & Selected Player Dossier */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* Selected Player Dossier Card */}
          <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "16px", padding: "20px", boxShadow: "var(--shadow-sm)" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--pitch-emerald)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
              Inspected Player Profile
            </div>

            {selectedPlayer ? (
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <div
                    style={{
                      width: "44px",
                      height: "44px",
                      borderRadius: "50%",
                      background: selectedPlayer.team === "home" ? "var(--pitch-emerald)" : "var(--accent-blue)",
                      color: "#fff",
                      display: "grid",
                      placeItems: "center",
                      fontWeight: 900,
                      fontSize: "18px",
                    }}
                  >
                    {selectedPlayer.num}
                  </div>
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: 900, color: "var(--pl-purple)" }}>
                      {selectedPlayer.name}
                    </h3>
                    <div style={{ fontSize: "12px", color: "var(--ink-muted)", fontWeight: 600 }}>
                      {selectedPlayer.pos} · {selectedPlayer.team === "home" ? "Ridge United" : "Harbor FC"}
                    </div>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "16px" }}>
                  <div style={{ background: "var(--surface-subtle)", padding: "10px", borderRadius: "8px" }}>
                    <div style={{ fontSize: "10px", color: "var(--ink-muted)", fontWeight: 700 }}>PASS ACCURACY</div>
                    <div style={{ fontSize: "16px", fontWeight: 900, color: "var(--pitch-emerald)" }}>{selectedPlayer.stats.accuracy}</div>
                  </div>
                  <div style={{ background: "var(--surface-subtle)", padding: "10px", borderRadius: "8px" }}>
                    <div style={{ fontSize: "10px", color: "var(--ink-muted)", fontWeight: 700 }}>SPRINT SPEED</div>
                    <div style={{ fontSize: "16px", fontWeight: 900, color: "var(--pl-purple)" }}>{selectedPlayer.stats.speed}</div>
                  </div>
                </div>

                <div style={{ marginTop: "12px", fontSize: "12px", color: "var(--ink-secondary)", lineHeight: "1.5" }}>
                  Current Position: <span className="font-mono tabular-nums">({selectedPlayer.x}m, {selectedPlayer.y}m)</span>. Active attacking anchor creating forward passing triangles.
                </div>
              </div>
            ) : (
              <p style={{ fontSize: "13px", color: "var(--ink-muted)" }}>Click any player token on the pitch to inspect live metrics.</p>
            )}
          </div>

          {/* Territorial Corridor Breakdown */}
          <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "16px", padding: "20px", boxShadow: "var(--shadow-sm)" }}>
            <h3 style={{ fontSize: "15px", fontWeight: 800, color: "var(--pl-purple)", marginBottom: "14px" }}>
              Territorial Zone Channels
            </h3>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Left Flank (Zone 1-3)</span>
                  <span className="font-mono">28%</span>
                </div>
                <div style={{ height: "6px", background: "var(--surface-subtle)", borderRadius: "999px", overflow: "hidden" }}>
                  <div style={{ width: "28%", height: "100%", background: "var(--accent-blue)", borderRadius: "999px" }} />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Central Half-Spaces (Zone 4-6)</span>
                  <span className="font-mono" style={{ color: "var(--pitch-emerald)" }}>48% (Overload)</span>
                </div>
                <div style={{ height: "6px", background: "var(--surface-subtle)", borderRadius: "999px", overflow: "hidden" }}>
                  <div style={{ width: "48%", height: "100%", background: "var(--pitch-emerald)", borderRadius: "999px" }} />
                </div>
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>
                  <span>Right Flank (Zone 7-9)</span>
                  <span className="font-mono">24%</span>
                </div>
                <div style={{ height: "6px", background: "var(--surface-subtle)", borderRadius: "999px", overflow: "hidden" }}>
                  <div style={{ width: "24%", height: "100%", background: "var(--pl-purple)", borderRadius: "999px" }} />
                </div>
              </div>
            </div>
          </div>

          {/* Quick Action Navigation */}
          <div style={{ background: "linear-gradient(135deg, rgba(56,0,60,0.04) 0%, rgba(5,150,105,0.04) 100%)", border: "1px solid var(--line)", borderRadius: "16px", padding: "18px" }}>
            <h4 style={{ fontSize: "13px", fontWeight: 800, color: "var(--pl-purple)", marginBottom: "6px" }}>
              Evidence-First Engine Provenance
            </h4>
            <p style={{ fontSize: "11px", color: "var(--ink-secondary)", lineHeight: "1.5" }}>
              Markers reflect true canonical coordinates from the match ledger. All spatial classifications obey the official pitch boundaries.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
