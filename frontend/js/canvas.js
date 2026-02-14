import { sim } from "./state.js";
import { CAM_ALPHA_UI, LOOKAHEAD_UI } from "./config.js";

export function initCanvas() {
  const canvas = document.getElementById("c");
  const ctx = canvas.getContext("2d");

  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(rect.width * dpr);
    canvas.height = Math.floor(rect.height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  return { canvas, ctx, resizeCanvas };
}

export function worldToScreen(canvas, wx, wy) {
  const zoom = sim.renderCam.zoom || 1.0;
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;
  return {
    x: (wx - sim.renderCam.cx) * zoom + w / 2,
    y: (sim.renderCam.cy - wy) * zoom + h / 2,
  };
}

export function screenToWorld(canvas, sx, sy) {
  const zoom = sim.renderCam.zoom || 1.0;
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;
  return {
    x: (sx - w / 2) / zoom + sim.renderCam.cx,
    y: sim.renderCam.cy - (sy - h / 2) / zoom,
  };
}

export function updateRenderCamera() {
  if (!sim.state) return;

  const r = sim.state.rocket;
  const z = (sim.state.camera && sim.state.camera.zoom) ? sim.state.camera.zoom : 1.0;
  sim.renderCam.zoom = z;

  const tx = r.x + r.vx * LOOKAHEAD_UI;
  const ty = r.y + r.vy * LOOKAHEAD_UI;

  if (!Number.isFinite(sim.renderCam.cx)) {
    sim.renderCam.cx = r.x;
    sim.renderCam.cy = r.y;
  }

  sim.renderCam.cx += (tx - sim.renderCam.cx) * CAM_ALPHA_UI;
  sim.renderCam.cy += (ty - sim.renderCam.cy) * CAM_ALPHA_UI;
}