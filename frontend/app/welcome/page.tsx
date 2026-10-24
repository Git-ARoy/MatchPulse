"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";

const agents = [
  ["Match Analyst", "Statistical momentum detection"], ["Tactical Analyst", "Territorial pressure and transition hypotheses"],
  ["Narrative Producer", "Fan, analyst, and broadcast adaptation"], ["Evidence Auditor", "Deterministic factual validation"],
];

export default function WelcomePage() {
  const { scrollYProgress } = useScroll();
  const footballY = useTransform(scrollYProgress, [0, 1], [0, 180]);
  return <main className="marketing"><section className="marketing-hero"><div><span className="hero-badge">Microsoft × Premier League · Inside the Game</span><h1>See the match. Trust the evidence.</h1><p>Live football intelligence with deterministic facts, inspected reasoning, and audience-ready stories.</p><div className="hero-actions"><Link className="primary-cta" href="/dashboard">Launch Live Console</Link><Link className="secondary-cta" href="/dashboard">Explore Demo Matches</Link></div></div><motion.div style={{ y: footballY }} className="floating-ball" aria-hidden>●</motion.div></section><section className="agent-showcase"><h2>Four roles. One evidence ledger.</h2><div className="agent-rail">{agents.map(([title, body], index) => <motion.article initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * 0.08 }} key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{body}</p></motion.article>)}</div></section></main>;
}
