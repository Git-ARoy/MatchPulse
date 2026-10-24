import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "MatchPulse | Intelligence Console",
  description: "Evidence-first football intelligence.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
