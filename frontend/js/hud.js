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
  const p = sim.state.hud.success_probability;

  if (sim.initialDistance == null) sim.initialDistance = d;
  const prog = clamp(1 - d / Math.max(1e-6, sim.initialDistance), 0, 1);

  el.progressFill.style.width = `${(prog * 100).toFixed(1)}%`;
  el.progressText.textContent = `${Math.round(prog * 100)}%`;

  el.speedText.textContent = v.toFixed(2);
  el.probText.textContent = `${Math.round(p * 100)}%`;

  el.distText.textContent = d.toFixed(1);
  el.speedText2.textContent = v.toFixed(2);
  el.probText2.textContent = `${Math.round(p * 100)}%`;
  el.timeText.textContent = sim.state.t.toFixed(2);

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
