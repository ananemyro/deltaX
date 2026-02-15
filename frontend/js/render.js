import { sim } from "./state.js";
import { STAR_COUNT, DEST_EDGE_ARROW_SIZE } from "./config.js";
import { worldToScreen } from "./canvas.js";
import { drawEarthAtScreen } from "./earth.js";

const stars = Array.from({ length: STAR_COUNT }, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * 1.6 + 0.2,
  a: Math.random() * 0.6 + 0.2,
}));

const AU_KM = 149_597_870.7;

function getRocketAndDest() {
  const r = sim.state?.rocket;
  const d = sim.state?.destination ?? sim.state?.dest; // tolerate either key
  return { r, d };
}

function updateMissState() {
  if (!sim.state) return;
  if (!sim.started) return;
  if (sim.missed) return;

  const status = sim.state.hud?.status;
  if (status === "success" || status === "failed") return;

  const { r, d } = getRocketAndDest();
  if (!r || !d) return;

  // Capture starting x once
  if (sim.startX == null) sim.startX = r.x;

  // Determine which “side” we started on (left/right of Earth)
  const goingRight = sim.startX < d.x;

  // How far past Earth counts as “miss”
  const margin = (d.radius ?? 30) * 1.2;

  // “Miss” means we crossed Earth’s x plus margin without success
  const crossed = goingRight ? (r.x > d.x + margin) : (r.x < d.x - margin);

  if (crossed) sim.missed = true;
}

function drawMissOverlay(canvas, ctx) {
  if (!sim.missed) return;

  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);

  // Dim
  ctx.fillStyle = "rgba(0,0,0,0.72)";
  ctx.fillRect(0, 0, w, h);

  // Text
  ctx.fillStyle = "rgba(255,255,255,0.92)";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  ctx.font = "700 34px system-ui";
  ctx.fillText("And then…", w / 2, h / 2 - 18);

  ctx.font = "800 40px system-ui";
  ctx.fillText("there were none.", w / 2, h / 2 + 26);

  ctx.restore();
}

function remainingDistanceUnits() {
  const { r, d } = getRocketAndDest();
  if (!r || !d) return 0;
  const dx = d.x - r.x;
  const dy = d.y - r.y;
  return Math.sqrt(dx * dx + dy * dy);
}

function len(x, y) { return Math.sqrt(x * x + y * y); }

function drawStars(canvas, ctx) {
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  for (const s of stars) {
    ctx.beginPath();
    ctx.arc(s.x * w, s.y * h, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${s.a})`;
    ctx.fill();
  }
}

function drawTrail(canvas, ctx) {
  if (!sim.state || sim.trail.length < 2) return;

  ctx.beginPath();
  for (let i = 0; i < sim.trail.length; i++) {
    const p = sim.trail[i];
    const sp = worldToScreen(canvas, p.x, p.y);
    if (i === 0) ctx.moveTo(sp.x, sp.y);
    else ctx.lineTo(sp.x, sp.y);
  }
  ctx.strokeStyle = "rgba(95,227,255,0.22)";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawPlanets(canvas, ctx) {
  for (const p of sim.state.planets) {
    const sp = worldToScreen(canvas, p.x, p.y);
    const zoom = sim.state.camera.zoom;
    const radius = p.radius * zoom;

    // Capture zone display (match your physics)
    const orbitRadius = (p.radius + 20.0) * zoom;

    ctx.save();
    ctx.translate(sp.x, sp.y);

    // Dotted orbit circle
    ctx.beginPath();
    ctx.arc(0, 0, orbitRadius, 0, Math.PI * 2);
    ctx.setLineDash([5, 8]);
    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]);

    // Countdown for orange planet if latched
    if (sim.state.latched_planet_id === p.id && p.status === "okay") {
      const countdown = sim.state.countdown;
      ctx.fillStyle = countdown < 3 ? "#ff7675" : "white";
      ctx.font = "bold 18px monospace";
      ctx.textAlign = "center";
      ctx.fillText(Math.ceil(countdown) + "s", 0, -radius - 30);

      if (countdown < 3) {
        ctx.beginPath();
        ctx.arc(0, 0, radius + 15, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 44, 44, ${0.3 + Math.sin(Date.now()/100)*0.2})`;
        ctx.lineWidth = 4;
        ctx.stroke();
      }
    }

    // Rings
    if (p.mass > 2500 || p.status === "good") {
      ctx.beginPath();
      ctx.ellipse(0, 0, radius * 2.2, radius * 0.8, Math.PI / 6, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(155, 176, 255, 0.15)";
      ctx.lineWidth = 3;
      ctx.stroke();
    }

    // Sphere gradient
    const grad = ctx.createRadialGradient(-radius/3, -radius/3, radius/10, 0, 0, radius);
    grad.addColorStop(0, p.color);
    grad.addColorStop(1, "#1a1a1a");

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // Surface details
    ctx.globalAlpha = 0.3;
    if (p.status === "bad" || p.radius < 40) {
      ctx.fillStyle = "rgba(0,0,0,0.2)";
      ctx.beginPath(); ctx.arc(-radius/2, radius/4, radius/5, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.arc(radius/3, -radius/3, radius/6, 0, Math.PI*2); ctx.fill();
    } else {
      ctx.fillStyle = "white";
      ctx.fillRect(-radius, -radius/4, radius*2, radius/2);
    }
    ctx.globalAlpha = 1.0;

    // Atmosphere / latch glow
    const isLatched = sim.state.latched_planet_id === p.id;
    ctx.beginPath();
    ctx.arc(0, 0, radius + 5, 0, Math.PI * 2);
    ctx.strokeStyle = isLatched ? "white" : p.color + "44";
    ctx.lineWidth = isLatched ? 3 : 4;
    ctx.stroke();

    ctx.restore();
  }
}

function drawGlobalWarning(canvas, ctx) {
  const latchedId = sim.state.latched_planet_id;
  if (latchedId === null) return;

  const countdown = sim.state.countdown;
  const currentPlanet = sim.state.planets.find(p => p.id === latchedId);
  if (!currentPlanet || currentPlanet.status !== "okay") return;

  const w = canvas.getBoundingClientRect().width;
  const opacity = 0.4 + Math.sin(Date.now() / 150) * 0.4;

  ctx.save();
  ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);

  const boxW = 180;
  const boxH = 60;
  const padding = 20;
  const x = w - boxW - padding;
  const y = padding;

  ctx.fillStyle = `rgba(231, 76, 60, ${opacity})`;
  ctx.beginPath();
  ctx.rect(x, y, boxW, boxH);
  ctx.fill();

  ctx.strokeStyle = "white";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.fillStyle = "white";
  ctx.font = "bold 14px monospace";
  ctx.textAlign = "center";
  ctx.fillText("STABILITY WARNING", x + boxW / 2, y + 25);

  ctx.font = "bold 24px monospace";
  ctx.fillText(countdown.toFixed(2) + "s", x + boxW / 2, y + 50);

  ctx.restore();
}

function drawShip(canvas, ctx) {
  const r = sim.state.rocket;
  const sp = worldToScreen(canvas, r.x, r.y);

  ctx.save();
  ctx.translate(sp.x, sp.y);

  const ang = Math.atan2(r.vy, r.vx);
  ctx.rotate(-ang);

  const scale = 1.4;

  const speed = Math.sqrt(r.vx * r.vx + r.vy * r.vy);
  if (speed > 0.1) {
    const flicker = Math.random() * 5;
    const flameLen = (15 + speed * 5) * scale + flicker;

    ctx.beginPath();
    ctx.moveTo(-10, 0);
    ctx.quadraticCurveTo(-15, -8, -10 - flameLen, 0);
    ctx.quadraticCurveTo(-15, 8, -10, 0);
    ctx.fillStyle = "rgba(255, 120, 0, 0.6)";
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(-10, 0);
    ctx.quadraticCurveTo(-12, -4, -10 - (flameLen * 0.6), 0);
    ctx.quadraticCurveTo(-12, 4, -10, 0);
    ctx.fillStyle = "rgba(255, 255, 100, 0.9)";
    ctx.fill();
  }

  ctx.fillStyle = "#e74c3c";
  ctx.beginPath();
  ctx.moveTo(-4, -6);
  ctx.bezierCurveTo(-15, -15, -20, -15, -12, -6);
  ctx.moveTo(-4, 6);
  ctx.bezierCurveTo(-15, 15, -20, 15, -12, 6);
  ctx.fill();

  const bodyGrad = ctx.createLinearGradient(0, -10, 0, 10);
  bodyGrad.addColorStop(0, "#ffffff");
  bodyGrad.addColorStop(0.5, "#dcdde1");
  bodyGrad.addColorStop(1, "#bdc3c7");

  ctx.beginPath();
  ctx.moveTo(20 * scale, 0);
  ctx.bezierCurveTo(15 * scale, -10 * scale, -10 * scale, -10 * scale, -12 * scale, 0);
  ctx.bezierCurveTo(-10 * scale, 10 * scale, 15 * scale, 10 * scale, 20 * scale, 0);
  ctx.fillStyle = bodyGrad;
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(20 * scale, 0);
  ctx.bezierCurveTo(18 * scale, -5 * scale, 12 * scale, -6 * scale, 10 * scale, -7 * scale);
  ctx.lineTo(10 * scale, 7 * scale);
  ctx.bezierCurveTo(12 * scale, 6 * scale, 18 * scale, 5 * scale, 20 * scale, 0);
  ctx.clip();
  ctx.fillStyle = "#e74c3c";
  ctx.fill();
  ctx.restore();

  ctx.beginPath();
  ctx.arc(2, 0, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = "#3498db";
  ctx.fill();
  ctx.strokeStyle = "#2980b9";
  ctx.lineWidth = 1;
  ctx.stroke();

  ctx.restore();
}

function drawEarthDestination(canvas, ctx) {
  const { d: dest } = getRocketAndDest();
  if (!dest) return;

  const ds = worldToScreen(canvas, dest.x, dest.y);
  const zoom = sim.state.camera.zoom;
  const rPx = dest.radius * zoom;

  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;
  if (ds.x < -rPx - 50 || ds.x > w + rPx + 50 || ds.y < -rPx - 50 || ds.y > h + rPx + 50) return;

  drawEarthAtScreen(ctx, ds.x, ds.y, rPx, 42, 0, false);

  ctx.save();
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.font = "bold 16px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("EARTH", ds.x, ds.y + 6);
  ctx.restore();
}

function drawDestinationAndArrow(canvas, ctx) {
  const { r: rocket, d: dest } = getRocketAndDest();
  if (!rocket || !dest) return;

  const ds = worldToScreen(canvas, dest.x, dest.y);
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  const onScreen = (ds.x >= -60 && ds.x <= w + 60 && ds.y >= -60 && ds.y <= h + 60);
  if (onScreen) return;

  const pulse = Math.sin(Date.now() / 200) * 1.5;
  const opacity = 0.5 + Math.sin(Date.now() / 200) * 0.1;

  const shipS = worldToScreen(canvas, rocket.x, rocket.y);
  const vx = ds.x - shipS.x;
  const vy = ds.y - shipS.y;

  const pad = 40;
  const minX = pad, maxX = w - pad, minY = pad, maxY = h - pad;

  let ax = ds.x, ay = ds.y;

  const cx = w / 2, cy = h / 2;
  const rx = ds.x - cx, ry = ds.y - cy;
  const tCandidates = [];

  if (Math.abs(rx) > 1e-6) { tCandidates.push((minX - cx) / rx); tCandidates.push((maxX - cx) / rx); }
  if (Math.abs(ry) > 1e-6) { tCandidates.push((minY - cy) / ry); tCandidates.push((maxY - cy) / ry); }

  let best = null;
  for (const t of tCandidates) {
    if (t <= 0) continue;
    const x = cx + rx * t;
    const y = cy + ry * t;
    if (x >= minX - 2 && x <= maxX + 2 && y >= minY - 2 && y <= maxY + 2) {
      if (best === null || t < best.t) best = { t, x, y };
    }
  }
  if (best) { ax = best.x; ay = best.y; }

  const ang = Math.atan2(vy, vx);

  ctx.save();
  ctx.translate(ax, ay);
  ctx.rotate(ang);

  ctx.shadowBlur = 15;
  ctx.shadowColor = "rgba(95, 227, 255, 0.8)";

  ctx.beginPath();
  const arrowHeadSize = DEST_EDGE_ARROW_SIZE + pulse;
  ctx.moveTo(0, 0);
  ctx.lineTo(-arrowHeadSize, -arrowHeadSize / 1.5);
  ctx.lineTo(-arrowHeadSize * 0.7, 0);
  ctx.lineTo(-arrowHeadSize, arrowHeadSize / 1.5);
  ctx.closePath();

  ctx.fillStyle = `rgba(95, 227, 255, 0.9)`;
  ctx.fill();
  ctx.restore();

  if (sim.initialDistance == null) sim.initialDistance = remainingDistanceUnits();
  const dUnits = remainingDistanceUnits();
  const dAU = 10.0 * (dUnits / Math.max(1e-6, sim.initialDistance));

  ctx.fillStyle = `rgba(95, 227, 255, ${opacity})`;
  ctx.font = "bold 12px monospace";
  ctx.fillText(`${dAU.toFixed(2)} AU`, ax - 28, ay + 30);
}

function drawJoystickVector(canvas, ctx) {
  if (len(sim.joyVec.x, sim.joyVec.y) < 0.05) return;
  const r = sim.state.rocket;
  const ship = worldToScreen(canvas, r.x, r.y);

  const arrowPx = 110 * Math.min(1, len(sim.joyVec.x, sim.joyVec.y));
  const vx = -sim.joyVec.x;
  const vy = -sim.joyVec.y;

  const end = { x: ship.x + vx * arrowPx, y: ship.y + vy * arrowPx };

  ctx.beginPath();
  ctx.moveTo(ship.x, ship.y);
  ctx.lineTo(end.x, end.y);
  ctx.strokeStyle = "rgba(255,255,255,0.8)";
  ctx.lineWidth = 2;
  ctx.stroke();

  const a = Math.atan2(end.y - ship.y, end.x - ship.x);
  const head = 10;
  ctx.beginPath();
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(end.x - head * Math.cos(a - 0.5), end.y - head * Math.sin(a - 0.5));
  ctx.lineTo(end.x - head * Math.cos(a + 0.5), end.y - head * Math.sin(a + 0.5));
  ctx.closePath();
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  ctx.fill();
}

function drawEmergencyBurnCounter(canvas, ctx) {
  if (!sim.state) return;

  const currentBurns = sim.state.space_burns_left ?? 10;
  const burstCount = sim.state.consecutive_burns ?? 0;
  const canSpaceBurn = sim.state.can_space_burn ?? true;
  const isLatched = sim.state.latched_planet_id !== null;

  ctx.save();
  ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);

  const h = canvas.getBoundingClientRect().height;
  const x = 20;
  const y = h - 80;

  ctx.fillStyle = "rgba(13, 15, 20, 0.85)";
  ctx.beginPath();
  ctx.roundRect(x, y, 190, 60, 8);
  ctx.fill();

  ctx.strokeStyle = canSpaceBurn ? "rgba(255, 255, 255, 0.1)" : "#ff4d4d";
  ctx.lineWidth = 2;
  ctx.stroke();

  let statusColor = "#5fe3ff";
  let burstText = `BURST: ${burstCount}/3`;

  if (isLatched) {
    statusColor = "#6dff57";
    burstText = "ORBITAL: UNLIMITED";
  } else if (!canSpaceBurn) {
    statusColor = "#ff4d4d";
    burstText = "ENGINES LOCKED";
  }

  ctx.fillStyle = "#9aa6b2";
  ctx.font = "bold 9px monospace";
  ctx.fillText("EMERGENCY PROPULSION", x + 12, y + 18);

  ctx.fillStyle = statusColor;
  ctx.font = "bold 28px monospace";
  ctx.fillText(`${currentBurns}`, x + 12, y + 48);

  ctx.fillStyle = statusColor;
  ctx.font = "bold 9px monospace";
  ctx.fillText(burstText, x + 60, y + 45);

  ctx.restore();
}

export function renderFrame(canvas, ctx) {
  if (!sim.state) return;

  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  ctx.clearRect(0, 0, w, h);

  drawStars(canvas, ctx);
  drawTrail(canvas, ctx);
  drawPlanets(canvas, ctx);

  drawEarthDestination(canvas, ctx);
  drawDestinationAndArrow(canvas, ctx);

  drawShip(canvas, ctx);
  drawJoystickVector(canvas, ctx);

  drawGlobalWarning(canvas, ctx);
  drawEmergencyBurnCounter(canvas, ctx);

  // Miss logic should run AFTER we have state for this frame
  updateMissState();
}
