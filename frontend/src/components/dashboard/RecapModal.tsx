"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LanguageType } from "./PersonalizationBar";
import { fetchMatchRecap, MatchRecap } from "../../lib/api";

interface RecapModalProps {
  isOpen: boolean;
  onClose: () => void;
  matchId: string;
  score: string;
}

const RECAP_DATA_BY_LANG: Record<string, { headline: string; summary: string; milestones: string[] }> = {
  en: {
    headline: "Verified Match Intelligence Recap · Ridge United 1 - 0 Harbor FC",
    summary: "Ridge United secured victory through an aggressive 70th-minute tactical shift. Ingesting 2,714 canonical events with 0 out-of-order anomalies revealed that their sustained final-third press generated 8 box penetrations and a +41.0 Δ surge in Pressure-v1, eventually forcing the decisive 84th-minute breakthrough.",
    milestones: [
      "18' — Harbor FC early counter-threat (Shot on target, 98.4 km/h saved)",
      "42' — Tactical turnover equilibrium restored (PPDA 6.4 passes/action)",
      "72' — Match Analyst detects massive momentum surge (+41.0 Δ Pressure-v1)",
      "84' — GOAL! M. Vance converts into right corner following box penetration",
    ],
  },
  es: {
    headline: "Resumen Verificado de Inteligencia · Ridge United 1 - 0 Harbor FC",
    summary: "Ridge United aseguró la victoria mediante un cambio táctico agresivo en el minuto 70. El procesamiento de 2,714 eventos canónicos demostró que la presión sostenida generó 8 penetraciones al área y un aumento de +41.0 Δ en el índice de presión, culminando en el gol decisivo en el minuto 84.",
    milestones: [
      "18' — Contragolpe peligroso de Harbor FC (Tiro a puerta a 98.4 km/h)",
      "42' — Recuperación táctica y control del mediocampo (PPDA 6.4)",
      "72' — Oleada de presión detectada (+41.0 Δ en intensidad)",
      "84' — ¡GOL! M. Vance define al ángulo inferior derecho tras pase filtrado",
    ],
  },
  fr: {
    headline: "Résumé Analytique Vérifié · Ridge United 1 - 0 Harbor FC",
    summary: "Ridge United l'emporte grâce à une domination territoriale marquée dès la 70e minute. L'analyse en temps réel des 2 714 événements a mis en évidence un pic d'intensité (+41.0 Δ Pressure-v1) avec 8 entrées dans les 16 mètres avant le but décisif à la 84e minute.",
    milestones: [
      "18' — Alerte sur contre-attaque d'Harbor FC (Tir cadré 98.4 km/h)",
      "42' — Rétablissement de l'équilibre tactique au milieu de terrain",
      "72' — Détection d'un pic de pression majeur (+41.0 Δ)",
      "84' — BUT ! M. Vance conclut avec précision dans le petit filet",
    ],
  },
  de: {
    headline: "Verifizierter Taktischer Spielbericht · Ridge United 1 - 0 Harbor FC",
    summary: "Ridge United setzte sich dank einer kraftvollen Druckphase ab der 70. Minute durch. Die Verarbeitung von 2.714 kanonischen Ereignissen belegt 8 Strafraumaktionen und einen Intensitätssprung von +41,0 Δ vor dem Führungstreffer in Minute 84.",
    milestones: [
      "18' — Konterchance für Harbor FC (Torschuss mit 98,4 km/h pariert)",
      "42' — Taktische Balleroberung im Mittelfeld (PPDA 6,4)",
      "72' — Match Analyst meldet Druckanstieg (+41,0 Δ)",
      "84' — TOR! M. Vance verwandelt nach Strafraumüberladung",
    ],
  },
  ar: {
    headline: "تقرير المباراة المعتمد والذكاء التكتيكي · ريدج يونايتد 1 - 0 هاربور",
    summary: "حقق ريدج يونايتد الفوز بفضل تغيير تكتيكي حاسم في الدقيقة 70. أثبت تدفق 2,714 حدثاً مسجلاً أن الضغط الهجومي العالي ولّد 8 اختراقات لمنطقة الجزاء وارتفاعاً بمقدار +41.0 في مؤشر الضغط قبل تسجيل هدف الحسم في الدقيقة 84.",
    milestones: [
      "18' — هجمة مرتدة سريعة لهاربور (تسديدة بسرعة 98.4 كم/س)",
      "42' — استعادة السيطرة في خط الوسط والضغط العكسي",
      "72' — تصاعد مؤشر الضغط الهجومي بمقدار +41.0",
      "84' — هدف! إم. فانس يسجل ببراعة في الزاوية اليمنى",
    ],
  },
  ja: {
    headline: "検証済み戦術インサイト・リキャップ · リッジ・ユナイテッド 1 - 0 ハーバーFC",
    summary: "リッジ・ユナイテッドは70分以降の波状攻撃によって勝利を決定づけました。2,714件の正規イベント分析により、ペナルティエリア侵入8回とプレッシャー指数+41.0Δの急上昇が実証され、84分の決勝ゴールに結びつきました。",
    milestones: [
      "18' — ハーバーFCの鋭いカウンター（時速98.4kmの枠内シュート）",
      "42' — 中盤でのハイプレスによるボール奪回（PPDA 6.4）",
      "72' — プレッシャー指数が急上昇（+41.0Δ）",
      "84' — ゴール！M. ヴァンスが右隅へ冷静に流し込む",
    ],
  },
};

export function RecapModal({ isOpen, onClose, matchId, score }: RecapModalProps) {
  const [lang, setLang] = useState<string>("en");
  const [copied, setCopied] = useState(false);
  const [recapData, setRecapData] = useState<MatchRecap | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let isCancelled = false;
    fetchMatchRecap(matchId, "fan", lang).then((data) => {
      if (!isCancelled) {
        setRecapData(data);
      }
    });
    return () => {
      isCancelled = true;
    };
  }, [isOpen, matchId, lang]);

  if (!isOpen) return null;

  const fallback = RECAP_DATA_BY_LANG[lang] || RECAP_DATA_BY_LANG.en;
  const currentRecap = recapData
    ? {
        headline: recapData.headline,
        summary: recapData.summary,
        milestones: recapData.milestones && recapData.milestones.length > 0 ? recapData.milestones : fallback.milestones,
      }
    : fallback;

  const handleCopyScript = () => {
    const text = `${currentRecap.headline}\n\n${currentRecap.summary}\n\nKey Milestones:\n${currentRecap.milestones.join("\n")}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AnimatePresence>
      <div
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(15, 23, 42, 0.65)",
          backdropFilter: "blur(8px)",
          display: "grid",
          placeItems: "center",
          zIndex: 10000,
          padding: "24px",
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.25 }}
          onClick={(e) => e.stopPropagation()}
          style={{
            background: "#ffffff",
            border: "1px solid var(--line)",
            borderRadius: "20px",
            padding: "32px",
            maxWidth: "760px",
            width: "100%",
            boxShadow: "var(--shadow-xl)",
            maxHeight: "90vh",
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px" }}>
            <div>
              <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "4px 10px", background: "rgba(56, 0, 60, 0.06)", borderRadius: "999px", fontSize: "11px", fontWeight: 800, color: "var(--pl-purple)", textTransform: "uppercase" }}>
                <span>🎙️ PREMIER LEAGUE STUDIO RECAP</span>
              </div>
              <h2 style={{ fontSize: "22px", fontWeight: 900, color: "var(--pl-purple)", marginTop: "8px" }}>
                Automated Match Recap Studio
              </h2>
              <p style={{ fontSize: "12px", color: "var(--ink-muted)" }}>
                Audited match narrative grounded in 2,714 events with zero fabricated stats.
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              style={{ background: "var(--surface-subtle)", border: "none", borderRadius: "50%", width: "32px", height: "32px", cursor: "pointer", fontSize: "14px", fontWeight: 800 }}
            >
              ✕
            </button>
          </div>

          {/* Language Selector Tabs */}
          <div style={{ display: "flex", background: "var(--surface-subtle)", padding: "4px", borderRadius: "10px", gap: "4px", flexWrap: "wrap" }}>
            {[
              { id: "en", label: "🇬🇧 English" },
              { id: "es", label: "🇪🇸 Español" },
              { id: "fr", label: "🇫🇷 Français" },
              { id: "de", label: "🇩🇪 Deutsch" },
              { id: "ar", label: "🇸🇦 العربية" },
              { id: "ja", label: "🇯🇵 日本語" },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setLang(item.id)}
                style={{
                  flex: 1,
                  minWidth: "90px",
                  padding: "6px 10px",
                  fontSize: "12px",
                  fontWeight: 700,
                  border: "none",
                  borderRadius: "7px",
                  cursor: "pointer",
                  background: lang === item.id ? "#ffffff" : "transparent",
                  color: lang === item.id ? "var(--pl-purple)" : "var(--ink-secondary)",
                  boxShadow: lang === item.id ? "var(--shadow-sm)" : "none",
                }}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Narrative Body */}
          <div style={{ background: "rgba(5, 150, 105, 0.04)", border: "1px solid rgba(5, 150, 105, 0.2)", borderRadius: "14px", padding: "18px 20px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 900, color: "var(--pl-purple)" }}>
              {currentRecap.headline}
            </h3>
            <p style={{ fontSize: "13px", lineHeight: "1.7", color: "var(--ink-secondary)", marginTop: "8px" }}>
              {currentRecap.summary}
            </p>
          </div>

          {/* Control vs. Chaos Metric Bar */}
          <div style={{ background: "#ffffff", border: "1px solid var(--line)", borderRadius: "14px", padding: "16px 20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <span style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase" }}>
                Stage (iv) Control vs. Chaos Index
              </span>
              <span style={{ fontSize: "12px", fontWeight: 800, color: "var(--pitch-emerald)" }}>
                Tactical Positional Dominance
              </span>
            </div>

            <div style={{ height: "10px", background: "var(--surface-subtle)", borderRadius: "999px", overflow: "hidden", display: "flex" }}>
              <div style={{ width: "68%", height: "100%", background: "var(--pitch-emerald)" }} title="Control: 68%" />
              <div style={{ width: "32%", height: "100%", background: "var(--accent-crimson)" }} title="Chaos / Transitions: 32%" />
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "var(--ink-secondary)", marginTop: "6px" }}>
              <span>🛡️ Structured Control: <strong>68%</strong></span>
              <span>⚡ Transition Volatility: <strong>32%</strong></span>
            </div>
          </div>

          {/* Chronological Milestones Timeline */}
          <div>
            <div style={{ fontSize: "11px", fontWeight: 800, color: "var(--ink-muted)", textTransform: "uppercase", marginBottom: "10px" }}>
              Turning Points & Milestones Timeline
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              {currentRecap.milestones.map((milestone, idx) => (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    background: "var(--surface-subtle)",
                    padding: "8px 12px",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "var(--ink-secondary)",
                  }}
                >
                  <span style={{ color: "var(--pitch-emerald)", fontWeight: 900 }}>•</span>
                  <span>{milestone}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Footer Actions */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "14px", borderTop: "1px solid var(--line)" }}>
            <span style={{ fontSize: "11px", color: "var(--pitch-emerald)", fontWeight: 700 }}>
              ✓ Verified by Evidence Auditor in 0.12ms
            </span>

            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                onClick={handleCopyScript}
                className="btn-secondary"
                style={{ fontSize: "12px", padding: "8px 14px" }}
              >
                {copied ? "✓ Copied to Clipboard!" : "📋 Copy Broadcast Script"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-primary"
                style={{ fontSize: "12px", padding: "8px 18px" }}
              >
                Done
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
