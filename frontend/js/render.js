import { sim } from "./state.js";
import { STAR_COUNT, SHIP_SIZE, DEST_EDGE_ARROW_SIZE } from "./config.js";
import { worldToScreen } from "./canvas.js";

const stars = Array.from({ length: STAR_COUNT }, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * 1.6 + 0.2,
  a: Math.random() * 0.6 + 0.2,
}));

function len(x, y) { return Math.sqrt(x * x + y * y); }

function fmtDistance(km) {
  const a = Math.abs(km);
  const AU = 149_597_870.7;

  if (a >= 0.5 * AU) return `${(km / AU).toFixed(2)} AU`;
  if (a >= 1e6) return `${(km / 1e6).toFixed(1)} Mkm`;
  if (a >= 1e3) return `${(km / 1e3).toFixed(0)}k km`;
  return `${km.toFixed(0)} km`;
}

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
    const physPx = p.radius * sim.state.camera.zoom;
    const radius = Math.max(4, Math.pow(physPx, 0.7) * 120);

    ctx.save();
    ctx.translate(sp.x, sp.y);

    const hasRings = p.has_rings;
    if (hasRings) {
      ctx.beginPath();
      ctx.ellipse(0, 0, radius * 2.4, radius * 0.9, Math.PI / 6, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
      ctx.lineWidth = 3;
      ctx.stroke();
    }

    const grad = ctx.createRadialGradient(-radius/3, -radius/3, radius/10, 0, 0, radius);
    if (p.color === "green") { grad.addColorStop(0, "#a2f3a2"); grad.addColorStop(1, "#27ae60"); }
    else if (p.color === "red") { grad.addColorStop(0, "#ff7675"); grad.addColorStop(1, "#c0392b"); }
    else { grad.addColorStop(0, "#dfe6e9"); grad.addColorStop(1, "#636e72"); }

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.globalAlpha = 0.3;
    if (p.color === "red" || p.radius < 40) {
      ctx.fillStyle = "rgba(0,0,0,0.2)";
      ctx.beginPath(); ctx.arc(-radius/2, radius/4, radius/5, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.arc(radius/3, -radius/3, radius/6, 0, Math.PI*2); ctx.fill();
    }
    ctx.globalAlpha = 1.0;

    ctx.beginPath();
    ctx.arc(0, 0, radius + 5, 0, Math.PI * 2);
    ctx.strokeStyle = p.color === "green" ? "rgba(46, 204, 113, 0.2)" : "rgba(231, 76, 60, 0.2)";
    ctx.lineWidth = 4;
    ctx.stroke();

    ctx.restore();
  }
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

function drawDestinationAndArrow(canvas, ctx) {
  const dest = sim.state.destination;
  const rocket = sim.state.rocket;
  const dxw = dest.x - rocket.x;
  const dyw = dest.y - rocket.y;
  const distWorldKm = Math.hypot(dxw, dyw);

  const ds = worldToScreen(canvas, dest.x, dest.y);
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  const pulse = Math.sin(Date.now() / 200) * 1.5;
  const opacity = 0.5 + Math.sin(Date.now() / 200) * 0.1;

  const onScreen = (ds.x >= -60 && ds.x <= w + 60 && ds.y >= -60 && ds.y <= h + 60);

  if (onScreen) {
    ctx.beginPath();
    const rPx = Math.min(80, dest.radius * sim.state.camera.zoom);
    ctx.arc(ds.x, ds.y, rPx + pulse, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(95, 227, 255, ${opacity})`;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    ctx.fillStyle = "rgba(95,227,255,0.9)";
    ctx.font = "12px system-ui";
    ctx.fillText("TARGET", ds.x + 12, ds.y - 12);
  }

  const shipS = worldToScreen(canvas, rocket.x, rocket.y);
  const vx = ds.x - shipS.x;
  const vy = ds.y - shipS.y;
  const distPixels = Math.sqrt(vx * vx + vy * vy);

  const pad = 40;
  const minX = pad, maxX = w - pad, minY = pad, maxY = h - pad;

  let ax = ds.x, ay = ds.y;

  if (!onScreen) {
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
  }

  const ang = Math.atan2(vy, vx);

  ctx.save();
  ctx.translate(ax, ay);
  ctx.rotate(ang);

  ctx.shadowBlur = 15;
  ctx.shadowColor = "rgba(95, 227, 255, 0.8)";

  ctx.beginPath();
  const arrowHeadSize = DEST_EDGE_ARROW_SIZE + (onScreen ? 0 : pulse);
  ctx.moveTo(0, 0);
  ctx.lineTo(-arrowHeadSize, -arrowHeadSize / 1.5);
  ctx.lineTo(-arrowHeadSize * 0.7, 0);
  ctx.lineTo(-arrowHeadSize, arrowHeadSize / 1.5);
  ctx.closePath();

  ctx.fillStyle = `rgba(95, 227, 255, ${onScreen ? 0.3 : 0.9})`;
  ctx.fill();
  ctx.restore();

  if (!onScreen) {
    ctx.fillStyle = `rgba(95, 227, 255, ${opacity})`;
    ctx.font = "bold 12px monospace";
    const label = fmtDistance(distWorldKm);
    ctx.textAlign = "center";
    ctx.fillText(label, ax, ay + 30);
    ctx.textAlign = "left";
  }
}

function drawJoystickVector(canvas, ctx) {
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

export function renderFrame(canvas, ctx) {
  if (!sim.state) return;

  ctx.save();
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.restore();

  drawStars(canvas, ctx);
  drawTrail(canvas, ctx);
  drawPlanets(canvas, ctx);
  drawDestinationAndArrow(canvas, ctx);
  drawShip(canvas, ctx);
  drawJoystickVector(canvas, ctx);
}