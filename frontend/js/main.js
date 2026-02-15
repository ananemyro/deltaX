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

// Intro overlay hookup
const overlay = document.getElementById("introOverlay");
const playBtn = document.getElementById("playBtn");

if (playBtn && overlay) {
  playBtn.addEventListener("click", () => {
    overlay.style.display = "none";
    sim.started = true;
    setStatus("wait", "launching...");
  });
} else {
  // If these are missing, you won't crash—game still runs.
  console.warn("Intro overlay elements missing:", { overlayFound: !!overlay, playBtnFound: !!playBtn });
}

let lastTime = performance.now();

async function tick(now) {
  lastTime = now;

  if (sim.state) {
    const s = sim.state.hud.status;

    // ✅ Step only when "ready" or "running" AND after Play
    if (sim.started && (s === "ready" || s === "running")) {
      try {
        await apiStep(STEP_DT);
      } catch (e) {
        console.error(e);
        setStatus("bad", "backend error");
      }
    }

    updateRenderCamera();
    renderFrame(canvas, ctx);
  }

  requestAnimationFrame(tick);
}

(async function boot() {
  setStatus("wait", "connecting...");
  try {
    await apiGetState();
    await apiReset();

    // Start in "not started" mode so overlay shows and sim doesn't step
    sim.started = false;
    if (overlay) overlay.style.display = "grid";

    setStatus("wait", "ready");
    requestAnimationFrame(tick);
  } catch (e) {
    console.error(e);
    setStatus("bad", "cannot connect");
    alert("Could not connect to backend at http://127.0.0.1:5000.\nStart Flask app.py first.");
  }
})();
