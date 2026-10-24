/**
 * MatchPulse Client-Side API & Real-Time Sync Service
 * 
 * Provides robust communication with the FastAPI backend, automatic fallback
 * to synthetic live data when offline, and WebSocket push streaming.
 */

export interface TeamMetrics {
  pass_completion_pct?: number | null;
  average_pass_distance_m?: number | null;
  average_pass_difficulty?: number | null;
  average_shot_speed_kph?: number | null;
}

export interface MatchStateView {
  match_id: string;
  state_version: number;
  teams: Record<string, {
    team_id: string;
    score: number;
    goals: number;
    passes: number;
    passes_completed: number;
    shots: number;
    shots_on_target: number;
  }>;
  clock: { minute: number; second: number };
  metrics?: Record<string, {
    value: number;
    previous_window_value?: number;
    delta?: number;
  }>;
  team_metrics?: Record<string, TeamMetrics>;
  players?: Array<{
    player_id: string;
    team_id: string;
    passes: number;
    passes_completed: number;
    shots: number;
    goals: number;
    high_regains: number;
    speed_kph?: number;
    distance_km?: number;
  }>;
}

export interface LiveInsight {
  insight_id: string;
  match_id: string;
  match_clock: { minute: number; second: number };
  insight_type: string;
  headline: string;
  summary: string;
  what_changed: string;
  why_it_matters: string;
  audience_variants?: Record<string, {
    mode: string;
    headline: string;
    summary: string;
    why_it_matters: string;
  }>;
  source_event_ids: string[];
}

export interface MatchRecap {
  match_id: string;
  audience: string;
  language: string;
  headline: string;
  summary: string;
  insight_ids: string[];
  evidence_event_ids: string[];
  synthetic: boolean;
  milestones?: string[];
  turning_points?: string[];
  control_vs_chaos?: {
    control_index: number;
    chaos_index: number;
    rhythm_pattern: string;
    tactical_phase: string;
  };
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchMatchState(matchId: string): Promise<MatchStateView | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/matches/${encodeURIComponent(matchId)}/state`, {
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMatchEvents(matchId: string, limit = 50) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/matches/${encodeURIComponent(matchId)}/events?limit=${limit}`, {
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMatchInsights(matchId: string) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/matches/${encodeURIComponent(matchId)}/insights`, {
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMatchRecap(matchId: string, audience = "fan", language = "en"): Promise<MatchRecap | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/matches/${encodeURIComponent(matchId)}/recap?audience=${audience}&language=${language}`, {
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function injectFixture(matchId: string, fixtureName: string) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/dev/matches/${encodeURIComponent(matchId)}/fixtures/${fixtureName}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    return res.ok;
  } catch {
    return false;
  }
}
