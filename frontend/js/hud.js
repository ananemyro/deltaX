import { sim } from "./state.js";

const el = {};

export function initHUD() {
  el.progressFill = document.getElementById("progressFill");
  el.progressText = document.getElementById("progressText");
  el.speedText = document.getElementById("speedText");
  el.probText = document.getElementById("probText");

  el.distText = document.getElementById("distText");
  el.speedText2 = document.getElementById("speedText2");
  el.probText2 = document.getElementById("probText2");
  el.timeText = document.getElementById("timeText");

  el.statusDot = document.getElementById("statusDot");
  el.statusText = document.getElementById("statusText");
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export function setStatus(kind, text) {
  el.statusText.textContent = text;
  el.statusDot.className = "dot " + kind;
}

export function updateHUD() {
  if (!sim.state) return;

  const d = sim.state.hud.distance_to_destination;
  const v = sim.state.hud.speed;
  const p = sim.state.hud.success_score;

  if (sim.initialDistance == null) sim.initialDistance = d;
  const prog = clamp(1 - d / Math.max(1e-6, sim.initialDistance), 0, 1);

  el.progressFill.style.width = `${(prog * 100).toFixed(1)}%`;
  el.progressText.textContent = `${Math.round(prog * 100)}%`;

  el.speedText.textContent = fmtSpeedKmS(v);
  el.probText.textContent = `${Math.round(p * 100)}%`;

  el.distText.textContent = fmtDistanceKm(d);
  el.speedText2.textContent = fmtSpeedKmS(v);
  el.probText2.textContent = `${Math.round(p * 100)}%`;
  el.timeText.textContent = fmtTimeSeconds(sim.state.t);

  if (sim.state.hud.status === "success") {
    setStatus("good", "success");
    sim.running = true;
  } else if (sim.state.hud.status === "failed") {
    setStatus("bad", "failed");
    sim.running = true;
  } else {
    setStatus(sim.running ? "run" : "wait", sim.running ? "running" : "ready");
  }
}

function fmtDistanceKm(km) {
  // show in Mkm above 1e6 km
  if (Math.abs(km) >= 1e6) return `${(km / 1e6).toFixed(2)} Mkm`;
  return `${km.toFixed(0)} km`;
}

function fmtSpeedKmS(v) {
  return `${v.toFixed(2)} km/s`;
}

function fmtTimeSeconds(t) {
  if (t >= 86400) return `${(t / 86400).toFixed(2)} d`;
  if (t >= 3600) return `${(t / 3600).toFixed(2)} h`;
  if (t >= 60) return `${(t / 60).toFixed(2)} min`;
  return `${t.toFixed(1)} s`;
}
