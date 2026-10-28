"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRightRegular, PlayRegular, ShieldCheckmarkRegular } from "@fluentui/react-icons";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

type Scenario = { scenario_id: string; title: string; description: string; match_id: string };
type Insight = { headline: string; summary: string; source_event_ids: string[]; validation?: { status: string } };
const api = process.env.NEXT_PUBLIC_API_URL || "";

export function LiveInteractivePreview() {
  const reduceMotion = useReducedMotion();
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState("momentum-surge");
  const [insight, setInsight] = useState<Insight | null>(null);
  const [message, setMessage] = useState("Choose a fictional sequence to run it through the evidence pipeline.");
  const [pending, setPending] = useState(false);

  useEffect(() => { void fetch(`${api}/api/v1/demo/scenarios`).then(response => response.ok ? response.json() : Promise.reject()).then(body => setScenarios(body.items)).catch(() => setMessage("Start the API to run the synthetic showcase.")); }, []);

  const run = async () => {
    const scenario = scenarios.find(item => item.scenario_id === selected);
    if (!scenario) return;
    setPending(true); setInsight(null);
    try {
      const loaded = await fetch(`${api}/api/v1/demo/scenarios/${selected}`, { method: "POST" });
      if (!loaded.ok && loaded.status !== 409) throw new Error("The synthetic sequence could not be ingested.");
      const insights = await fetch(`${api}/api/v1/matches/${scenario.match_id}/insights?limit=5`);
      if (!insights.ok) throw new Error("The evidence service did not return an insight.");
      const items = (await insights.json()).items as Insight[];
      setInsight(items.at(-1) ?? null);
      setMessage(items.length ? "The pipeline produced a verified, evidence-linked story." : "The pipeline stayed quiet because the sequence did not cross a story threshold.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to run the showcase."); }
    finally { setPending(false); }
  };

  return <section className="studio-preview"><div className="studio-preview-intro"><p className="section-kicker">Try the pipeline</p><h2>Put the evidence engine on air.</h2><p>Run a short fictional sequence. The result is fetched from the same APIs used by the live console.</p><div className="scenario-buttons">{scenarios.map(scenario => <button key={scenario.scenario_id} className={selected === scenario.scenario_id ? "active" : ""} onClick={() => setSelected(scenario.scenario_id)}>{scenario.title}</button>)}</div><button className="preview-run" disabled={pending || !scenarios.length} onClick={() => void run()}><PlayRegular />{pending ? "Running sequence" : "Run synthetic sequence"}</button></div><div className="studio-preview-output"><AnimatePresence mode="wait">{insight ? <motion.article key={insight.headline} initial={reduceMotion ? false : { opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? undefined : { opacity: 0, y: -10 }} className="preview-insight"><div><ShieldCheckmarkRegular /><span>{insight.validation?.status ?? "verified"}</span></div><h3>{insight.headline}</h3><p>{insight.summary}</p><small>{insight.source_event_ids.length} source events locked to this claim</small></motion.article> : <motion.div key="empty" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} className="preview-empty"><ShieldCheckmarkRegular /><p>{message}</p></motion.div>}</AnimatePresence><Link href="/dashboard" className="preview-console-link">Open full studio <ArrowRightRegular /></Link></div></section>;
}
