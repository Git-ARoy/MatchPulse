"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Event = { event_id: string; player_id?: string | null; team_id: string; x?: number | null; y?: number | null; event_type: string };
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AnalysisPage({ params }: { params: Promise<{ id: string }> }) {
  const [id, setId] = useState(""); const [events, setEvents] = useState<Event[]>([]);
  useEffect(() => { void params.then(({ id }) => setId(id)); }, [params]);
  useEffect(() => { if (!id) return; const load = async () => { const response = await fetch(`${api}/api/v1/matches/${encodeURIComponent(id)}/events?limit=100`); if (response.ok) setEvents((await response.json()).items); }; void load(); const socket = new WebSocket(api.replace(/^http/, "ws") + `/api/v1/matches/${encodeURIComponent(id)}/live-stream`); socket.onmessage = () => void load(); return () => socket.close(); }, [id]);
  const positioned = [...events].reverse().filter(event => event.x != null && event.y != null).filter((event, index, list) => event.player_id && list.findIndex(other => other.player_id === event.player_id) === index).slice(0, 22);
  const ball = [...events].reverse().find(event => event.x != null && event.y != null);
  return <main className="radar-page"><header><p className="eyebrow">Live tactical analysis</p><h1>Pitch radar</h1><p>Markers render only observed canonical player and ball coordinates; no positions are fabricated.</p></header><div className="pitch" role="img" aria-label="Live tactical pitch"><div className="halfway" /><div className="centre-circle" />{positioned.map((event, index) => <motion.div key={event.player_id} className={`player-marker ${event.team_id.includes("ridge") ? "home" : "away"}`} animate={{ left: `${event.x}%`, top: `${event.y}%` }} transition={{ type: "spring", stiffness: 300, damping: 30 }}>{event.player_id?.split("_").pop() ?? index + 1}</motion.div>)}{ball && <motion.div className="ball-marker" animate={{ left: `${ball.x}%`, top: `${ball.y}%` }} transition={{ type: "spring", stiffness: 300, damping: 30 }} />}</div><p className="radar-caption">{positioned.length} observed player positions · {ball ? "ball coordinate available" : "awaiting ball coordinate"}</p></main>;
}
