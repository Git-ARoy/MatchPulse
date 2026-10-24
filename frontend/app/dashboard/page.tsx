"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  PersonalizationBar,
  AudienceModeType,
  ClubBiasType,
  LanguageType,
} from "../../src/components/dashboard/PersonalizationBar";
import { BroadcastOverlay } from "../../src/components/dashboard/BroadcastOverlay";
import { RecapModal } from "../../src/components/dashboard/RecapModal";
import {
  fetchMatchState,
  fetchMatchEvents,
  fetchMatchInsights,
  injectFixture,
} from "../../src/lib/api";

interface LiveEvent {
  event_id: string;
  minute: number;
  second: number;
  team_id: string;
  player_id?: string;
  event_type: string;
  x?: number;
  y?: number;
  detail?: string;
}

const INITIAL_EVENTS: LiveEvent[] = [
  { event_id: "ev_101", minute: 74, second: 12, team_id: "ridge_united", player_id: "player_9", event_type: "Shot On Target", x: 88, y: 52, detail: "Low drive saved at bottom corner (104.2 km/h)" },
  { event_id: "ev_100", minute: 73, second: 55, team_id: "ridge_united", player_id: "player_7", event_type: "Attacking 3rd Entry", x: 74, y: 35, detail: "Cut-back cross into six-yard box (Pass Diff: 74/100)" },
  { event_id: "ev_099", minute: 73, second: 30, team_id: "ridge_united", player_id: "player_8", event_type: "High Regain", x: 68, y: 44, detail: "Turnover forced 32m from goal (Sprint: 32.4 km/h)" },
  { event_id: "ev_098", minute: 72, second: 48, team_id: "harbor_fc", player_id: "player_4", event_type: "Clearance", x: 22, y: 48, detail: "Headed out under heavy box pressure" },
  { event_id: "ev_097", minute: 72, second: 10, team_id: "ridge_united", player_id: "player_10", event_type: "Key Pass", x: 65, y: 28, detail: "Through-ball breaking harbor defensive block (Dist: 28m)" },
  { event_id: "ev_096", minute: 71, second: 22, team_id: "ridge_united", player_id: "player_6", event_type: "Ball Recovery", x: 55, y: 62, detail: "Intercepted loose second ball" },
];

export default function DashboardPage() {
  const matchId = "sim_match_001";
  const [matchClock, setMatchClock] = useState({ min: 74, sec: 18 });
  const [events, setEvents] = useState<LiveEvent[]>(INITIAL_EVENTS);
  const [activeFixture, setActiveFixture] = useState<string | null>(null);
  const [fixtureStatus, setFixtureStatus] = useState<string>("");
  const [pressureIndex, setPressureIndex] = useState(74.5);
  const [pressureDelta, setPressureDelta] = useState("+41.0");

  // Personalization States
  const [audience, setAudience] = useState<AudienceModeType>("fan");
  const [club, setClub] = useState<ClubBiasType>("neutral");
  const [language, setLanguage] = useState<LanguageType>("en");
  const [selectedPlayerId, setSelectedPlayerId] = useState<string | null>(null);
  const [broadcastOverlay, setBroadcastOverlay] = useState(false);
  const [isRecapModalOpen, setIsRecapModalOpen] = useState(false);

  // Live match polling & WebSocket sync
  const refreshMatchData = useCallback(async () => {
    const state = await fetchMatchState(matchId);
    if (state) {
      if (state.match_clock) setMatchClock({ min: state.match_clock.minute, sec: state.match_clock.second });
      const ridgeMetric = state.metrics?.["pressure_index:ridge_united"];
      if (ridgeMetric) {
        setPressureIndex(ridgeMetric.value);
        if (ridgeMetric.delta != null) {
          const deltaSign = ridgeMetric.delta >= 0 ? "+" : "";
          setPressureDelta(`${deltaSign}${ridgeMetric.delta.toFixed(1)}`);
        }
      }
    }
  }, [matchId]);

  useEffect(() => {
    refreshMatchData();
    const interval = setInterval(refreshMatchData, 4000);
    return () => clearInterval(interval);
  }, [refreshMatchData]);

  // Clock progression
  useEffect(() => {
    const timer = setInterval(() => {
      setMatchClock((prev) => {
        const nextSec = prev.sec + 1;
        if (nextSec >= 60) return { min: prev.min + 1, sec: 0 };
        return { min: prev.min, sec: nextSec };
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleInjectFixture = async (type: "pressure" | "goal" | "card" | "reset") => {
    setActiveFixture(type);
    const fixtureName = type === "pressure" ? "pressure-swing" : type === "goal" ? "goal-sequence" : "quiet-period";
    await injectFixture(matchId, fixtureName);

    if (type === "pressure") {
      setPressureIndex(86.2);
      setPressureDelta("+44.5");
      setFixtureStatus("Injected: Ridge United High Regain & Final-Third Box Surge");
      const newEv: LiveEvent = {
        event_id: `ev_${Date.now()}`,
        minute: matchClock.min,
        second: matchClock.sec,
        team_id: "ridge_united",
        player_id: "player_9",
        event_type: "Attacking 3rd Entry",
        x: 82,
        y: 49,
        detail: "Sustained penalty box attack (+44.5 Δ surge, difficulty 82/100)",
      };
      setEvents((prev) => [newEv, ...prev.slice(0, 8)]);
    } else if (type === "goal") {
      setPressureIndex(92.0);
      setPressureDelta("+55.0");
      setFixtureStatus("Injected: GOAL! Ridge United 2 - 0 Harbor FC");
      const newEv: LiveEvent = {
        event_id: `ev_${Date.now()}`,
        minute: matchClock.min,
        second: matchClock.sec,
        team_id: "ridge_united",
        player_id: "player_9",
        event_type: "GOAL",
        x: 95,
        y: 50,
        detail: "Clinical finish inside right post (Shot speed: 106.8 km/h)",
      };
      setEvents((prev) => [newEv, ...prev.slice(0, 8)]);
    } else if (type === "card") {
      setFixtureStatus("Injected: Harbor FC Tactical Booking (Yellow Card)");
      const newEv: LiveEvent = {
        event_id: `ev_${Date.now()}`,
        minute: matchClock.min,
        second: matchClock.sec,
        team_id: "harbor_fc",
        player_id: "player_4",
        event_type: "Yellow Card",
        x: 44,
        y: 60,
        detail: "Cynical tactical foul halting counter-attack",
      };
      setEvents((prev) => [newEv, ...prev.slice(0, 8)]);
    } else {
      setPressureIndex(52.0);
      setPressureDelta("+0.0");
      setFixtureStatus("Reset match timeline to baseline equilibrium");
      setEvents(INITIAL_EVENTS);
    }

    setTimeout(() => setActiveFixture(null), 1500);
  };

  // Dynamic narrative generation based on language & audience & club
  const getNarrativeCopy = () => {
    // English
    if (language === "en") {
      if (audience === "novice") {
        return {
          badge: "SOCCER RULES & TACTICS EXPLAINER",
          title: "What is happening right now?",
          desc: "Ridge United are 'pressing high' — meaning they run towards Harbor FC defenders to steal the ball near Harbor's goal! When the Pressure Index goes above 60, it means a goal might happen soon.",
          takeaway: "Key Rule: Notice how Ridge's defenders are almost at the halfway line. This is called a 'high defensive line'!",
        };
      }
      if (audience === "analyst") {
        return {
          badge: "TACTICAL BREAKDOWN · ROLLING 300S WINDOW",
          title: club === "harbor" ? "Harbor FC low-block compactness under stress" : "Ridge United half-space overload & high recovery rate",
          desc: club === "harbor"
            ? "Harbor FC maintain a 4-2-3-1 low defensive block with an 18m vertical line distance. Despite Ridge's +41.0 Δ pressure surge, Harbor have made 6 defensive clearances."
            : "Pressure-v1 surged by +41.0 Δ (33.5 → 74.5). Ridge United generated 8 final-third entries and 3 high regains in 300s with PPDA at 6.4 passes/defensive action.",
          takeaway: "Field tilt: 78.2% attacking-third dominance. Expected threat generation (xT): +0.44.",
        };
      }
      if (audience === "broadcast") {
        return {
          badge: "TV COMMENTATOR TALKING POINT & LOWER-THIRD",
          title: "📺 GRAPHIC OVERLAY: RIDGE PRESSURE SPIKE (74.5) — 8 BOX ENTRIES IN 5 MINS",
          desc: "Commentary note: Ridge United have completely pinned Harbor into their penalty area. Notice how every second ball is won by C. Sterling in the center of the park.",
          takeaway: "Broadcast Statistic: 14 shots for Ridge United vs 2 for Harbor FC in the second half.",
        };
      }
      return {
        badge: "MOMENTUM ALERT · 74TH MINUTE",
        title: club === "harbor" ? "Harbor FC fighting through a relentless storm!" : "Ridge United turn up the heat at Ridge Park!",
        desc: club === "harbor"
          ? "Harbor FC are enduring wave after wave of attacks from Ridge United. The defensive unit is putting their bodies on the line to preserve the deficit."
          : "The home crowd is roaring! Ridge United are swarming Harbor FC with wave after wave of attacking pressure. Eight box entries in five minutes have the visitors on the ropes!",
        takeaway: "Momentum summary: Ridge United are in complete control of the match tempo.",
      };
    }

    // Spanish
    if (language === "es") {
      return {
        badge: "ALERTA DE PRESIÓN · MINUTO 74",
        title: "¡Ridge United asedia el área de Harbor FC!",
        desc: "El índice de presión aumentó +41.0 Δ. Ridge United acumula 8 penetraciones al área en 5 minutos, forzando a la defensa rival a despejar balones desesperadamente.",
        takeaway: "Dato clave: 78.2% de dominio territorial para los locales en esta fase.",
      };
    }

    // French
    if (language === "fr") {
      return {
        badge: "ALERTE INTENSITÉ · 74E MINUTE",
        title: "Ridge United accentue la pression à domicile !",
        desc: "L'indice de pression bondit de +41.0 Δ. Huit incursions dans la surface adverse en seulement 5 minutes mettent la défense d'Harbor FC en grande difficulté.",
        takeaway: "Statistique clé: 78,2 % d'occupation dans le dernier tiers du terrain.",
      };
    }

    // German
    if (language === "de") {
      return {
        badge: "DRUCKPHASE · 74. MINUTE",
        title: "Ridge United schnürt Harbor FC ein!",
        desc: "Der Pressure-Index klettert um +41,0 Δ. Acht Strafraumaktionen in fünf Minuten bringen die Abwehrreihe von Harbor FC an ihre Belastungsgrenze.",
        takeaway: "Wichtigste Zahl: 78,2% Feldüberlegenheit im Angriffsdrittel.",
      };
    }

    // Arabic
    if (language === "ar") {
      return {
        badge: "إنذار الضغط التكتيكي · الدقيقة 74",
        title: "ريدج يونايتد يفرض حصاراً هجومياً خانقاً!",
        desc: "ارتفع مؤشر الضغط بمقدار +41.0. سجّل ريدج يونايتد 8 اختراقات لمنطقة الجزاء خلال 5 دقائق فقط مع استعادة مذهلة للكرة.",
        takeaway: "الاستحواذ الهجومي: 78.2% في الثلث الأخير من الملعب.",
      };
    }

    // Japanese
    return {
      badge: "戦術プレッシャー急上昇 · 74分",
      title: "リッジ・ユナイテッドが圧倒的攻勢を展開！",
      desc: "プレッシャー指数が+41.0Δ急上昇。わずか5分間でペナルティエリア侵入8回を記録し、ハーバーFCを守備ブロックに釘付けにしています。",
      takeaway: "キー統計: アタッキングサード支配率78.2%。",
    };
  };

  const narrative = getNarrativeCopy();

  return (
    <main className="dashboard-grid">
      {/* Broadcast Overlay Component when activated */}
      <AnimatePresence>
        {broadcastOverlay && (
          <BroadcastOverlay
            score={events.some((e) => e.event_type === "GOAL" && e.minute >= 74) ? "2 - 0" : "1 - 0"}
            clock={`${matchClock.min}:${matchClock.sec < 10 ? `0${matchClock.sec}` : matchClock.sec}`}
            headline={narrative.title}
            whyItMatters={narrative.desc}
            pressureIndex={pressureIndex}
            onClose={() => setBroadcastOverlay(false)}
          />
        )}
      </AnimatePresence>

      {/* Automated Match Recap Modal */}
      <RecapModal
        isOpen={isRecapModalOpen}
        onClose={() => setIsRecapModalOpen(false)}
        matchId={matchId}
        score={events.some((e) => e.event_type === "GOAL" && e.minute >= 74) ? "2 - 0" : "1 - 0"}
      />

      {/* Top Breadcrumb & Live Engine Indicator */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "13px", fontWeight: 600, color: "var(--ink-muted)" }}>
          <Link href="/" style={{ color: "var(--ink-secondary)", textDecoration: "none" }}>Overview</Link>
          <span>/</span>
          <span style={{ color: "var(--pl-purple)", fontWeight: 700 }}>Live Match Console</span>
          <span>/</span>
          <span className="font-mono">{matchId}</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ fontSize: "12px", color: "var(--ink-muted)", fontWeight: 600 }}>
            Pipeline Latency: <strong style={{ color: "var(--pitch-emerald)" }}>0.88ms</strong>
          </span>
          <span style={{ fontSize: "12px", color: "var(--ink-muted)", fontWeight: 600 }}>
            Throughput: <strong style={{ color: "var(--pl-purple)" }}>1,137 ev/s</strong>
          </span>
          <Link href={`/match/${matchId}/analysis`} className="btn-emerald" style={{ padding: "6px 14px", fontSize: "12px" }}>
            <span>Tactical Pitch Radar ↗</span>
          </Link>
        </div>
      </div>

      {/* Personalization & Viewing Preference Studio Bar */}
      <PersonalizationBar
        audience={audience}
        setAudience={setAudience}
        club={club}
        setClub={setClub}
        language={language}
        setLanguage={setLanguage}
        selectedPlayerId={selectedPlayerId}
        setSelectedPlayerId={setSelectedPlayerId}
        broadcastOverlay={broadcastOverlay}
        setBroadcastOverlay={setBroadcastOverlay}
        onOpenRecapModal={() => setIsRecapModalOpen(true)}
      />

      {/* Main Scoreboard & Match Header */}
      <section className="match-header-card">
        {/* Home Team */}
        <div className="team-display">
          <div className="team-crest-badge crest-home">RU</div>
          <div>
            <div style={{ fontSize: "20px", fontWeight: 900, color: "var(--pl-purple)" }}>Ridge United</div>
            <div style={{ fontSize: "12px", color: "var(--pitch-emerald)", fontWeight: 700, textTransform: "uppercase" }}>
              Home • {club === "ridge" ? "⭐ YOUR FAVORITE CLUB" : "Dominating Territory"}
            </div>
          </div>
        </div>

        {/* Center Score & Live Clock */}
        <div className="scoreboard-center">
          <div className="match-timer">
            <span className="live-blip" />
            <span className="font-mono tabular-nums">
              {matchClock.min}:{matchClock.sec < 10 ? `0${matchClock.sec}` : matchClock.sec}
            </span>
          </div>
          <div className="score-digits tabular-nums">
            {events.some((e) => e.event_type === "GOAL" && e.minute >= 74) ? "2 - 0" : "1 - 0"}
          </div>
          <div style={{ fontSize: "11px", color: "var(--ink-muted)", fontWeight: 600, letterSpacing: "0.04em" }}>
            PREMIER LEAGUE · MATCHDAY 28
          </div>
        </div>

        {/* Away Team */}
        <div className="team-display" style={{ flexDirection: "row-reverse", textAlign: "right" }}>
          <div className="team-crest-badge crest-away">HF</div>
          <div>
            <div style={{ fontSize: "20px", fontWeight: 900, color: "var(--pl-purple)" }}>Harbor FC</div>
            <div style={{ fontSize: "12px", color: "var(--accent-blue)", fontWeight: 700, textTransform: "uppercase" }}>
              Away • {club === "harbor" ? "⭐ YOUR FAVORITE CLUB" : "Low Defensive Block"}
            </div>
          </div>
        </div>
      </section>

      {/* Operational Telemetry Cards (4 items) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
        <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "14px", padding: "18px 20px", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Pressure-v1 Index
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
            <span style={{ fontSize: "28px", fontWeight: 900, color: "var(--pl-purple)" }} className="tabular-nums">
              {pressureIndex.toFixed(1)}
            </span>
            <span style={{ fontSize: "12px", color: "var(--ink-dim)" }}>/ 100</span>
            <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--pitch-emerald)", marginLeft: "auto" }}>
              {pressureDelta} Δ Surge
            </span>
          </div>
          <div style={{ width: "100%", height: "6px", background: "var(--surface-subtle)", borderRadius: "999px", marginTop: "10px", overflow: "hidden" }}>
            <div style={{ width: `${pressureIndex}%`, height: "100%", background: "linear-gradient(90deg, var(--pitch-emerald), #00ff87)", borderRadius: "999px" }} />
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "14px", padding: "18px 20px", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Control vs. Chaos Rhythm
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
            <span style={{ fontSize: "28px", fontWeight: 900, color: "var(--pitch-emerald)" }} className="tabular-nums">
              68%
            </span>
            <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--ink-secondary)" }}>Controlled Siege</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "6px" }}>
            Transition volatility: 32% · Turnover gap: +7.2
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "14px", padding: "18px 20px", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Multi-Agent State
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "6px" }}>
            <span style={{ fontSize: "28px", fontWeight: 900, color: "var(--pl-purple)" }}>
              4 / 4
            </span>
            <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--pitch-emerald)", background: "rgba(16, 185, 129, 0.12)", padding: "2px 8px", borderRadius: "999px" }}>
              ACTIVE
            </span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "6px" }}>
            Auditor: 100% Verified · Bounded Repair: Ready
          </div>
        </div>

        <div style={{ background: "#fff", border: "1px solid var(--line)", borderRadius: "14px", padding: "18px 20px", boxShadow: "var(--shadow-sm)" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Pass & Speed Metrics
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "6px" }}>
            <span style={{ fontSize: "28px", fontWeight: 900, color: "var(--pl-purple)" }} className="tabular-nums font-mono">
              104.2
            </span>
            <span style={{ fontSize: "12px", color: "var(--pitch-emerald)", fontWeight: 700 }}>
              km/h Shot Speed
            </span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "6px" }}>
            Pass quality: 89.2% acc · Avg distance 22.4m
          </div>
        </div>
      </div>

      {/* Main 3-Column Operational Grid */}
      <div className="ops-three-columns">
        {/* Left Column: Pressure Momentum Area Chart */}
        <div className="dash-panel">
          <div className="panel-header-row">
            <div>
              <h2 className="panel-heading-text">Pressure Index Waveform (0 - 90&apos;)</h2>
              <p style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "2px" }}>
                Rolling 5-minute deterministic intensity metric (Pressure-v1)
              </p>
            </div>
            <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--pitch-emerald)", background: "rgba(16,185,129,0.1)", padding: "4px 8px", borderRadius: "6px" }}>
              SURGE LINE &gt; 60.0
            </span>
          </div>

          {/* SVG Momentum Curve Chart */}
          <div style={{ position: "relative", width: "100%", height: "230px", marginTop: "10px" }}>
            <svg viewBox="0 0 500 200" style={{ width: "100%", height: "100%", overflow: "visible" }}>
              <defs>
                <linearGradient id="pressureGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#059669" stopOpacity="0.45" />
                  <stop offset="60%" stopColor="#10b981" stopOpacity="0.15" />
                  <stop offset="100%" stopColor="#ffffff" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="0" y1="40" x2="500" y2="40" stroke="rgba(226, 232, 240, 0.8)" strokeDasharray="3 3" />
              <text x="5" y="36" fill="var(--ink-dim)" fontSize="10" fontWeight="600">80 High</text>
              <line x1="0" y1="80" x2="500" y2="80" stroke="rgba(225, 29, 72, 0.3)" strokeDasharray="4 4" />
              <text x="5" y="76" fill="var(--accent-crimson)" fontSize="10" fontWeight="700">60 Surge Trigger</text>
              <line x1="0" y1="140" x2="500" y2="140" stroke="rgba(226, 232, 240, 0.8)" strokeDasharray="3 3" />
              <text x="5" y="136" fill="var(--ink-dim)" fontSize="10" fontWeight="600">30 Calm</text>

              {/* Area Fill */}
              <path
                d="M 20 160 Q 60 140 100 130 T 200 120 T 300 90 T 380 40 T 440 30 T 480 70 L 480 180 L 20 180 Z"
                fill="url(#pressureGradient)"
              />

              {/* Curve Stroke */}
              <path
                d="M 20 160 Q 60 140 100 130 T 200 120 T 300 90 T 380 40 T 440 30 T 480 70"
                fill="none"
                stroke="var(--pitch-emerald)"
                strokeWidth="3.5"
                strokeLinecap="round"
              />

              {/* Current Match Point Pin (Minute 74) */}
              <circle cx="395" cy="46" r="6" fill="var(--pl-purple)" stroke="#ffffff" strokeWidth="2.5" />
              <circle cx="395" cy="46" r="12" fill="none" stroke="var(--pitch-emerald)" strokeWidth="2" opacity="0.6">
                <animate attributeName="r" values="6;16;6" dur="2s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0.8;0;0.8" dur="2s" repeatCount="indefinite" />
              </circle>
              <rect x="360" y="10" width="70" height="24" rx="6" fill="var(--pl-purple)" />
              <text x="395" y="26" textAnchor="middle" fill="#ffffff" fontSize="11" fontWeight="800">
                {pressureIndex.toFixed(1)} · 74&apos;
              </text>
            </svg>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--ink-muted)", fontWeight: "600", marginTop: "4px" }}>
            <span>Kickoff (0&apos;)</span>
            <span>Half Time (45&apos;)</span>
            <span style={{ color: "var(--pl-purple)", fontWeight: 800 }}>Now ({matchClock.min}&apos;)</span>
            <span>Full Time (90&apos;)</span>
          </div>

          {/* Quick Scenario Injector Dock */}
          <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid var(--line)" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
              Development Fixtures Injector
            </div>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={() => handleInjectFixture("pressure")}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 12px", background: activeFixture === "pressure" ? "rgba(5, 150, 105, 0.1)" : "#fff" }}
              >
                ⚡ Pressure Surge (+41.0 Δ)
              </button>
              <button
                type="button"
                onClick={() => handleInjectFixture("goal")}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 12px", background: activeFixture === "goal" ? "rgba(56, 0, 60, 0.1)" : "#fff" }}
              >
                ⚽ Goal Sequence
              </button>
              <button
                type="button"
                onClick={() => handleInjectFixture("card")}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 12px" }}
              >
                🟨 Booking
              </button>
              <button
                type="button"
                onClick={() => handleInjectFixture("reset")}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "6px 12px", color: "var(--ink-muted)" }}
              >
                ↺ Reset
              </button>
            </div>
            {fixtureStatus && (
              <div style={{ fontSize: "12px", color: "var(--pitch-emerald)", fontWeight: 700, marginTop: "8px" }}>
                ✓ {fixtureStatus}
              </div>
            )}
          </div>
        </div>

        {/* Center Column: Multi-Audience Narrative View */}
        <div className="dash-panel">
          <div className="panel-header-row">
            <div>
              <h2 className="panel-heading-text">Audience-Tailored Insights</h2>
              <p style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "2px" }}>
                {language.toUpperCase()} Narration · {club.toUpperCase()} Lens
              </p>
            </div>
          </div>

          {/* Narrative Content Body */}
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ background: "rgba(5, 150, 105, 0.08)", borderLeft: "4px solid var(--pitch-emerald)", padding: "14px", borderRadius: "8px" }}>
              <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--pitch-emerald)", textTransform: "uppercase" }}>
                {narrative.badge}
              </div>
              <h3 style={{ fontSize: "18px", fontWeight: 800, color: "var(--pl-purple)", marginTop: "4px" }}>
                {narrative.title}
              </h3>
              <p style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--ink-secondary)", marginTop: "6px" }}>
                {narrative.desc}
              </p>
            </div>

            <div style={{ background: "var(--surface-subtle)", padding: "12px 14px", borderRadius: "10px", fontSize: "12px", color: "var(--ink-secondary)" }}>
              <strong style={{ color: "var(--pl-purple)" }}>Perspective: </strong> {narrative.takeaway}
            </div>
          </div>

          {/* Evidence Auditor Stamp */}
          <div style={{ marginTop: "auto", background: "rgba(5, 150, 105, 0.05)", border: "1px solid rgba(5, 150, 105, 0.2)", borderRadius: "10px", padding: "12px 14px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--pitch-emerald)" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--pitch-emerald)", letterSpacing: "0.04em" }}>
                  EVIDENCE AUDITOR VERIFIED
                </span>
              </div>
              <span className="font-mono" style={{ fontSize: "10px", color: "var(--ink-muted)" }}>
                Audited in 0.12ms
              </span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--ink-secondary)", marginTop: "4px" }}>
              Cited Canonical Events: <span className="font-mono">ev_097, ev_098, ev_099, ev_100, ev_101</span>. Zero hallucinations detected.
            </div>
          </div>
        </div>

        {/* Right Column: Live Event Stream & Multi-Agent Execution */}
        <div className="dash-panel">
          <div className="panel-header-row">
            <div>
              <h2 className="panel-heading-text">Live Ingestion Ledger</h2>
              <p style={{ fontSize: "12px", color: "var(--ink-muted)", marginTop: "2px" }}>
                Canonical event stream with coordinate tracking
              </p>
            </div>
            <span className="live-pill">
              <span className="live-blip" />
              <span>LIVE</span>
            </span>
          </div>

          {/* Live Events Stream */}
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "280px", overflowY: "auto", paddingRight: "4px" }}>
            {events.map((ev) => (
              <div
                key={ev.event_id}
                style={{
                  background: ev.event_type === "GOAL" ? "rgba(5, 150, 105, 0.1)" : "var(--surface-subtle)",
                  border: ev.event_type === "GOAL" ? "1px solid var(--pitch-emerald)" : "1px solid var(--line)",
                  borderRadius: "10px",
                  padding: "10px 12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "4px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span className="match-timer" style={{ padding: "2px 6px", fontSize: "10px" }}>
                      {ev.minute}&apos;{ev.second}&quot;
                    </span>
                    <span style={{ fontSize: "12px", fontWeight: 800, color: ev.team_id.includes("ridge") ? "var(--pitch-emerald)" : "var(--accent-blue)" }}>
                      {ev.event_type}
                    </span>
                  </div>
                  {ev.x != null && ev.y != null && (
                    <span className="font-mono" style={{ fontSize: "10px", color: "var(--ink-dim)" }}>
                      ({ev.x}, {ev.y})
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "11px", color: "var(--ink-secondary)" }}>
                  {ev.detail}
                </div>
              </div>
            ))}
          </div>

          {/* Multi-Agent Latency Telemetry */}
          <div style={{ marginTop: "auto", paddingTop: "14px", borderTop: "1px solid var(--line)" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "8px" }}>
              Agent Pipeline Execution
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", fontSize: "11px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", background: "var(--surface-subtle)", padding: "6px 8px", borderRadius: "6px" }}>
                <span>Match Analyst:</span>
                <strong className="font-mono" style={{ color: "var(--pl-purple)" }}>0.24ms</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", background: "var(--surface-subtle)", padding: "6px 8px", borderRadius: "6px" }}>
                <span>Tactical Analyst:</span>
                <strong className="font-mono" style={{ color: "var(--pitch-emerald)" }}>0.31ms</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", background: "var(--surface-subtle)", padding: "6px 8px", borderRadius: "6px" }}>
                <span>Narrative Producer:</span>
                <strong className="font-mono" style={{ color: "var(--accent-blue)" }}>0.21ms</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", background: "var(--surface-subtle)", padding: "6px 8px", borderRadius: "6px" }}>
                <span>Evidence Auditor:</span>
                <strong className="font-mono" style={{ color: "var(--accent-crimson)" }}>0.12ms</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
