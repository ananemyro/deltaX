// js/main.js
import { STEP_DT } from "./config.js";
import { sim } from "./state.js";
import { initCanvas, updateRenderCamera } from "./canvas.js";
import { initHUD, setStatus } from "./hud.js";
import { renderFrame } from "./render.js";
import { initInput } from "./input.js";
import { apiGetState, apiReset, apiStep, apiResolveEvent } from "./api.js";

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

    if (sim.started && !sim.freeze && !sim.missed && (s === "ready" || s === "running")) {
      await apiStep(STEP_DT);

      const status = sim.state?.hud?.status;

      // Show "And then..." overlay on depletion deaths
      if (status === "failed") {
        const r = sim.state?.fail_reason;

        const depletionReasons = new Set([
          "oxygen_depleted",
          "morale_depleted",
          "water_depleted",
          "food_depleted",
        ]);

        if (depletionReasons.has(r)) {
          sim.missed = true;    // reuse existing "And then..." overlay logic
          sim.freeze = true;    // stop stepping
          sim.started = false;  // stop further stepping
        } else {
          // Non-depletion failures still freeze + show miss overlay
          sim.freeze = true;
          sim.started = false;
          const ov = document.getElementById("missOverlay");
          if (ov) ov.style.display = "grid";
        }
      }

      updatePlanetUI();
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


let ignoredPlanetId = null;

window.visitedPlanets = new Set(); // Using window makes it global

// version 4: last working version before trying to pull event from events.py
async function updatePlanetUI() {
  if (!sim.state) return;

  const orbitalPrompt = document.getElementById("orbitalPrompt");
  const eventText = document.getElementById("orbitalEventText");
  const landBtn = document.getElementById("landBtn");
  const ignoreBtn = document.getElementById("ignoreBtn");

  const ev = sim.state.pending_event;

  if (!ev) {
    if (orbitalPrompt) orbitalPrompt.style.display = "none";
    return;
  }

  // Show prompt text
  if (eventText) eventText.textContent = ev.prompt || "Decision required.";

  // Update button labels dynamically (works for any 2-choice event)
  if (landBtn && ev.choices?.[0]) landBtn.textContent = ev.choices[0].label ?? "YES";
  if (ignoreBtn && ev.choices?.[1]) ignoreBtn.textContent = ev.choices[1].label ?? "NO";

  // Show prompt overlay
  if (orbitalPrompt) orbitalPrompt.style.display = "flex";

  // Pause stepping while choice is up
  sim.started = false;
}

// Update the ignoreBtn in initPlanetMenu
document.getElementById("ignoreBtn").onclick = () => {
    ignoredPlanetId = sim.state.latched_planet_id; // Remember this planet
    document.getElementById("orbitalPrompt").style.display = "none";
};

function initPlanetMenu() {
  const orbitalPrompt = document.getElementById("orbitalPrompt");
  const landBtn = document.getElementById("landBtn");
  const ignoreBtn = document.getElementById("ignoreBtn");

  landBtn.onclick = async () => {
    const ev = sim.state?.pending_event;
    if (!ev?.choices?.[0]) return;

    await apiResolveEvent(ev.choices[0].id);
    orbitalPrompt.style.display = "none";
    sim.started = true;
  };

  ignoreBtn.onclick = async () => {
    const ev = sim.state?.pending_event;
    if (!ev?.choices?.[1]) return;

    await apiResolveEvent(ev.choices[1].id);
    orbitalPrompt.style.display = "none";
    sim.started = true;
  };
}


// Call this once during bootup
initPlanetMenu();
