"use client";

import { ArrowTrendingRegular, DataBarVerticalRegular, DrawTextRegular, PersonFeedbackRegular, ShieldCheckmarkRegular } from "@fluentui/react-icons";
import { motion, useReducedMotion } from "framer-motion";

const stages = [
  { title: "Ingest", copy: "Validate fictional events, preserve order, and reject duplicate IDs.", icon: ArrowTrendingRegular },
  { title: "Interpret", copy: "Calculate match state, momentum, pressure, pass quality, and player facts.", icon: DataBarVerticalRegular },
  { title: "Explain", copy: "Specialist agents connect material changes to a bounded evidence window.", icon: DrawTextRegular },
  { title: "Render", copy: "Produce compact verified outputs for the console and broadcast overlays.", icon: ShieldCheckmarkRegular },
  { title: "Personalize", copy: "Adapt the same facts for fans, analysts, broadcasters, languages, and player focus.", icon: PersonFeedbackRegular },
];

export function HorizontalAgentRail() {
  const reduceMotion = useReducedMotion();
  return <section id="pipeline" className="pipeline-section"><div className="pipeline-intro"><p className="section-kicker">One evidence ledger</p><h2>Five stages. One accountable story.</h2><p>MatchPulse keeps numerical claims deterministic, gives agents a bounded role, and leaves an inspectable trail from event to screen.</p></div><div className="pipeline-track">{stages.map((stage, index) => { const Icon = stage.icon; return <motion.article key={stage.title} initial={reduceMotion ? false : { opacity: 0, y: 28 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={{ duration: 0.5, delay: index * 0.06 }} className="pipeline-stage"><span className="pipeline-index">{String(index + 1).padStart(2, "0")}</span><Icon /><h3>{stage.title}</h3><p>{stage.copy}</p></motion.article>; })}</div></section>;
}
