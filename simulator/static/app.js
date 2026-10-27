// MatchPulse Synthetic Match Simulator - Frontend Engine & Canvas Visualizer

const canvas = document.getElementById("pitchCanvas");
const ctx = canvas.getContext("2d");

// DOM Elements
const btnStart = document.getElementById("btnStart");
const btnPause = document.getElementById("btnPause");
const btnResume = document.getElementById("btnResume");
const btnReset = document.getElementById("btnReset");
const btnAdvanceHalf = document.getElementById("btnAdvanceHalf");
const matchupSelect = document.getElementById("matchupSelect");

const homeName = document.getElementById("homeName");
const homeBadge = document.getElementById("homeBadge");
const awayName = document.getElementById("awayName");
const awayBadge = document.getElementById("awayBadge");
const scoreText = document.getElementById("scoreText");
const clockText = document.getElementById("clockText");
const phaseBadge = document.getElementById("phaseBadge");
const pitchStatus = document.getElementById("pitchStatus");

const toggleNames = document.getElementById("toggleNames");
const toggleZones = document.getElementById("toggleZones");

const statDelivered = document.getElementById("statDelivered");
const statAcks = document.getElementById("statAcks");
const statLatency = document.getElementById("statLatency");
const bridgeStatusIndicator = document.getElementById("bridgeStatusIndicator");
const eventFeedList = document.getElementById("eventFeedList");
const eventCountBadge = document.getElementById("eventCountBadge");

const mpSyncBadge = document.getElementById("mpSyncBadge");
const mpHomePressureLabel = document.getElementById("mpHomePressureLabel");
const mpHomePressureVal = document.getElementById("mpHomePressureVal");
const mpAwayPressureLabel = document.getElementById("mpAwayPressureLabel");
const mpAwayPressureVal = document.getElementById("mpAwayPressureVal");
const mpInsightContainer = document.getElementById("mpInsightContainer");

// Live Simulation State Cache
let currentSnapshot = null;
let currentDispatcher = null;
let recentEvents = [];
let ballTrail = [];

// WebSocket Connection
let socket = null;

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/live`;
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    pitchStatus.textContent = "Live Telemetry Connected · Stream Active";
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.snapshot) {
        currentSnapshot = data.snapshot;
        currentDispatcher = data.dispatcher;
        if (data.recent_events) {
          recentEvents = data.recent_events;
        }
        updateScoreboard();
        updateBridgeTelemetry();
        updateEventFeed();
      }
    } catch (err) {
      console.error("WS Parse error", err);
    }
  };

  socket.onclose = () => {
    pitchStatus.textContent = "Reconnecting to Simulator Stream…";
    setTimeout(connectWebSocket, 2000);
  };
}

// REST Control Actions
async function apiCall(endpoint, method = "POST", body = null) {
  try {
    const res = await fetch(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : null,
    });
    return await res.json();
  } catch (err) {
    console.error("API Call failed:", endpoint, err);
  }
}

// Event Listeners for Controls
btnStart.addEventListener("click", async () => {
  await apiCall("/api/simulation/start");
  btnStart.disabled = true;
  btnPause.disabled = false;
  btnResume.disabled = true;
});

btnPause.addEventListener("click", async () => {
  await apiCall("/api/simulation/pause");
  btnPause.disabled = true;
  btnResume.disabled = false;
});

btnResume.addEventListener("click", async () => {
  await apiCall("/api/simulation/resume");
  btnPause.disabled = false;
  btnResume.disabled = true;
});

btnReset.addEventListener("click", async () => {
  await apiCall("/api/simulation/reset", "POST", { matchup_id: matchupSelect.value });
  btnStart.disabled = false;
  btnPause.disabled = true;
  btnResume.disabled = true;
  btnAdvanceHalf.style.display = "none";
});

btnAdvanceHalf.addEventListener("click", async () => {
  await apiCall("/api/simulation/advance-half");
  btnAdvanceHalf.style.display = "none";
  btnPause.disabled = false;
});

matchupSelect.addEventListener("change", async (e) => {
  await apiCall("/api/simulation/reset", "POST", { matchup_id: e.target.value });
  btnStart.disabled = false;
  btnPause.disabled = true;
  btnResume.disabled = true;
});

// Speed Pills
document.querySelectorAll(".speed-pills .pill").forEach((pill) => {
  pill.addEventListener("click", async () => {
    document.querySelectorAll(".speed-pills .pill").forEach((p) => p.classList.remove("active"));
    pill.classList.add("active");
    const speed = parseFloat(pill.dataset.speed);
    await apiCall("/api/simulation/speed", "POST", { multiplier: speed });
  });
});

// Scenario Injector Buttons
document.querySelectorAll(".btn-inject").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const action = btn.dataset.action;
    const teamRole = btn.dataset.team;
    let teamId = null;
    if (currentSnapshot) {
      teamId = teamRole === "home" ? currentSnapshot.home_team.team_id : currentSnapshot.away_team.team_id;
    }
    await apiCall("/api/simulation/inject", "POST", { action, team_id: teamId });
  });
});

// Update DOM elements from snapshot
function updateScoreboard() {
  if (!currentSnapshot) return;

  const home = currentSnapshot.home_team;
  const away = currentSnapshot.away_team;

  homeName.textContent = home.name;
  homeBadge.textContent = home.short_name;
  homeBadge.style.color = home.primary_color;

  awayName.textContent = away.name;
  awayBadge.textContent = away.short_name;
  awayBadge.style.color = away.primary_color;

  scoreText.textContent = `${home.score} - ${away.score}`;
  clockText.textContent = currentSnapshot.clock_display;

  const phase = currentSnapshot.phase;
  phaseBadge.textContent = phase.replace("_", " ").toUpperCase();

  if (phase === "first_half") {
    phaseBadge.style.color = "#10B981";
    btnAdvanceHalf.style.display = "none";
  } else if (phase === "half_time") {
    phaseBadge.style.color = "#F59E0B";
    btnAdvanceHalf.style.display = "inline-block";
    btnPause.disabled = true;
  } else if (phase === "second_half") {
    phaseBadge.style.color = "#10B981";
    btnAdvanceHalf.style.display = "none";
  } else if (phase === "full_time") {
    phaseBadge.style.color = "#EF4444";
    btnPause.disabled = true;
    btnResume.disabled = true;
  }

  // Update button states
  if (currentSnapshot.is_paused && phase !== "not_started" && phase !== "full_time") {
    btnPause.disabled = true;
    btnResume.disabled = false;
  } else if (!currentSnapshot.is_paused) {
    btnStart.disabled = true;
    btnPause.disabled = false;
    btnResume.disabled = true;
  }
}

function updateBridgeTelemetry() {
  if (!currentDispatcher) return;

  statDelivered.textContent = currentDispatcher.total_dispatched;
  statAcks.textContent = currentDispatcher.delivered_count;
  statLatency.textContent = `${currentDispatcher.latency_ms} ms`;

  const status = currentDispatcher.status;
  bridgeStatusIndicator.className = "bridge-status";
  if (status === "connected") {
    bridgeStatusIndicator.textContent = "Live Stream (200 OK)";
    bridgeStatusIndicator.classList.add("status-connected");
  } else if (status === "unreachable") {
    bridgeStatusIndicator.textContent = "MatchPulse Offline";
    bridgeStatusIndicator.classList.add("status-unreachable");
  } else {
    bridgeStatusIndicator.textContent = status;
    bridgeStatusIndicator.classList.add("status-idle");
  }

  // Update Bi-Directional MatchPulse AI Intelligence Feedback
  const intel = currentDispatcher.matchpulse_intelligence;
  if (intel && intel.connected) {
    mpSyncBadge.textContent = `Sync v${intel.state_version} (${intel.last_synced_at})`;
    mpSyncBadge.style.color = "#10B981";

    // Pressure Index
    if (currentSnapshot) {
      const homeId = currentSnapshot.home_team.team_id;
      const awayId = currentSnapshot.away_team.team_id;
      const homePressure = intel.pressure_metrics[`pressure_index:${homeId}`];
      const awayPressure = intel.pressure_metrics[`pressure_index:${awayId}`];

      mpHomePressureLabel.textContent = `${currentSnapshot.home_team.short_name} Pressure`;
      mpAwayPressureLabel.textContent = `${currentSnapshot.away_team.short_name} Pressure`;

      if (homePressure && typeof homePressure.value === "number") {
        const delta = homePressure.delta != null ? ` (${homePressure.delta >= 0 ? "+" : ""}${Math.round(homePressure.delta)})` : "";
        mpHomePressureVal.textContent = `${Math.round(homePressure.value)}${delta}`;
      } else {
        mpHomePressureVal.textContent = "Calculating…";
      }

      if (awayPressure && typeof awayPressure.value === "number") {
        const delta = awayPressure.delta != null ? ` (${awayPressure.delta >= 0 ? "+" : ""}${Math.round(awayPressure.delta)})` : "";
        mpAwayPressureVal.textContent = `${Math.round(awayPressure.value)}${delta}`;
      } else {
        mpAwayPressureVal.textContent = "Calculating…";
      }
    }

    // Latest AI Insight
    if (intel.latest_insights && intel.latest_insights.length > 0) {
      const latest = intel.latest_insights[0];
      mpInsightContainer.innerHTML = `
        <div class="mp-insight-card">
          <div class="mp-insight-header">
            <span class="mp-insight-badge">⏱ ${latest.clock} · ${latest.validation_status.toUpperCase()}</span>
          </div>
          <div class="mp-insight-headline">${latest.headline}</div>
          <div class="mp-insight-summary">${latest.summary}</div>
        </div>
      `;
    }
  } else {
    mpSyncBadge.textContent = "Awaiting Feedback";
    mpSyncBadge.style.color = "#64748B";
  }
}

function updateEventFeed() {
  if (!recentEvents.length) return;
  eventCountBadge.textContent = `${currentSnapshot ? currentSnapshot.event_count : recentEvents.length} events`;

  const reversed = [...recentEvents].reverse();
  const html = reversed
    .map((e) => {
      const isGoal = e.event_type === "goal";
      const isCard = e.event_type === "yellow_card" || e.event_type === "red_card";
      const cls = isGoal ? "goal" : isCard ? "card" : "";
      const clock = `${e.minute}:${String(e.second).padStart(2, "0")}`;
      const actor = e.player_id ? e.player_id.replace(/^.*?_/, "").toUpperCase() : e.team_id.replace("_", " ").toUpperCase();
      return `
      <div class="event-entry ${cls}">
        <time>${clock}</time>
        <span class="type">${e.event_type.replace("_", " ")}</span>
        <span class="actor">${actor}</span>
      </div>
    `;
    })
    .join("");

  eventFeedList.innerHTML = html;
}

// ---------------------------------------------------------------------------
// 2D Pitch Canvas Rendering (60 FPS)
// ---------------------------------------------------------------------------

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 1. Draw Pitch Grass & Stripes
  drawPitchBackground();

  // 2. Draw Tactical Zones (if toggled)
  if (toggleZones.checked) {
    drawTacticalZones();
  }

  // 3. Draw Pitch Markings (Lines, Circles, Boxes)
  drawPitchMarkings();

  // 4. Draw 22 Players
  if (currentSnapshot) {
    drawPlayers(currentSnapshot.home_team, true);
    drawPlayers(currentSnapshot.away_team, false);

    // 5. Draw Ball & Motion Trail
    drawBall(currentSnapshot.ball);
  }

  requestAnimationFrame(render);
}

function drawPitchBackground() {
  const width = canvas.width;
  const height = canvas.height;
  const numStripes = 10;
  const stripeWidth = width / numStripes;

  for (let i = 0; i < numStripes; i++) {
    ctx.fillStyle = i % 2 === 0 ? "#123420" : "#143C25";
    ctx.fillRect(i * stripeWidth, 0, stripeWidth, height);
  }

  // Pitch Border
  ctx.strokeStyle = "rgba(255, 255, 255, 0.4)";
  ctx.lineWidth = 2.5;
  ctx.strokeRect(0, 0, width, height);
}

function drawTacticalZones() {
  const width = canvas.width;
  const height = canvas.height;

  ctx.strokeStyle = "rgba(0, 229, 255, 0.12)";
  ctx.setLineDash([4, 6]);
  ctx.lineWidth = 1.5;

  // Defensive / Middle / Attacking Third lines
  const third1 = width * 0.333;
  const third2 = width * 0.666;

  ctx.beginPath();
  ctx.moveTo(third1, 0);
  ctx.lineTo(third1, height);
  ctx.moveTo(third2, 0);
  ctx.lineTo(third2, height);
  ctx.stroke();

  ctx.setLineDash([]); // reset
}

function drawPitchMarkings() {
  const w = canvas.width;
  const h = canvas.height;

  ctx.strokeStyle = "rgba(255, 255, 255, 0.55)";
  ctx.lineWidth = 2;

  // Halfway Line
  ctx.beginPath();
  ctx.moveTo(w / 2, 0);
  ctx.lineTo(w / 2, h);
  ctx.stroke();

  // Center Circle (radius ~ 9.15m -> ~8.7% of 105m)
  const centerRadius = w * 0.087;
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, centerRadius, 0, Math.PI * 2);
  ctx.stroke();

  // Center Spot
  ctx.fillStyle = "#FFFFFF";
  ctx.beginPath();
  ctx.arc(w / 2, h / 2, 3, 0, Math.PI * 2);
  ctx.fill();

  // Penalty Boxes (16.5m depth -> 15.7% of w, 40.3m height -> 59.2% of h)
  const boxDepth = w * 0.157;
  const boxHeight = h * 0.592;
  const boxTop = (h - boxHeight) / 2;

  // Left 18-yard box
  ctx.strokeRect(0, boxTop, boxDepth, boxHeight);
  // Right 18-yard box
  ctx.strokeRect(w - boxDepth, boxTop, boxDepth, boxHeight);

  // 6-yard boxes (5.5m depth -> 5.2% of w, 18.3m height -> 26.9% of h)
  const smallDepth = w * 0.052;
  const smallHeight = h * 0.269;
  const smallTop = (h - smallHeight) / 2;

  ctx.strokeRect(0, smallTop, smallDepth, smallHeight);
  ctx.strokeRect(w - smallDepth, smallTop, smallDepth, smallHeight);

  // Penalty Spots (11m -> 10.4% of w)
  const penSpotDist = w * 0.104;
  ctx.beginPath();
  ctx.arc(penSpotDist, h / 2, 2.5, 0, Math.PI * 2);
  ctx.arc(w - penSpotDist, h / 2, 2.5, 0, Math.PI * 2);
  ctx.fill();

  // Penalty D-Arcs
  ctx.beginPath();
  ctx.arc(penSpotDist, h / 2, centerRadius, -0.65, 0.65, false);
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(w - penSpotDist, h / 2, centerRadius, Math.PI - 0.65, Math.PI + 0.65, false);
  ctx.stroke();

  // Corner Arcs
  const cornerRadius = w * 0.015;
  ctx.beginPath();
  ctx.arc(0, 0, cornerRadius, 0, Math.PI / 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(0, h, cornerRadius, -Math.PI / 2, 0);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(w, 0, cornerRadius, Math.PI / 2, Math.PI);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(w, h, cornerRadius, Math.PI, -Math.PI / 2);
  ctx.stroke();

  // Goal Mouths (7.32m -> 10.76% of h)
  const goalHeight = h * 0.1076;
  const goalTop = (h - goalHeight) / 2;
  ctx.lineWidth = 4;
  ctx.strokeStyle = "#FFFFFF";
  ctx.strokeRect(-5, goalTop, 5, goalHeight);
  ctx.strokeRect(w, goalTop, 5, goalHeight);
}

function drawPlayers(team, isHome) {
  const w = canvas.width;
  const h = canvas.height;
  const showNames = toggleNames.checked;

  for (const player of team.players) {
    if (player.is_sent_off) continue;

    const px = (player.x / 100) * w;
    const py = (player.y / 100) * h;

    // Player Circle
    ctx.save();
    ctx.beginPath();
    ctx.arc(px, py, 11, 0, Math.PI * 2);
    ctx.fillStyle = team.primary_color;
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = team.secondary_color || "#FFFFFF";
    ctx.stroke();

    // Shirt Number
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "bold 9px var(--font-mono)";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(player.number, px, py);

    // Cards
    if (player.yellow_cards > 0) {
      ctx.fillStyle = "#F59E0B";
      ctx.fillRect(px + 7, py - 11, 4, 7);
      ctx.strokeStyle = "#000";
      ctx.lineWidth = 0.5;
      ctx.strokeRect(px + 7, py - 11, 4, 7);
    }

    // Name Label
    if (showNames) {
      ctx.fillStyle = "rgba(11, 15, 23, 0.75)";
      ctx.font = "500 9px var(--font-sans)";
      const displayName = player.name.split(" ").slice(-1)[0]; // last name
      const textWidth = ctx.measureText(displayName).width;
      ctx.fillRect(px - textWidth / 2 - 3, py + 14, textWidth + 6, 12);
      ctx.fillStyle = "#F0F4FC";
      ctx.fillText(displayName, px, py + 23);
    }

    ctx.restore();
  }
}

function drawBall(ball) {
  const w = canvas.width;
  const h = canvas.height;

  const bx = (ball.x / 100) * w;
  const by = (ball.y / 100) * h;

  // Maintain motion trail
  ballTrail.push({ x: bx, y: by });
  if (ballTrail.length > 8) ballTrail.shift();

  // Draw trail
  if (ballTrail.length > 1) {
    ctx.save();
    for (let i = 0; i < ballTrail.length - 1; i++) {
      const alpha = (i + 1) / ballTrail.length * 0.35;
      ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(ballTrail[i].x, ballTrail[i].y);
      ctx.lineTo(ballTrail[i + 1].x, ballTrail[i + 1].y);
      ctx.stroke();
    }
    ctx.restore();
  }

  // Ball Height Shadow (if in the air)
  if (ball.z > 0.1) {
    ctx.save();
    ctx.fillStyle = "rgba(0, 0, 0, 0.35)";
    ctx.beginPath();
    ctx.ellipse(bx, by + ball.z * 3, 5 + ball.z, 3 + ball.z * 0.5, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  // Draw Ball
  ctx.save();
  const radius = 5.5 + Math.min(3, ball.z * 0.5);
  ctx.beginPath();
  ctx.arc(bx, by, radius, 0, Math.PI * 2);
  ctx.fillStyle = "#FFFFFF";
  ctx.fill();
  ctx.lineWidth = 1.5;
  ctx.strokeStyle = "#1A1A1A";
  ctx.stroke();

  // Subtle gloss
  ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
  ctx.beginPath();
  ctx.arc(bx - 1.5, by - 1.5, radius * 0.4, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

// Start visualizer loop and WS connection
connectWebSocket();
requestAnimationFrame(render);
