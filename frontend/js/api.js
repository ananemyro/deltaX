import { API } from "./config.js";
import { sim, setState } from "./state.js";
import { updateHUD } from "./hud.js";

export async function apiGetState() {
  const res = await fetch(`${API}/state`);
  const data = await res.json();
  setState(data);
  return data;
}

export async function apiReset(seed = null) {
  const body = seed == null ? {} : { seed };
  const res = await fetch(`${API}/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  setState(data);

  sim.initialDistance = data.hud.distance_to_destination;
  sim.trail.length = 0;
  sim.trail.push({ x: data.rocket.x, y: data.rocket.y });

  updateHUD();
  return data;
}

export async function apiStep(dt) {
  const res = await fetch(`${API}/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dt }),
  });
  const data = await res.json();
  setState(data);

  sim.trail.push({ x: data.rocket.x, y: data.rocket.y });
  updateHUD();
  return data;
}

export async function apiPlan(dvx, dvy) {
  const res = await fetch(`${API}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dvx, dvy }),
  });
  const data = await res.json();
  setState(data);

  updateHUD();
  return data;
}
