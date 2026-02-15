// js/main.js
import { STEP_DT } from "./config.js";
import { sim } from "./state.js";
import { initCanvas, updateRenderCamera } from "./canvas.js";
import { initHUD, setStatus } from "./hud.js";
import { apiGetState, apiReset, apiStep } from "./api.js";
import { renderFrame } from "./render.js";
import { initInput } from "./input.js";

const { canvas, ctx } = initCanvas();
initHUD();
initInput();

const overlay = document.getElementById("introOverlay");
const playBtn = document.getElementById("playBtn");

const missOverlay = document.getElementById("missOverlay");

if (playBtn && overlay) {
  playBtn.addEventListener("click", () => {
    overlay.style.display = "none";
    sim.started = true;
    setStatus("wait", "launching...");
  });
}

async function tick() {
  if (sim.state) {
    const s = sim.state.hud.status;

    // ONLY ONE stepping block (and stop stepping if missed)
    if (sim.started && !sim.missed && (s === "ready" || s === "running")) {
      try {
        await apiStep(STEP_DT);
      } catch (e) {
        console.error(e);
        setStatus("bad", "backend error");
      }
    }

    updateRenderCamera();
    renderFrame(canvas, ctx);
    if (missOverlay) {
        missOverlay.style.display = sim.missed ? "grid" : "none";
    }

  }

  requestAnimationFrame(tick);
}

(async function boot() {
  setStatus("wait", "connecting...");
  try {
    await apiGetState();
    await apiReset();

    // Start in "not started" mode so overlay shows
    sim.started = false;
    sim.missed = false;
    sim.startX = null;

    if (overlay) overlay.style.display = "grid";

    setStatus("wait", "ready");
    requestAnimationFrame(tick);
  } catch (e) {
    console.error(e);
    setStatus("bad", "cannot connect");
    alert("Could not connect to backend at http://127.0.0.1:5000.\nStart Flask app.py first.");
  }
})();
