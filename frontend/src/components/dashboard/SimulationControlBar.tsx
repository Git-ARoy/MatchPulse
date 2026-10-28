"use client";

import { useEffect, useState, useCallback } from "react";
import {
  PlayRegular,
  PauseRegular,
  FastForwardRegular,
  ArrowResetRegular,
  FlashRegular,
  DismissCircleRegular,
  TargetRegular,
} from "@fluentui/react-icons";

interface SimulationControlBarProps {
  apiUrl: string;
  matchId: string;
  onRefreshMatch: () => void;
}

export function SimulationControlBar({ apiUrl, matchId, onRefreshMatch }: SimulationControlBarProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [eventsCount, setEventsCount] = useState(0);
  const [phase, setPhase] = useState("not_started");
  const [actionPending, setActionPending] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Poll simulation status periodically
  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/simulation/status?match_id=${encodeURIComponent(matchId)}`);
      if (res.ok) {
        const data = await res.json();
        const snap = data.snapshot;
        if (snap) {
          setIsRunning(!snap.is_paused);
          setSpeed(snap.speed_multiplier ?? 1.0);
          setEventsCount(snap.event_counter ?? 0);
          setPhase(snap.phase ?? "not_started");
        }
      }
    } catch {
      // Background probe silent error
    }
  }, [apiUrl, matchId]);

  useEffect(() => {
    void fetchStatus();
    const interval = setInterval(() => void fetchStatus(), 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleTogglePlay = async () => {
    setActionPending(true);
    try {
      const endpoint = isRunning ? "/api/v1/simulation/pause" : "/api/v1/simulation/start";
      const res = await fetch(`${apiUrl}${endpoint}?match_id=${encodeURIComponent(matchId)}`, {
        method: "POST",
      });
      if (res.ok) {
        setIsRunning(!isRunning);
        setFeedback(isRunning ? "Simulation paused" : "Autonomous simulation started");
        setTimeout(() => setFeedback(null), 2500);
        onRefreshMatch();
      } else {
        const errData = await res.json().catch(() => null);
        const errMsg = errData?.message || errData?.detail || `Simulation error (${res.status})`;
        setFeedback(errMsg);
        setTimeout(() => setFeedback(null), 3000);
      }
    } catch {
      setFeedback("Simulation action failed");
      setTimeout(() => setFeedback(null), 2500);
    } finally {
      setActionPending(false);
    }
  };

  const handleSetSpeed = async (multiplier: number) => {
    setActionPending(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/simulation/speed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ multiplier }),
      });
      if (res.ok) {
        setSpeed(multiplier);
        setFeedback(`Speed set to ${multiplier}x`);
        setTimeout(() => setFeedback(null), 2000);
      } else {
        setFeedback("Failed to update speed");
        setTimeout(() => setFeedback(null), 2000);
      }
    } catch {
      setFeedback("Speed change failed");
      setTimeout(() => setFeedback(null), 2000);
    } finally {
      setActionPending(false);
    }
  };

  const handleInject = async (action: string) => {
    setActionPending(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/simulation/inject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        setFeedback(`Injected ${action.replace("_", " ")} moment into live simulation!`);
        setTimeout(() => setFeedback(null), 3000);
        onRefreshMatch();
      } else {
        setFeedback(`Failed to inject ${action}`);
        setTimeout(() => setFeedback(null), 2500);
      }
    } catch {
      setFeedback("Scenario injection failed");
      setTimeout(() => setFeedback(null), 2500);
    } finally {
      setActionPending(false);
    }
  };

  const handleReset = async () => {
    setActionPending(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/simulation/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ matchup_id: matchId }),
      });
      if (res.ok) {
        setIsRunning(false);
        setFeedback("Simulation match reset");
        setTimeout(() => setFeedback(null), 2500);
        onRefreshMatch();
      } else {
        setFeedback("Failed to reset match");
        setTimeout(() => setFeedback(null), 2500);
      }
    } catch {
      setFeedback("Reset action failed");
      setTimeout(() => setFeedback(null), 2500);
    } finally {
      setActionPending(false);
    }
  };

  return (
    <div className="sim-control-bar" role="region" aria-label="Autonomous match simulation controller">
      {/* Status & Telemetry Group */}
      <div className="sim-status-group">
        <span className={`sim-indicator ${isRunning ? "live" : "idle"}`} />
        <div className="sim-info-block">
          <span className="sim-title">
            PHYSICS SIMULATOR <strong>({isRunning ? "10Hz LIVE STREAM" : "READY"})</strong>
          </span>
          <span className="sim-meta">
            Phase: <strong>{phase.replace("_", " ")}</strong> · Dispatched Events: <strong>{eventsCount}</strong>
          </span>
        </div>
      </div>

      {/* Primary Actions Group */}
      <div className="sim-actions-group">
        <button
          type="button"
          className={`sim-btn-primary ${isRunning ? "active" : ""}`}
          onClick={handleTogglePlay}
          disabled={actionPending}
        >
          {isRunning ? <PauseRegular /> : <PlayRegular />}
          <span>{isRunning ? "Pause Sim" : "Start Live Sim"}</span>
        </button>

        {/* Speed Selector */}
        <div className="sim-speed-selector">
          <FastForwardRegular />
          {[1.0, 2.0, 5.0, 10.0].map((s) => (
            <button
              key={s}
              type="button"
              className={`speed-pill ${speed === s ? "selected" : ""}`}
              onClick={() => void handleSetSpeed(s)}
              disabled={actionPending}
            >
              {s}x
            </button>
          ))}
        </div>

        {/* Live Scenario Injectors */}
        <div className="sim-inject-group">
          <button
            type="button"
            className="sim-inject-btn penalty"
            title="Inject Penalty Scenario"
            onClick={() => void handleInject("penalty")}
            disabled={actionPending}
          >
            <FlashRegular />
            <span>+Penalty</span>
          </button>

          <button
            type="button"
            className="sim-inject-btn card"
            title="Inject Red Card Scenario"
            onClick={() => void handleInject("red_card")}
            disabled={actionPending}
          >
            <DismissCircleRegular />
            <span>+Red Card</span>
          </button>

          <button
            type="button"
            className="sim-inject-btn freekick"
            title="Inject Free Kick Scenario"
            onClick={() => void handleInject("free_kick")}
            disabled={actionPending}
          >
            <TargetRegular />
            <span>+Free Kick</span>
          </button>

          <button
            type="button"
            className="sim-btn-icon"
            title="Reset Simulation Match"
            onClick={handleReset}
            disabled={actionPending}
          >
            <ArrowResetRegular />
          </button>
        </div>
      </div>

      {feedback && (
        <div className="sim-feedback-toast" role="status">
          {feedback}
        </div>
      )}
    </div>
  );
}
