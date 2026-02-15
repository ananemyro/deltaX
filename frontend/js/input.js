import { sim } from "./state.js";
import { JOY_DV_MAX, JOY_GAIN } from "./config.js";
import { apiPlan, apiReset } from "./api.js";
import { resetHudFlags } from "./hud.js";

resetHudFlags();

const G0 = 9.81;
const TARGET_MAX_G = 1.0;
const DV_UNITS_ARE_KMS = true;

function plannedDvMag(mag) {
  // Unclamped magnitude would be JOY_GAIN * mag, then clamp to JOY_DV_MAX
  return Math.min(JOY_DV_MAX, JOY_GAIN * mag);
}

function dvToG(dv) {
  // Convert dv to m/s if we’re interpreting dv as km/s
  const dv_mps = DV_UNITS_ARE_KMS ? dv * 1000 : dv;

  // Pick burn time so that dvMax maps to TARGET_MAX_G
  const dvMax = plannedDvMag(1.0);
  const dvMax_mps = DV_UNITS_ARE_KMS ? dvMax * 1000 : dvMax;

  // Avoid divide-by-zero if dvMax is 0
  if (dvMax_mps <= 1e-9) return 0.0;

  const burnSec = dvMax_mps / (TARGET_MAX_G * G0);
  const a_mps2 = dv_mps / burnSec;

  return a_mps2 / G0;
}

function setKnob(joystick, knob, nx, ny) {
  const r = joystick.getBoundingClientRect();
  const radius = Math.min(r.width, r.height) * 0.38;
  const x = nx * radius;
  const y = ny * radius;
  knob.style.left = `calc(50% + ${x}px)`;
  knob.style.top  = `calc(50% + ${y}px)`;
}

function joystickPointer(joystick, evt) {
  const r = joystick.getBoundingClientRect();
  const x = evt.clientX - r.left - r.width / 2;
  const y = evt.clientY - r.top - r.height / 2;
  const radius = Math.min(r.width, r.height) * 0.38;

  const nx = x / radius;
  const ny = y / radius;

  const mm = Math.sqrt(nx * nx + ny * ny);
  const cx = mm > 1 ? nx / mm : nx;
  const cy = mm > 1 ? ny / mm : ny;

  return { nx: cx, ny: cy, mag: Math.min(1, mm) };
}

export function initInput() {
  const resetBtn = document.getElementById("resetBtn");
  const joystick = document.getElementById("joystick");
  const knob = document.getElementById("knob");
  const joystickMag = document.getElementById("joystickMag");

  resetBtn.addEventListener("click", async () => {
      await apiReset();

      // Core flags
      sim.freeze = false;
      sim.missed = false;
      sim.startX = null;
      sim.initialDistance = null;
      sim.initialSpeed = null;

      // Ensure the sim isn't "stuck paused" from an event prompt
      sim.started = true;

      // Reset HUD-related “one-time” flags
      resetHudFlags();

      // Hide overlays
      const successOv = document.getElementById("successOverlay");
      if (successOv) successOv.style.display = "none";

      const missOv = document.getElementById("missOverlay");
      if (missOv) missOv.style.display = "none";

      const orbitalPrompt = document.getElementById("orbitalPrompt");
      if (orbitalPrompt) orbitalPrompt.style.display = "none";

      const planetMenu = document.getElementById("planetMenuOverlay");
      if (planetMenu) planetMenu.style.display = "none";

      // Clear visited planet memory (if you use it)
      if (window.visitedPlanets) window.visitedPlanets.clear();

      // Reset joystick UI state
      sim.joyVec = { x: 0, y: 0 };
      setKnob(joystick, knob, 0, 0);
      joystickMag.textContent = "0.00 g";
    });


  joystick.addEventListener("pointerdown", (evt) => {
    sim.joyActive = true;
    joystick.setPointerCapture(evt.pointerId);

    const j = joystickPointer(joystick, evt);
    sim.joyVec = { x: j.nx, y: j.ny };
    setKnob(joystick, knob, sim.joyVec.x, sim.joyVec.y);

    const dv = plannedDvMag(j.mag);
    joystickMag.textContent = `${dvToG(dv).toFixed(2)} g`;
  });

  joystick.addEventListener("pointermove", (evt) => {
    if (!sim.joyActive) return;

    const j = joystickPointer(joystick, evt);
    sim.joyVec = { x: j.nx, y: j.ny };
    setKnob(joystick, knob, sim.joyVec.x, sim.joyVec.y);

    const dv = plannedDvMag(j.mag);
    joystickMag.textContent = `${dvToG(dv).toFixed(2)} g`;
  });

  joystick.addEventListener("pointerup", async () => {
    sim.joyActive = false;
    sim.started = true;

    const mag = Math.min(1.0, Math.sqrt(sim.joyVec.x ** 2 + sim.joyVec.y ** 2));

    let dvx = -sim.joyVec.x * JOY_GAIN * mag;
    let dvy =  sim.joyVec.y * JOY_GAIN * mag;

    const m = Math.sqrt(dvx * dvx + dvy * dvy);
    if (m > JOY_DV_MAX) {
      dvx = (dvx / m) * JOY_DV_MAX;
      dvy = (dvy / m) * JOY_DV_MAX;
    }

    if (Math.abs(dvx) > 1e-6 || Math.abs(dvy) > 1e-6) {
      await apiPlan(dvx, dvy);
    }

    sim.joyVec = { x: 0, y: 0 };
    setKnob(joystick, knob, 0, 0);
    joystickMag.textContent = "0.00 g";
  });
}
