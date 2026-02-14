import { sim } from "./state.js";

const el = {};

const AU_KM = 149_597_870.7;
const KM_PER_UNIT = 1_000_000;              // tweak this
const JOURNEY_SEC_PER_SIM_SEC = 86_400;     // tweak this

function formatJourneyTimeDays(days) {
  if (days < 60) return `${days.toFixed(1)} d`;
  const years = days / 365.25;
  if (years < 2) return `${(days / 30.44).toFixed(1)} mo`;
  return `${years.toFixed(2)} yr`;
}

function unitsToKm(units) {
  return units * KM_PER_UNIT;
}

function speedUnitsToKmPerSec(vUnitsPerSimSec) {
  return vUnitsPerSimSec * KM_PER_UNIT / JOURNEY_SEC_PER_SIM_SEC;
}

function simTimeToDays(tSimSec) {
  return (tSimSec * JOURNEY_SEC_PER_SIM_SEC) / 86_400;
}

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

  const dUnits = sim.state.hud.distance_to_destination;
  const vUnits = sim.state.hud.speed;

  if (sim.initialDistance == null) sim.initialDistance = dUnits;
  if (sim.initialSpeed == null) sim.initialSpeed = vUnits;

  const p = sim.state.hud.success_probability;

  // anchored display targets
  const START_DISTANCE_AU = 10.0;
  const START_SPEED_KMS = 30.0;

  // Display conversions
  const dAU = START_DISTANCE_AU * (dUnits / Math.max(1e-6, sim.initialDistance));
  const vKmS = START_SPEED_KMS * (vUnits / Math.max(1e-6, sim.initialSpeed));
  const dKm = dAU * AU_KM;
  const tDays = simTimeToDays(sim.state.t);

  if (sim.initialDistance == null) sim.initialDistance = dUnits;
  const prog = clamp(1 - dUnits / Math.max(1e-6, sim.initialDistance), 0, 1);

  el.progressFill.style.width = `${(prog * 100).toFixed(1)}%`;
  el.progressText.textContent = `${Math.round(prog * 100)}%`;

  el.probText.textContent = `${Math.round(p * 100)}%`;
  el.probText2.textContent = `${Math.round(p * 100)}%`;

  el.speedText.textContent = vKmS.toFixed(1);
  el.speedText2.textContent = vKmS.toFixed(1);

  el.distText.textContent = dKm.toFixed(0);
  el.timeText.textContent = formatJourneyTimeDays(tDays);

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