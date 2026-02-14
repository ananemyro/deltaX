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

let lastTime = performance.now();

async function tick(now) {
  lastTime = now;

  if (sim.state) {
    if (sim.started && sim.state.hud.status === "running") {
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
    setStatus("wait", "ready");
    requestAnimationFrame(tick);
  } catch (e) {
    console.error(e);
    setStatus("bad", "cannot connect");
    alert("Could not connect to backend at http://127.0.0.1:5000.\nStart Flask app.py first.");
  }
})();