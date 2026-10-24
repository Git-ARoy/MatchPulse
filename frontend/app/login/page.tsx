"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signIn } from "next-auth/react";
import { motion } from "framer-motion";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("analyst@premierleague.com");
  const [password, setPassword] = useState("MatchPulse2026!");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  const handleCredentialsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg("");
    try {
      const res = await signIn("credentials", {
        redirect: false,
        email,
        password,
        callbackUrl: "/dashboard",
      });
      if (res?.error) {
        setErrorMsg("Invalid credentials. Use demo credentials or continue as guest.");
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      setErrorMsg("An unexpected error occurred. Continuing to console...");
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    signIn("google", { callbackUrl: "/dashboard" });
  };

  const handleGuestAccess = () => {
    router.push("/dashboard");
  };

  return (
    <main className="stadium-auth-bg">
      {/* Stadium floodlight beams */}
      <div className="floodlight-beam beam-left" />
      <div className="floodlight-beam beam-right" />
      <div className="pitch-lines-ambient" />

      <motion.div
        className="auth-card-premium"
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      >
        {/* Header */}
        <div style={{ textAlign: "center" }}>
          <div className="auth-brand-badge">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="#00FF87" />
            </svg>
            <span>MATCHPULSE ACCESS</span>
          </div>

          <h1 className="auth-title">Enter Match Room</h1>
          <p className="auth-desc">
            Evidence-first intelligence & multi-agent verification console.
          </p>
        </div>

        {/* Social / OAuth Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          className="auth-social-btn"
          aria-label="Continue with Google"
        >
          <svg width="20" height="20" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z"
            />
            <path
              fill="#34A853"
              d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24Z"
            />
            <path
              fill="#FBBC05"
              d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.98 0 12s.45 3.82 1.25 5.42l4.03-3.15Z"
            />
            <path
              fill="#EA4335"
              d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98Z"
            />
          </svg>
          <span>Continue with Google</span>
        </button>

        {/* Divider */}
        <div className="auth-divider">
          <span>or use analyst credentials</span>
        </div>

        {/* Form */}
        <form onSubmit={handleCredentialsSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div className="input-label">
            <span>Analyst Work Email</span>
            <input
              className="input-field"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@premierleague.com"
              required
            />
          </div>

          <div className="input-label">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span>Security Key / Password</span>
              <span style={{ fontSize: "11px", color: "var(--pitch-emerald)", fontWeight: 700 }}>Preloaded Demo</span>
            </div>
            <input
              className="input-field"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
            />
          </div>

          {errorMsg && (
            <div style={{ fontSize: "12px", color: "var(--accent-crimson)", background: "rgba(225, 29, 72, 0.08)", padding: "8px 12px", borderRadius: "8px", fontWeight: 600 }}>
              {errorMsg}
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            style={{ width: "100%", padding: "12px", fontSize: "15px" }}
            disabled={loading}
          >
            {loading ? "Verifying..." : "Sign In to Match Room"}
          </button>
        </form>

        {/* One-Click Guest Access Option */}
        <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "4px" }}>
          <button
            type="button"
            onClick={handleGuestAccess}
            className="btn-secondary"
            style={{ width: "100%", padding: "10px", fontSize: "13px" }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"></path>
              <polyline points="10 17 15 12 10 7"></polyline>
              <line x1="15" y1="12" x2="3" y2="12"></line>
            </svg>
            <span>Explore Console as Guest (Instant Access)</span>
          </button>

          <div style={{ textAlign: "center", marginTop: "4px" }}>
            <Link href="/" style={{ fontSize: "13px", color: "var(--ink-muted)", textDecoration: "none", fontWeight: 600 }}>
              ← Return to MatchPulse Overview
            </Link>
          </div>
        </div>

        {/* Security badge footer */}
        <div className="auth-footer-security">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
          </svg>
          <span>Audited by Microsoft Agent Framework & Azure AI Foundry</span>
        </div>
      </motion.div>
    </main>
  );
}
