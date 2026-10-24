"use client";

import { HeroSection } from "../../src/components/landing/HeroSection";
import { HorizontalAgentRail } from "../../src/components/landing/HorizontalAgentRail";
import { LiveInteractivePreview } from "../../src/components/landing/LiveInteractivePreview";

export default function WelcomePage() {
  return (
    <main className="landing-shell">
      <HeroSection />
      <HorizontalAgentRail />
      <LiveInteractivePreview />
    </main>
  );
}
