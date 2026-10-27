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
      className="broadcast-lower-third-overlay"
    >
      <div className="overlay-inner-row">
        {/* Left: Official Premier League Studio Score Bug */}
        <div className="overlay-bug-group">
          {/* PL Lion Brand Badge */}
          <div className="overlay-lion-crest" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#00FF87" />
            </svg>
          </div>

          <div className="overlay-score-details">
            <div className="overlay-badge-meta">
              <span className="overlay-pl-label">PL PRODUCTIONS · LIVE OVERLAY</span>
              <span className="overlay-feed-label">• 1080p50 SYNC</span>
            </div>
            <div className="overlay-match-scoreline">
              <span className="overlay-score-text">RIDGE {score} HARBOR</span>
              <span className="overlay-clock-chip">⏱ {clock}</span>
            </div>
          </div>
        </div>

        {/* Center: Live Lower-Third Machine-Readable Graphic Copy */}
        <div className="overlay-center-narrative">
          <div className="overlay-momentum-tag">
            MOMENTUM ALERT (PRESSURE-V1: {pressureIndex.toFixed(1)})
          </div>
          <div className="overlay-headline-text" title={headline}>
            {headline}
          </div>
          <div className="overlay-sub-text" title={whyItMatters}>
            {whyItMatters}
          </div>
        </div>

        {/* Right: Broadcast Telemetry Badges & Close Button */}
        <div className="overlay-right-actions">
          <div className="overlay-telemetry-badges">
            <div className="telemetry-chip speed-chip">
              <div className="telemetry-label">SHOT SPEED</div>
              <div className="telemetry-val">{shotSpeedKph} km/h</div>
            </div>

            <div className="telemetry-chip difficulty-chip">
              <div className="telemetry-label">PASS DIFFICULTY</div>
              <div className="telemetry-val">{passDifficulty}/100</div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close Broadcast Overlay"
            className="overlay-close-button"
          >
            ✕
          </button>
        </div>
      </div>
    </motion.div>
  );
}
