import { sim } from "./state.js";

const el = {};

const AU_KM = 149_597_870.7;
const JOURNEY_SEC_PER_SIM_SEC = 86_400;

let hudFrameCount = 0;
let lastBurnCount = 3;
let successShown = false;

export function resetHudFlags() {
  successShown = false;
}

function formatJourneyTimeDays(days) {
  if (days < 60) return `${days.toFixed(1)} d`;
  const years = days / 365.25;
  if (years < 2) return `${(days / 30.44).toFixed(1)} mo`;
  return `${years.toFixed(2)} yr`;
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

  el.burnOverlay = document.getElementById("spaceBurnOverlay");
  el.burnCount = document.getElementById("burnCountDisplay");
  el.burnStatus = document.getElementById("burnStatus");
}

function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

export function setStatus(kind, text) {
  if (!el.statusText || !el.statusDot) return;
  el.statusText.textContent = text;
  el.statusDot.className = "dot " + kind;
}

export function updateHUD() {
  if (!sim.state) return;

  const dUnits = sim.state.hud.distance_to_destination;
  const vUnits = sim.state.hud.speed;
  const p = sim.state.hud.success_probability;
  const tSimSec = sim.state.t;
  const status = sim.state.hud.status;

  if (sim.initialDistance == null) sim.initialDistance = dUnits;
  if (sim.initialSpeed == null) sim.initialSpeed = vUnits;

  const START_DISTANCE_AU = 10.0;
  const START_SPEED_KMS = 30.0;

  const dAU = START_DISTANCE_AU * (dUnits / Math.max(1e-6, sim.initialDistance));
  const vKmS = START_SPEED_KMS * (vUnits / Math.max(1e-6, sim.initialSpeed));
  const dKm = dAU * AU_KM;
  const tDays = simTimeToDays(tSimSec);

  const prog = clamp(1 - dUnits / Math.max(1e-6, sim.initialDistance), 0, 1);

  const ARRIVE_EPS = 0.03;
  const arrivedVisually = (dUnits / Math.max(1e-6, sim.initialDistance)) < ARRIVE_EPS;

  const done = (status === "success") || arrivedVisually;

    if (done && !successShown) {
      const ov = document.getElementById("successOverlay");
      if (ov) ov.style.display = "grid";

      // freeze stepping without messing with "missed"
      sim.freeze = true;

      successShown = true;
    }

  const progShown = done ? 1 : prog;
  const pShown = done ? 1 : p;

  hudFrameCount++;
  const shouldUpdateText = hudFrameCount % 4 === 0;

  el.progressFill.style.width = `${(progShown * 100).toFixed(1)}%`;

  const resources = ["crew_health", "ship_health", "morale", "oxygen", "food", "water", "fuel"];


  resources.forEach((res) => {
    let val = sim.state[res] !== undefined ? sim.state[res] : 100;
    val = Math.max(0, Math.min(100, val));

    const fillEl = document.getElementById(`${res}Fill`);
    const textEl = document.getElementById(`${res}Text`);
    if (fillEl) fillEl.style.width = `${val}%`;
    if (textEl) textEl.textContent = `${Math.round(val)}%`;
  });

  if (shouldUpdateText) {
    el.progressText.textContent = `${Math.round(progShown * 100)}%`;
    el.speedText.textContent = vKmS.toFixed(1);
    el.speedText2.textContent = vKmS.toFixed(1);

    el.probText.textContent = `${Math.round(pShown * 100)}%`;
    el.probText2.textContent = `${Math.round(pShown * 100)}%`;

    el.distText.textContent = Math.round(dKm).toLocaleString();
    el.timeText.textContent = formatJourneyTimeDays(tDays);

    resources.forEach((res) => {
      let val = sim.state[res] !== undefined ? sim.state[res] : 100;
      val = Math.max(0, Math.min(100, val));
      const textEl = document.getElementById(`${res}Text`);
      const fillEl = document.getElementById(`${res}Fill`);

      if (textEl) textEl.textContent = `${Math.round(val)}%`;
      if (fillEl && res === "crew_health") {
        if (val < 30) fillEl.classList.add("critical");
        else fillEl.classList.remove("critical");
      }
    });

    const currentBurns = sim.state.space_burns_left ?? 3;
    const canSpaceBurn = sim.state.can_space_burn ?? true;
    const isLatched = sim.state.latched_planet_id !== null;

    if (el.burnCount) el.burnCount.textContent = currentBurns;

    if (currentBurns < lastBurnCount && el.burnOverlay) {
      el.burnOverlay.classList.remove("flash-red");
      void el.burnOverlay.offsetWidth;
      el.burnOverlay.classList.add("flash-red");
    }
    lastBurnCount = currentBurns;

    if (el.burnStatus) {
      if (isLatched) {
        el.burnStatus.textContent = "ORBITAL: UNLIMITED";
        el.burnStatus.style.color = "var(--good)";
      } else if (!canSpaceBurn) {
        el.burnStatus.textContent = "LIMIT HIT: LATCH TO RESET";
        el.burnStatus.style.color = "var(--bad)";
      } else {
        el.burnStatus.textContent = "READY";
        el.burnStatus.style.color = "var(--accent)";
      }
    }
  }

  // Mission status label
  if (done) {
    setStatus("good", "success");
  } else if (status === "failed") {
    setStatus("bad", "failed");
  } else if (sim.missed) {
    setStatus("bad", "missed");
  } else {
    setStatus(sim.running ? "run" : "wait", sim.running ? "running" : "ready");
  }
}
