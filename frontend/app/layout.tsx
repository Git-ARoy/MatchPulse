import type { Metadata } from "next";
import "./styles.css";
import { Navbar } from "../src/components/navigation/Navbar";
import { Footer } from "../src/components/navigation/Footer";

export const metadata: Metadata = {
  title: "MatchPulse | Evidence-First Football Intelligence",
  description: "Transforming live football events into explainable, evidence-backed, audience-specific insights.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
