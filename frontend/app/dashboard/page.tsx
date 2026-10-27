"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowClockwiseRegular, ChartMultipleRegular, EyeRegular, PersonRegular, PlayRegular, ShieldCheckmarkRegular, SparkleRegular, TranslateRegular } from "@fluentui/react-icons";
import { motion, useReducedMotion } from "framer-motion";

type Team = { goals: number; shots: number; shots_on_target: number; passes: number; passes_completed: number; high_regains: number };
type Player = { player_id: string; team_id: string; passes: number; passes_completed: number; shots: number; goals: number; high_regains: number; pressure_events: number };
type Event = { event_id: string; minute: number; second: number; team_id: string; player_id?: string; event_type: string; zone?: string; x?: number; y?: number };
type Variant = { headline: string; summary: string; why_it_matters: string; detail?: string; next_watch?: string };
type Insight = { insight_id: string; headline: string; summary: string; why_it_matters: string; detail?: string; next_watch?: string; source_event_ids: string[]; match_clock: { minute: number; second: number }; validation?: { status: string }; audience_variants: Record<string, Variant>; agent_findings?: { stage: string; status: string }[] };
type State = { match_clock: { minute: number; second: number }; status: string; teams: Record<string, Team>; metrics: Record<string, { team_id: string; value: number; delta?: number | null; availability: string }>; team_metrics: Record<string, { pass_completion_pct?: number | null; average_pass_distance_m?: number | null; average_pass_difficulty?: number | null; average_shot_speed_kph?: number | null }>; players: Player[]; synthetic: boolean; data_source: string; live_feed_available: boolean };
type Scenario = { scenario_id: string; title: string; description: string; match_id: string; home_team_name: string; away_team_name: string };
type ActiveMatch = { match_id: string; status: string; match_clock: { minute: number; second: number }; teams: Record<string, { goals: number }>; event_count: number };
type Recap = { headline: string; summary: string; language: string; evidence_event_ids: string[] };

const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const initialMatchId = "synthetic_ridge_harbor";
const display = (value: string) => value.replaceAll("_", " ").replace(/\b\w/g, item => item.toUpperCase());
const clock = (value?: { minute: number; second: number }) => value ? `${value.minute}:${String(value.second).padStart(2, "0")}` : "--:--";

export default function DashboardPage() {
  const reduceMotion = useReducedMotion();
  const [matchId, setMatchId] = useState(initialMatchId);
  const [state, setState] = useState<State | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeMatches, setActiveMatches] = useState<ActiveMatch[]>([]);
  const [selected, setSelected] = useState<Insight | null>(null);
  const [mode, setMode] = useState<"fan" | "analyst" | "broadcast">("fan");
  const [language, setLanguage] = useState<"en" | "es">("en");
  const [playerFocus, setPlayerFocus] = useState("");
  const [recap, setRecap] = useState<Recap | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionPending, setActionPending] = useState(false);
  const [notice, setNotice] = useState("Load the fictional match sequence to begin the live studio experience.");

  const loadMatch = useCallback(async (id = matchId) => {
    setLoading(true);
    try {
      const encoded = encodeURIComponent(id);
      const [stateResponse, eventsResponse, insightsResponse] = await Promise.all([
        fetch(`${api}/api/v1/matches/${encoded}/state`),
        fetch(`${api}/api/v1/matches/${encoded}/events?limit=100`),
        fetch(`${api}/api/v1/matches/${encoded}/insights?limit=20`),
      ]);
      if (stateResponse.status === 404) { setState(null); setEvents([]); setInsights([]); setSelected(null); return; }
      if (!stateResponse.ok || !eventsResponse.ok || !insightsResponse.ok) throw new Error("The match service did not return a complete state.");
      const nextState = await stateResponse.json() as State;
      const nextEvents = (await eventsResponse.json()).items as Event[];
      const nextInsights = (await insightsResponse.json()).items as Insight[];
      setState(nextState); setEvents(nextEvents); setInsights(nextInsights);
      setSelected(current => nextInsights.find(item => item.insight_id === current?.insight_id) ?? nextInsights.at(-1) ?? null);
      setNotice("Synthetic event ledger connected. Every displayed claim links to accepted events.");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Unable to load the match service."); }
    finally { setLoading(false); }
  }, [matchId]);

  const loadScenario = async (scenario: Scenario) => {
    setActionPending(true); setRecap(null);
    try {
      const response = await fetch(`${api}/api/v1/demo/scenarios/${scenario.scenario_id}`, { method: "POST" });
      if (!response.ok && response.status !== 409) throw new Error("Could not ingest this synthetic scenario.");
      setMatchId(scenario.match_id);
      await loadMatch(scenario.match_id);
    } catch (error) { setNotice(error instanceof Error ? error.message : "Unable to load the scenario."); }
    finally { setActionPending(false); }
  };

  const loadRecap = async () => {
    if (!state) return;
    setActionPending(true);
    try {
      const response = await fetch(`${api}/api/v1/matches/${encodeURIComponent(matchId)}/recap?audience=${mode}&language=${language}`);
      if (!response.ok) throw new Error("The recap could not be generated.");
      setRecap(await response.json() as Recap);
    } catch (error) { setNotice(error instanceof Error ? error.message : "The recap could not be generated."); }
    finally { setActionPending(false); }
  };

  const loadActiveMatches = useCallback(async () => {
    try {
      const response = await fetch(`${api}/api/v1/matches`);
      if (response.ok) {
        const body = await response.json();
        const items = (body.items || []) as ActiveMatch[];
        const filtered = items.filter(item => !scenarios.some(s => s.match_id === item.match_id) && item.event_count > 0);
        setActiveMatches(filtered);
      }
    } catch {
      // Background match discovery silent error
    }
  }, [scenarios]);

  useEffect(() => { void fetch(`${api}/api/v1/demo/scenarios`).then(response => response.ok ? response.json() : Promise.reject()).then(body => setScenarios(body.items)).catch(() => setNotice("Start the API to load the synthetic showcase.")); }, []);
  useEffect(() => { void loadMatch(); void loadActiveMatches(); }, [loadMatch, loadActiveMatches]);
  useEffect(() => {
    const timer = setInterval(() => void loadActiveMatches(), 5000);
    return () => clearInterval(timer);
  }, [loadActiveMatches]);
  useEffect(() => {
    if (!state?.live_feed_available) return;
    const socket = new WebSocket(api.replace(/^http/, "ws") + `/api/v1/matches/${encodeURIComponent(matchId)}/live-stream`);
    socket.onmessage = () => { void loadMatch(); void loadActiveMatches(); };
    return () => socket.close();
  }, [loadActiveMatches, loadMatch, matchId, state?.live_feed_available]);

  const activeCopy = selected?.audience_variants[mode] ?? selected;
  const teams = Object.entries(state?.teams ?? {});
  const focusedPlayer = state?.players.find(player => player.player_id === playerFocus);
  const metrics = useMemo(() => Object.values(state?.metrics ?? {}).filter(metric => metric.availability === "available"), [state]);

  return <main className="console-shell">
    <section className="console-topline"><div><p className="console-eyebrow">Synthetic studio environment</p><h1>Live match intelligence</h1><p>Fictional events flow through the same ingest, interpret, explain, render, and personalize pipeline.</p></div><div className="synthetic-policy"><ShieldCheckmarkRegular /><span>No real Premier League match data</span></div></section>

    <section className="scenario-strip" aria-label="Synthetic scenarios">
      {activeMatches.map(m => <button key={m.match_id} className={`scenario-choice ${m.match_id === matchId ? "active" : ""}`} disabled={actionPending} onClick={() => { setMatchId(m.match_id); void loadMatch(m.match_id); }}><PlayRegular /><span><strong>{Object.keys(m.teams).map(display).join(" vs ") || display(m.match_id)}</strong><small>Live simulation ({clock(m.match_clock)} · {m.event_count} events)</small></span></button>)}
      {scenarios.map(scenario => <button key={scenario.scenario_id} className={`scenario-choice ${scenario.match_id === matchId ? "active" : ""}`} disabled={actionPending} onClick={() => void loadScenario(scenario)}><PlayRegular /><span><strong>{scenario.title}</strong><small>{scenario.description}</small></span></button>)}
      <button className="refresh-button" onClick={() => { void loadMatch(); void loadActiveMatches(); }} aria-label="Refresh match data"><ArrowClockwiseRegular /></button>
    </section>

    <section className="scorebar" aria-live="polite">
      <div className="scorebar-team"><span className="team-mark home">RU</span><strong>{teams[0] ? display(teams[0][0]) : "Ridge United"}</strong></div>
      <div className="scorebar-score"><span>{clock(state?.match_clock)}</span><strong>{teams.length ? `${teams[0]?.[1].goals ?? 0} - ${teams[1]?.[1].goals ?? 0}` : "0 - 0"}</strong><small>{state?.status?.replaceAll("_", " ") ?? "Awaiting synthetic feed"}</small></div>
      <div className="scorebar-team away"><strong>{teams[1] ? display(teams[1][0]) : "Harbor FC"}</strong><span className="team-mark away">HF</span></div>
    </section>

    <p className={`console-notice ${state?.synthetic ? "ready" : ""}`}>{loading ? "Connecting to match services..." : notice}</p>

    <div className="console-layout">
      <section className="console-main">
        <div className="section-heading"><div><p className="console-eyebrow">Verified story</p><h2>{activeCopy?.headline ?? "Awaiting a material moment"}</h2></div><div className="mode-switch" role="tablist" aria-label="Audience mode">{(["fan", "analyst", "broadcast"] as const).map(item => <button key={item} role="tab" aria-selected={mode === item} className={mode === item ? "selected" : ""} onClick={() => setMode(item)}>{item}</button>)}</div></div>
        {activeCopy ? <motion.article initial={reduceMotion ? false : { opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="story-card"><p>{activeCopy.summary}</p><div><span>Why it matters</span><p>{activeCopy.why_it_matters}</p></div>{mode === "analyst" && activeCopy.detail && <small>{activeCopy.detail}</small>}{mode === "fan" && activeCopy.next_watch && <small>Next watch: {activeCopy.next_watch}</small>}<footer><ShieldCheckmarkRegular /> Verified against {selected?.source_event_ids.length ?? 0} event(s)</footer></motion.article> : <div className="empty-state"><SparkleRegular /><p>A routine sequence is deliberately quiet until the evidence threshold is met.</p></div>}

        <div className="metric-grid">{metrics.length ? metrics.map(metric => <article key={metric.team_id} className="metric-panel"><span>{display(metric.team_id)} pressure</span><strong>{metric.value.toFixed(0)}</strong><small>{metric.delta == null ? "Opening window" : `${metric.delta >= 0 ? "+" : ""}${metric.delta.toFixed(0)} vs previous five minutes`}</small></article>) : <article className="metric-panel placeholder"><span>Pressure index</span><strong>--</strong><small>Load a scenario to calculate</small></article>}</div>

        <section className="recap-card"><div><p className="console-eyebrow">Automatic recap</p><h2>{recap?.headline ?? "A recap, grounded in the ledger"}</h2>{recap ? <p>{recap.summary}</p> : <p>Produce a compact, audience-aware wrap using only approved insights and their source events.</p>}</div><div className="recap-controls"><label><TranslateRegular /> Language<select value={language} onChange={event => setLanguage(event.target.value as "en" | "es")}><option value="en">English</option><option value="es">Español</option></select></label><button className="console-action" disabled={!state || actionPending} onClick={() => void loadRecap()}>Generate recap</button></div></section>
      </section>

      <aside className="console-rail">
        <section className="rail-panel"><div className="rail-title"><ChartMultipleRegular /><h2>Evidence timeline</h2><span>{insights.length}</span></div>{insights.length ? insights.slice().reverse().map(insight => <button key={insight.insight_id} className={`timeline-item ${selected?.insight_id === insight.insight_id ? "current" : ""}`} onClick={() => setSelected(insight)}><time>{clock(insight.match_clock)}</time><strong>{insight.headline}</strong><small>{insight.validation?.status ?? "verified"}</small></button>) : <p className="rail-empty">No verified moments yet.</p>}</section>
        <section className="rail-panel"><div className="rail-title"><EyeRegular /><h2>Incoming events</h2><span>{events.length}</span></div><div className="event-feed">{events.length ? events.slice().reverse().map(event => <div className="event-item" key={event.event_id}><time>{clock(event)}</time><div><strong>{display(event.event_type)}</strong><small>{display(event.player_id ?? event.team_id)}</small></div><span>{display(event.zone ?? "unmapped")}</span></div>) : <p className="rail-empty">The ledger is empty.</p>}</div></section>
        <section className="rail-panel player-focus"><div className="rail-title"><PersonRegular /><h2>Player focus</h2></div><select value={playerFocus} onChange={event => setPlayerFocus(event.target.value)}><option value="">Choose a player</option>{state?.players.map(player => <option key={player.player_id} value={player.player_id}>{display(player.player_id)}</option>)}</select>{focusedPlayer ? <div className="player-facts"><strong>{display(focusedPlayer.player_id)}</strong><span>{focusedPlayer.passes_completed}/{focusedPlayer.passes} completed passes</span><span>{focusedPlayer.shots} shots · {focusedPlayer.goals} goals</span><span>{focusedPlayer.high_regains} high regains</span></div> : <p className="rail-empty">Choose a player to keep their verified actions in view.</p>}<Link href={`/match/${matchId}/analysis`} className="radar-link">Open tactical radar</Link></section>
      </aside>
    </div>
  </main>;
}
