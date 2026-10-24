"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";

type Event = { event_id: string; minute: number; second: number; team_id: string; player_id?: string | null; event_type: string; x?: number | null; y?: number | null; zone?: string | null };
type Insight = { insight_id: string; headline: string; summary: string; why_it_matters: string; source_event_ids: string[]; match_clock: { minute: number; second: number }; validation?: { status: string }; audience_variants?: Record<string, { headline: string; summary: string; why_it_matters: string }> };
type State = { match_clock: { minute: number; second: number }; status: string; teams: Record<string, { goals: number; shots: number; shots_on_target: number; passes: number; passes_completed: number; high_regains: number }>; metrics: Record<string, { team_id: string; value: number; delta: number | null }>; data_source?: string; historical?: boolean; live_feed_available?: boolean };
type AvailableMatch = { source_match_id: string; match_id: string; home_team?: string; away_team?: string; match_date?: string; competition?: string; season?: string; event_count: number };
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const display = (value: string) => value.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, char => char.toUpperCase());

export default function DashboardPage() {
  const [matchId, setMatchId] = useState("statsbomb_123");
  const [state, setState] = useState<State | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [selected, setSelected] = useState<Insight | null>(null);
  const [mode, setMode] = useState("fan");
  const [message, setMessage] = useState("Enter a StatsBomb Open Data match ID to inspect its historical event ledger.");
  const [availableMatches, setAvailableMatches] = useState<AvailableMatch[]>([]);
  const [sourceMatchId, setSourceMatchId] = useState("");
  const [importing, setImporting] = useState(false);

  const discover = useCallback(async () => {
    try {
      const response = await fetch(`${api}/api/v1/import/statsbomb/matches?limit=50`);
      if (!response.ok) throw new Error("Could not read the Open Data catalog. Check STATSBOMB_OPEN_DATA_ROOT.");
      const body = await response.json() as { items: AvailableMatch[] };
      setAvailableMatches(body.items);
      if (body.items.length) setSourceMatchId(current => current || body.items[0].source_match_id);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Open Data catalog unavailable."); }
  }, []);

  const importMatch = async () => {
    if (!sourceMatchId.trim()) return;
    setImporting(true); setMessage("Importing completed Open Data events…");
    try {
      const response = await fetch(`${api}/api/v1/import/statsbomb/${encodeURIComponent(sourceMatchId.trim())}`, { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body?.error?.message ?? "Historical match import failed.");
      setMatchId(body.match_id); setMessage(`Imported ${body.accepted_count} historical events. Live feed is not available for this match.`);
    } catch (error) { setMessage(error instanceof Error ? error.message : "Historical match import failed."); }
    finally { setImporting(false); }
  };

  const load = useCallback(async () => {
    setMessage("Loading match data…");
    try {
      const id = encodeURIComponent(matchId);
      const [stateResponse, eventsResponse, insightsResponse] = await Promise.all([
        fetch(`${api}/api/v1/matches/${id}/state`), fetch(`${api}/api/v1/matches/${id}/events?limit=100`), fetch(`${api}/api/v1/matches/${id}/insights`),
      ]);
      if (stateResponse.status === 404) { setState(null); setEvents([]); setInsights([]); setSelected(null); setMessage("This match is not loaded. Configure STATSBOMB_OPEN_DATA_ROOT and import a completed match first."); return; }
      if (!stateResponse.ok || !eventsResponse.ok || !insightsResponse.ok) throw new Error("Match data could not be retrieved.");
      const nextState = await stateResponse.json() as State; const eventBody = await eventsResponse.json(); const insightBody = await insightsResponse.json();
      const nextInsights = insightBody.items as Insight[];
      setState(nextState); setEvents(eventBody.items); setInsights(nextInsights); setSelected(current => nextInsights.find(item => item.insight_id === current?.insight_id) ?? nextInsights[0] ?? null);
      setMessage(nextState.live_feed_available === false ? "Historical event replay loaded. Live feed is not available for this match." : "Live match feed connected.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to load match data."); }
  }, [matchId]);

  useEffect(() => { void load(); void discover(); }, [load, discover]);
  useEffect(() => {
    if (!state?.live_feed_available) return;
    const socket = new WebSocket(api.replace(/^http/, "ws") + `/api/v1/matches/${encodeURIComponent(matchId)}/live-stream`);
    socket.onmessage = () => void load();
    return () => socket.close();
  }, [load, matchId, state?.live_feed_available]);

  const selectedCopy = selected?.audience_variants?.[mode] ?? selected;
  const pressure = useMemo(() => Object.values(state?.metrics ?? {}), [state]);
  return <main className="dashboard-grid"><div className="dashboard-toolbar"><div><Link href="/" className="nav-item">Overview</Link><span className="crumb">/ Historical match console</span></div><div className="match-selector"><label htmlFor="match-id">Loaded ID</label><input id="match-id" value={matchId} onChange={event => setMatchId(event.target.value)} /><button className="btn-primary" onClick={() => void load()}>Load</button></div></div>
    <section className="dash-panel import-panel"><div><h2 className="panel-heading-text">Open Data match catalog</h2><p className="panel-subtitle">Completed Hudl/StatsBomb matches only. Imported matches are replayable; no live feed is available.</p></div><div className="match-selector"><label htmlFor="source-match-id">Source match ID</label><select id="source-match-id" value={sourceMatchId} onChange={event => setSourceMatchId(event.target.value)}><option value="">Select a match</option>{availableMatches.map(item => <option key={item.source_match_id} value={item.source_match_id}>{item.source_match_id} · {item.home_team ?? "Home"} vs {item.away_team ?? "Away"} ({item.event_count} events)</option>)}</select><button className="btn-primary" disabled={importing || !sourceMatchId} onClick={() => void importMatch()}>{importing ? "Importing…" : "Import historical match"}</button><button className="btn-secondary" onClick={() => void discover()}>Refresh catalog</button></div></section>
    <div className={`data-availability ${state?.live_feed_available === false ? "historical" : ""}`}><span className="status-dot" /><strong>{state?.live_feed_available === false ? "HISTORICAL REPLAY" : state ? "LIVE SOURCE" : "NO SOURCE"}</strong><span>{message}</span></div>
    <section className="match-header-card"><div className="team-display"><div className="team-crest-badge crest-home">SB</div><div><div className="team-name">{state ? Object.keys(state.teams)[0] ? display(Object.keys(state.teams)[0]) : "Home" : "Historical match"}</div><div className="team-subtitle">{state?.data_source ?? "Awaiting import"}</div></div></div><div className="scoreboard-center"><div className="match-timer"><span className="font-mono tabular-nums">{state ? `${state.match_clock.minute}:${String(state.match_clock.second).padStart(2, "0")}` : "—"}</span></div><div className="score-digits tabular-nums">{state ? `${Object.values(state.teams)[0]?.goals ?? 0} - ${Object.values(state.teams)[1]?.goals ?? 0}` : "—"}</div><div className="team-subtitle">{state?.status ?? "No match loaded"}</div></div><div className="team-display away"><div className="team-crest-badge crest-away">OD</div><div><div className="team-name">{state ? Object.keys(state.teams)[1] ? display(Object.keys(state.teams)[1]) : "Away" : "Open Data"}</div><div className="team-subtitle">StatsBomb event archive</div></div></div></section>
    <section className="ops-three-columns"><div className="dash-panel"><h2 className="panel-heading-text">Pressure-v1 snapshot</h2><p className="panel-subtitle">Deterministic metric from the imported event ledger.</p>{pressure.length ? pressure.map(item => <div className="metric-line" key={item.team_id}><span>{display(item.team_id)}</span><strong>{item.value.toFixed(1)}</strong><span>{item.delta == null ? "No prior window" : `${item.delta >= 0 ? "+" : ""}${item.delta.toFixed(1)} Δ`}</span></div>) : <p className="empty-copy">Import a completed match to calculate pressure.</p>}<Link href={`/match/${matchId}/analysis`} className="btn-secondary">Open tactical radar</Link></div><div className="dash-panel"><div className="panel-header-row"><h2 className="panel-heading-text">Evidence-linked insights</h2><span className="source-badge">{insights.length}</span></div>{insights.length ? insights.map(insight => <button className="insight-card" key={insight.insight_id} onClick={() => setSelected(insight)}><strong>{insight.headline}</strong><span>{insight.match_clock.minute}&apos; · {insight.validation?.status ?? "verified"}</span></button>) : <p className="empty-copy">No significant moments detected in this historical event stream.</p>}{selected && <div className="selected-insight"><div className="audience-tab-group">{["fan", "analyst", "broadcast"].map(item => <button key={item} className={`audience-tab-btn ${mode === item ? "active" : ""}`} onClick={() => setMode(item)}>{display(item)}</button>)}</div><motion.div key={mode} initial={{ opacity: 0 }} animate={{ opacity: 1 }}><h3>{selectedCopy?.headline}</h3><p>{selectedCopy?.summary}</p><p><strong>Why it matters:</strong> {selectedCopy?.why_it_matters}</p></motion.div><small>Evidence: {selected.source_event_ids.join(", ")}</small></div>}</div><div className="dash-panel"><div className="panel-header-row"><h2 className="panel-heading-text">Event ticker</h2><span className="source-badge">{events.length}</span></div><div className="event-ticker">{events.length ? [...events].reverse().map(event => <div className="event-row" key={event.event_id}><span className="event-time">{event.minute}&apos;{String(event.second).padStart(2, "0")}</span><div><strong>{display(event.event_type)}</strong><small>{display(event.player_id ?? event.team_id)}</small></div><span className="zone-badge">{display(event.zone ?? "zone unavailable")}</span></div>) : <p className="empty-copy">No accepted events yet.</p>}</div></div></section>
  </main>;
}
