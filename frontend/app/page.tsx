"use client";

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, FluentProvider, Input, Spinner, Text, webLightTheme } from "@fluentui/react-components";
import { ArrowClockwiseRegular, ChevronRightRegular, DataBarVerticalRegular, PulseRegular, ShieldTaskRegular } from "@fluentui/react-icons";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Team = { goals: number; shots: number; shots_on_target: number; passes: number; passes_completed: number };
type State = { match_clock: { minute: number; second: number }; teams: Record<string, Team>; metrics: Record<string, { team_id: string; value: number; delta: number | null; availability: string }> };
type Finding = { stage: string; status: string; duration_ms: number };
type AudienceMode = "fan" | "analyst" | "broadcast";
type AudienceVariant = { headline: string; summary: string; why_it_matters: string; detail?: string | null; next_watch?: string | null };
type Insight = { insight_id: string; headline: string; summary: string; why_it_matters: string; match_clock: { minute: number; second: number }; validation?: { status: string }; source_event_ids: string[]; agent_findings: Finding[]; audience_variants: Record<AudienceMode, AudienceVariant> };
type MatchEvent = { event_id: string; minute: number; second: number; event_type: string; team_id: string; player_id?: string | null; zone?: string | null };
type FixtureName = "pressure-swing" | "goal-sequence" | "quiet-period";

const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const fixtures: { name: FixtureName; title: string; description: string }[] = [
  { name: "pressure-swing", title: "Pressure Swing", description: "A high regain and final-third entry create a verified pressure signal." },
  { name: "goal-sequence", title: "Goal Sequence", description: "A short build-up ends in a goal and score-state change." },
  { name: "quiet-period", title: "Quiet Period", description: "Routine midfield actions deliberately produce no insight." },
];

function label(id: string) { return id.replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, char => char.toUpperCase()); }
function clock(event: { minute: number; second: number }) { return `${event.minute}'${String(event.second).padStart(2, "0")}`; }

export default function MatchConsole() {
  const [matchId, setMatchId] = useState("sim_match_001");
  const [state, setState] = useState<State | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [events, setEvents] = useState<MatchEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [fixtureLoading, setFixtureLoading] = useState<FixtureName | null>(null);
  const [selected, setSelected] = useState<Insight | null>(null);
  const [audience, setAudience] = useState<AudienceMode>("fan");

  const load = useCallback(async (requestedMatchId = matchId) => {
    setLoading(true); setError(null);
    try {
      const encodedId = encodeURIComponent(requestedMatchId);
      const [stateResponse, insightsResponse, eventsResponse] = await Promise.all([
        fetch(`${api}/api/v1/matches/${encodedId}/state`),
        fetch(`${api}/api/v1/matches/${encodedId}/insights`),
        fetch(`${api}/api/v1/matches/${encodedId}/events?limit=100`),
      ]);
      if (stateResponse.status === 404) { setState(null); setInsights([]); setEvents([]); setSelected(null); return; }
      if (!stateResponse.ok || !insightsResponse.ok || !eventsResponse.ok) throw new Error("The console could not retrieve current match intelligence.");
      const [nextState, insightPayload, eventPayload] = await Promise.all([stateResponse.json(), insightsResponse.json(), eventsResponse.json()]);
      const nextInsights = insightPayload.items as Insight[];
      setState(nextState as State); setInsights(nextInsights); setEvents(eventPayload.items as MatchEvent[]);
      setSelected(current => nextInsights.find(item => item.insight_id === current?.insight_id) ?? nextInsights[0] ?? null);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to load match data."); }
    finally { setLoading(false); }
  }, [matchId]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    const socketUrl = api.replace(/^http/, "ws") + `/api/v1/matches/${encodeURIComponent(matchId)}/live-stream`;
    const socket = new WebSocket(socketUrl);
    socket.onmessage = () => { void load(); };
    // REST establishes the initial snapshot; all subsequent updates arrive
    // through the live stream so fan/broadcast clients do not poll.
    return () => socket.close();
  }, [matchId, load]);

  const injectFixture = async (fixture: FixtureName) => {
    const fixtureMatchId = `demo_${fixture.replace("-", "_")}_${Date.now()}`;
    setFixtureLoading(fixture); setError(null);
    try {
      const response = await fetch(`${api}/api/v1/dev/matches/${encodeURIComponent(fixtureMatchId)}/fixtures/${fixture}`, { method: "POST" });
      if (!response.ok) {
        const body = await response.json().catch(() => null) as { error?: { message?: string } } | null;
        throw new Error(body?.error?.message ?? "Fixture injection failed.");
      }
      setMatchId(fixtureMatchId);
      await load(fixtureMatchId);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Fixture injection failed."); }
    finally { setFixtureLoading(null); }
  };

  const chart = Object.values(state?.metrics ?? {}).map(metric => ({ team: label(metric.team_id), pressure: metric.value }));
  const selectedVariant = selected?.audience_variants[audience];

  return <FluentProvider theme={webLightTheme} className="shell">
    <header className="topbar"><div><Text weight="semibold" size={500}>MATCHPULSE</Text><Text className="product-label">Evidence-first intelligence console</Text></div><div className="toolbar"><Input value={matchId} onChange={(_, data) => setMatchId(data.value)} aria-label="Match ID" /><Button appearance="primary" icon={loading ? <Spinner size="tiny" /> : <ArrowClockwiseRegular />} onClick={() => void load()}>Refresh</Button></div></header>
    <main className="console">
      <section className="status-strip"><div><Text className="kicker">Live match state</Text><Text className="clock">{state ? clock(state.match_clock) : "—"}</Text></div><div className="status-copy"><Badge appearance="filled" color={state ? "success" : "informative"}>{state ? "Connected" : "Awaiting events"}</Badge><Text>{state ? `${Object.keys(state.teams).length} tracked teams · ${events.length} ledger events · ${insights.length} verified insights` : "Submit canonical events to the API to begin analysis."}</Text></div></section>
      {error && <div className="error"><Text weight="semibold">Data unavailable</Text><Text>{error}</Text></div>}
      <section className="score-grid">{Object.entries(state?.teams ?? {}).map(([team, stats]) => <Card key={team} className="team-card"><Text weight="semibold">{label(team)}</Text><div className="scoreline"><strong>{stats.goals}</strong><span>goals</span></div><Text className="muted">{stats.shots} shots · {stats.shots_on_target} on target · {stats.passes_completed}/{stats.passes} completed passes</Text></Card>)}{!state && <Card className="empty-card"><PulseRegular fontSize={28} /><Text weight="semibold">No match state yet</Text><Text>Use canonical ingestion or one of the controlled synthetic fixtures below.</Text></Card>}</section>
      <section className="workspace"><Card className="pressure-panel"><div className="panel-head"><div><Text className="kicker">Pressure-v1</Text><Text weight="semibold" size={500}>Current five-minute window</Text></div><DataBarVerticalRegular fontSize={22} /></div>{chart.length ? <div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart}><XAxis dataKey="team" tickLine={false} axisLine={false} /><YAxis domain={[0, 100]} tickLine={false} axisLine={false} /><Tooltip /><Bar dataKey="pressure" fill="#0f6cbd" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div> : <Text className="muted">Pressure becomes available after event ingestion.</Text>}<Text className="footnote">MatchPulse-defined metric; not an official Premier League statistic.</Text></Card>
        <Card className="insight-panel"><div className="panel-head"><div><Text className="kicker">Verified insights</Text><Text weight="semibold" size={500}>Evidence-linked moments</Text></div><ShieldTaskRegular fontSize={22} /></div>{insights.length ? <div className="insight-list">{insights.map(item => <button key={item.insight_id} className={`insight-row ${selected?.insight_id === item.insight_id ? "active" : ""}`} onClick={() => setSelected(item)}><div><Text weight="semibold">{item.headline}</Text><Text className="muted">{clock(item.match_clock)} · {item.source_event_ids.length} source events</Text></div><ChevronRightRegular /></button>)}</div> : <Text className="muted">No significant moment has met the configured evidence threshold.</Text>}</Card>
        <Card className="ticker-panel"><div className="panel-head"><div><Text className="kicker">Event ticker</Text><Text weight="semibold" size={500}>Canonical event ledger</Text></div><Badge appearance="tint">{events.length}</Badge></div>{events.length ? <div className="ticker-list">{[...events].reverse().map(event => <div key={event.event_id} className="ticker-row"><Text className="ticker-clock">{clock(event)}</Text><div><Text weight="semibold">{label(event.event_type)}</Text><Text className="muted">{label(event.player_id ?? event.team_id)}</Text></div><Badge appearance="outline">{label(event.zone ?? "unmapped")}</Badge></div>)}</div> : <Text className="muted">Accepted events will appear here in live-ledger order.</Text>}</Card></section>
      <section className="detail-grid"><Card className="detail-panel"><Text className="kicker">Selected insight</Text>{selected ? <><div className="audience-switcher" role="tablist" aria-label="Audience mode">{(["fan", "analyst", "broadcast"] as AudienceMode[]).map(mode => <Button key={mode} role="tab" size="small" appearance={audience === mode ? "primary" : "secondary"} aria-selected={audience === mode} onClick={() => setAudience(mode)}>{label(mode)}</Button>)}</div><Text as="h1" weight="semibold" size={600}>{selectedVariant?.headline ?? selected.headline}</Text><Text>{selectedVariant?.summary ?? selected.summary}</Text><Text className="why"><strong>Why it matters: </strong>{selectedVariant?.why_it_matters ?? selected.why_it_matters}</Text>{selectedVariant?.detail && <Text className="variant-detail">{selectedVariant.detail}</Text>}{selectedVariant?.next_watch && <Text className="next-watch"><strong>Next watch: </strong>{selectedVariant.next_watch}</Text>}<div className="evidence"><Text weight="semibold">Evidence</Text><Text>{selected.source_event_ids.join(" · ")}</Text><Badge color="success">{selected.validation?.status ?? "verified"}</Badge></div></> : <Text className="muted">Select a published insight to inspect its evidence.</Text>}</Card>
        <Card className="trace-panel"><Text className="kicker">Agent activity</Text><Text weight="semibold" size={500}>Inspectable workflow trace</Text>{selected?.agent_findings.length ? <div className="trace-list">{selected.agent_findings.map((stage, index) => <div key={`${stage.stage}-${index}`} className="trace-row"><span className={`trace-dot ${stage.status}`} /><Text>{label(stage.stage)}</Text><Text className="muted">{stage.duration_ms.toFixed(1)} ms</Text></div>)}</div> : <Text className="muted">Agent stages appear only for a verified insight.</Text>}</Card>
        <Card className="fixture-panel"><Text className="kicker">Development fixtures</Text><Text weight="semibold" size={500}>Inject a small synthetic sequence</Text><Text className="muted">Each button creates a fresh match ID and posts to the backend’s dev-only endpoint.</Text><div className="fixture-list">{fixtures.map(fixture => <div key={fixture.name} className="fixture-row"><div><Text weight="semibold">{fixture.title}</Text><Text className="muted">{fixture.description}</Text></div><Button appearance="secondary" disabled={fixtureLoading !== null} icon={fixtureLoading === fixture.name ? <Spinner size="tiny" /> : undefined} onClick={() => void injectFixture(fixture.name)}>Inject</Button></div>)}</div></Card></section>
    </main>
  </FluentProvider>;
}
