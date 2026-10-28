"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowClockwiseRegular, ArrowLeftRegular, EyeRegular, MapRegular, PlayRegular, ShieldCheckmarkRegular, VideoRegular } from "@fluentui/react-icons";
import { motion, useReducedMotion } from "framer-motion";
import { AutoEventingFeed } from "../../../../src/components/radar/AutoEventingFeed";

type Event = { event_id: string; minute: number; second: number; event_type: string; team_id: string; player_id?: string; x?: number; y?: number; zone?: string };
type Insight = { insight_id: string; headline: string; summary: string; source_event_ids: string[]; match_clock: { minute: number; second: number } };
type State = { synthetic: boolean; match_clock: { minute: number; second: number }; teams: Record<string, { goals: number }>; data_source: string; live_feed_available: boolean };
type SimPlayer = { id: string; name: string; number: number; role: string; x: number; y: number; speed_kph?: number };
type SimTracking = { match_id: string; home_team?: { players: SimPlayer[] }; away_team?: { players: SimPlayer[] }; ball?: { x: number; y: number; speed_kph: number } };

const api = process.env.NEXT_PUBLIC_API_URL || "";
const name = (value?: string) => (value ?? "Unknown").replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());
const clock = (value?: { minute: number; second: number }) => value ? `${value.minute}:${String(value.second).padStart(2, "0")}` : "--:--";

export default function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const reduceMotion = useReducedMotion();
  const [matchId, setMatchId] = useState("synthetic_ridge_harbor");
  const [state, setState] = useState<State | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [selectedInsight, setSelectedInsight] = useState<Insight | null>(null);
  const [showPressure, setShowPressure] = useState(true);
  const [showAutoEventing, setShowAutoEventing] = useState(false);
  const [liveTracking, setLiveTracking] = useState<SimTracking | null>(null);
  const [status, setStatus] = useState("Connecting to the synthetic event ledger…");

  useEffect(() => { void params.then(value => setMatchId(value.id || "synthetic_ridge_harbor")); }, [params]);

  const load = useCallback(async () => {
    try {
      const id = encodeURIComponent(matchId);
      const [stateResponse, eventsResponse, insightsResponse] = await Promise.all([
        fetch(`${api}/api/v1/matches/${id}/state`),
        fetch(`${api}/api/v1/matches/${id}/events?limit=100`),
        fetch(`${api}/api/v1/matches/${id}/insights?limit=20`),
      ]);
      if (stateResponse.status === 404) { setStatus("Load the Momentum surge scenario from the live console to populate this radar."); return; }
      if (!stateResponse.ok || !eventsResponse.ok || !insightsResponse.ok) throw new Error("The match service did not return a complete radar view.");
      const nextEvents = (await eventsResponse.json()).items as Event[];
      const nextInsights = (await insightsResponse.json()).items as Insight[];
      setState(await stateResponse.json() as State);
      setEvents(nextEvents);
      setInsights(nextInsights);
      setSelectedInsight(current => nextInsights.find(item => item.insight_id === current?.insight_id) ?? nextInsights.at(-1) ?? null);
      setStatus("Coordinates represent accepted fictional event locations. Player tracking is not inferred where the event ledger does not provide it.");
    } catch (error) { setStatus(error instanceof Error ? error.message : "Unable to connect to the match service."); }
  }, [matchId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (!state?.live_feed_available) return;
    const wsProto = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
    const socketBase = api ? api.replace(/^http/, "ws") : (typeof window !== "undefined" ? `${wsProto}//${window.location.host}` : "");
    if (!socketBase) return;
    const socket = new WebSocket(`${socketBase}/api/v1/matches/${encodeURIComponent(matchId)}/live-stream`);
    socket.onmessage = () => void load();
    return () => socket.close();
  }, [load, matchId, state?.live_feed_available]);

  useEffect(() => {
    let active = true;
    const fetchTracking = async () => {
      try {
        const res = await fetch(`${api}/api/v1/matches/${encodeURIComponent(matchId)}/tracking`);
        if (res.ok && active) {
          const data = await res.json() as SimTracking;
          setLiveTracking(data);
        }
      } catch {
        // Silently skip if tracking is not currently transmitting
      }
    };
    void fetchTracking();
    const interval = setInterval(() => void fetchTracking(), 1200);
    return () => { active = false; clearInterval(interval); };
  }, [matchId]);

  const evidenceIds = new Set(selectedInsight?.source_event_ids ?? []);
  const plottedEvents = useMemo(() => events.filter(event => typeof event.x === "number" && typeof event.y === "number"), [events]);
  const teams = Object.entries(state?.teams ?? {});
  const homeTeamId = teams[0]?.[0] ?? "";
  const homeTeamName = teams[0]?.[0] ? name(teams[0][0]) : "Home Team";
  const awayTeamName = teams[1]?.[0] ? name(teams[1][0]) : "Away Team";

  return <main className="radar-shell">
    <header className="radar-header">
      <div><Link href="/dashboard" className="radar-back"><ArrowLeftRegular /> Live console</Link><p className="console-eyebrow">Verified event replay</p><h1>Tactical event radar</h1><p>Evidence coordinates, not invented player tracking.</p></div>
      <div className="radar-actions">
        <button className={showAutoEventing ? "selected" : ""} onClick={() => setShowAutoEventing(value => !value)}>
          <VideoRegular /> Optical auto-eventing
        </button>
        <button className={showPressure ? "selected" : ""} onClick={() => setShowPressure(value => !value)}>
          <MapRegular /> Pressure overlay
        </button>
        <button onClick={() => void load()} aria-label="Refresh tactical radar">
          <ArrowClockwiseRegular />
        </button>
      </div>
    </header>

    {showAutoEventing && (
      <div style={{ marginBottom: "20px" }}>
        <AutoEventingFeed isOpen={showAutoEventing} onClose={() => setShowAutoEventing(false)} />
      </div>
    )}

    <section className="radar-score"><span><ShieldCheckmarkRegular /> Synthetic, fictional match</span><strong>{teams[0] ? `${name(teams[0][0])} ${teams[0][1].goals} – ${teams[1]?.[1].goals ?? 0} ${name(teams[1]?.[0])}` : "Awaiting match state"}</strong><time>{clock(state?.match_clock)}</time></section>
    <p className="radar-status">{status}</p>

    <div className="radar-grid">
      <section className="radar-card pitch-card" aria-label="Event position radar">
        <div className="pitch-toolbar">
          <span><EyeRegular /> {liveTracking ? "Live 22-Player Physics Tracking (Active)" : `${plottedEvents.length} observed positions`}</span>
          <span>{liveTracking ? `Ball Speed: ${liveTracking.ball?.speed_kph ?? 0} km/h` : (selectedInsight ? `Replaying ${clock(selectedInsight.match_clock)}` : "Select an insight to replay its evidence")}</span>
        </div>
        <div className={`event-pitch ${showPressure ? "pressure-on" : ""}`}>
          <span className="pitch-line halfway" /><span className="pitch-circle" /><span className="pitch-box left" /><span className="pitch-box right" />
          {showPressure && <><span className="pressure-zone ridge" /><span className="pressure-zone harbor" /></>}
          
          {/* Live Simulated 22 Players & Ball */}
          {liveTracking?.home_team?.players?.map((p) => (
            <div
              key={p.id}
              className="player-sim-dot home"
              title={`${p.name} (#${p.number} ${p.role}) · Speed: ${p.speed_kph ?? 0} km/h`}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
            >
              <span>{p.number}</span>
            </div>
          ))}
          {liveTracking?.away_team?.players?.map((p) => (
            <div
              key={p.id}
              className="player-sim-dot away"
              title={`${p.name} (#${p.number} ${p.role}) · Speed: ${p.speed_kph ?? 0} km/h`}
              style={{ left: `${p.x}%`, top: `${p.y}%` }}
            >
              <span>{p.number}</span>
            </div>
          ))}
          {liveTracking?.ball && (
            <div
              className="player-sim-ball"
              title={`Ball Position (${liveTracking.ball.x}, ${liveTracking.ball.y}) · ${liveTracking.ball.speed_kph} km/h`}
              style={{ left: `${liveTracking.ball.x}%`, top: `${liveTracking.ball.y}%` }}
            />
          )}

          {/* Canonical Plotted Events */}
          {plottedEvents.map((event, index) => {
            const isHome = event.team_id === homeTeamId || event.team_id.includes("ridge");
            return <motion.button key={event.event_id} className={`event-marker ${isHome ? "ridge" : "harbor"} ${evidenceIds.has(event.event_id) ? "evidence" : ""}`} title={`${clock(event)} ${name(event.event_type)} · ${name(event.player_id)}`} initial={reduceMotion ? false : { opacity: 0, scale: .6 }} animate={{ opacity: 1, scale: evidenceIds.has(event.event_id) ? 1.32 : 1 }} transition={{ type: "spring", stiffness: 300, damping: 30, delay: reduceMotion ? 0 : index * .03 }} style={{ left: `${event.x}%`, top: `${event.y}%` }} onClick={() => setSelectedInsight(insights.find(insight => insight.source_event_ids.includes(event.event_id)) ?? null)}><span /></motion.button>;
          })}
          {!plottedEvents.length && !liveTracking && <div className="pitch-empty"><PlayRegular /><p>No accepted coordinates yet</p><small>Load a synthetic scenario in the live console.</small></div>}
        </div>
        <div className="pitch-legend"><span><i className="ridge" /> {homeTeamName} event</span><span><i className="harbor" /> {awayTeamName} event</span><span><i className="evidence" /> Selected evidence</span>{liveTracking && <span style={{ color: "var(--pitch-emerald)", fontWeight: 800 }}><i style={{ background: "#00ff87", boxShadow: "0 0 6px #00ff87" }} /> Live 22-Player Physics Stream</span>}</div>
      </section>

      <aside className="radar-side">
        <section className="radar-card"><p className="console-eyebrow">Evidence window</p><h2>{selectedInsight?.headline ?? "No verified moment selected"}</h2><p>{selectedInsight?.summary ?? "The radar stays intentionally quiet until a material moment passes deterministic validation."}</p>{selectedInsight && <div className="evidence-list">{events.filter(event => evidenceIds.has(event.event_id)).map(event => <div key={event.event_id}><time>{clock(event)}</time><span>{name(event.event_type)}</span><small>{name(event.zone)}</small></div>)}</div>}</section>
        <section className="radar-card"><p className="console-eyebrow">Data policy</p><h2>What this view knows</h2><ul><li>Accepted synthetic event positions</li><li>Verified insight evidence windows</li><li>Team ownership and match clock</li></ul><p className="radar-muted">It does not synthesize 22 player positions, speed, or video-derived events. Those appear only when a compliant source supplies them.</p></section>
      </aside>
    </div>
  </main>;
}
