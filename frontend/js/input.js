import { sim } from "./state.js";
import { JOY_DV_MAX, JOY_GAIN } from "./config.js";
import { apiPlan, apiReset } from "./api.js";

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
    sim.started = false;
    sim.joyVec = { x: 0, y: 0 };
    setKnob(joystick, knob, 0, 0);
    joystickMag.textContent = "0.00";
  });

  joystick.addEventListener("pointerdown", (evt) => {
    sim.joyActive = true;
    joystick.setPointerCapture(evt.pointerId);

    const j = joystickPointer(joystick, evt);
    sim.joyVec = { x: j.nx, y: j.ny };
    setKnob(joystick, knob, sim.joyVec.x, sim.joyVec.y);
    joystickMag.textContent = j.mag.toFixed(2);
  });

  joystick.addEventListener("pointermove", (evt) => {
    if (!sim.joyActive) return;

    const j = joystickPointer(joystick, evt);
    sim.joyVec = { x: j.nx, y: j.ny };
    setKnob(joystick, knob, sim.joyVec.x, sim.joyVec.y);
    joystickMag.textContent = j.mag.toFixed(2);
  });

  joystick.addEventListener("pointerup", async () => {
    sim.joyActive = false;
    sim.started = true;

    const mag = Math.min(1.0, Math.sqrt(sim.joyVec.x * sim.joyVec.x + sim.joyVec.y * sim.joyVec.y));

    let dvx = -sim.joyVec.x * JOY_GAIN * mag;
    let dvy = sim.joyVec.y * JOY_GAIN * mag;

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
    joystickMag.textContent = "0.00";
  });
}