"use client";

import Image from "next/image";
import Link from "next/link";
import { ArrowRightRegular, DataBarVerticalRegular, ShieldCheckmarkRegular } from "@fluentui/react-icons";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";

export function HeroSection() {
  const reduceMotion = useReducedMotion();
  const { scrollY } = useScroll();
  const pitchShift = useTransform(scrollY, [0, 700], [0, reduceMotion ? 0 : 55]);

  return (
    <section className="broadcast-hero">
      <motion.div className="broadcast-hero-media" style={{ y: pitchShift }} aria-hidden="true">
        <Image src="/images/stadium-broadcast-hero.png" alt="" fill priority sizes="100vw" className="broadcast-hero-image" />
      </motion.div>
      <div className="broadcast-hero-scrim" aria-hidden="true" />
      <div className="broadcast-hero-content">
        <motion.p initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="hero-kicker">
          Evidence-first football intelligence
        </motion.p>
        <motion.h1 initial={reduceMotion ? false : { opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.65, delay: 0.08 }}>
          Follow the game.<br />Understand the moment.
        </motion.h1>
        <motion.p initial={reduceMotion ? false : { opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.16 }} className="hero-lede">
          Synthetic events become verified stories for fans, analysts, and broadcast teams.
        </motion.p>
        <motion.div initial={reduceMotion ? false : { opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.24 }} className="hero-actions">
          <Link href="/dashboard" className="hero-primary-action">Open the live demo <ArrowRightRegular /></Link>
          <Link href="#pipeline" className="hero-secondary-action">See how evidence works</Link>
        </motion.div>
      </div>
      <motion.aside initial={reduceMotion ? false : { opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.65, delay: 0.28 }} className="hero-proof-card">
        <div className="hero-proof-heading"><span>Live pipeline</span><span className="semantic-live-dot" /></div>
        <div className="hero-proof-row"><DataBarVerticalRegular /><div><strong>Interpret</strong><span>Pressure and match state</span></div></div>
        <div className="hero-proof-row"><ShieldCheckmarkRegular /><div><strong>Verify</strong><span>Evidence before narrative</span></div></div>
        <p>Fictional demo data only. No real Premier League match data is used.</p>
      </motion.aside>
    </section>
  );
}
