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





// ------ WHAT IT DOES
// updatePlanetUI serves as the logic controller that monitors your ship's interaction with planets 
// to trigger the new landing menus.
// if the planet is orange, pop up will be hidden
// ------

// version 1: last working version 
// function updatePlanetUI() {
//     if (!sim.state) return;

//     const orbitalPrompt = document.getElementById("orbitalPrompt");
//     const planetMenu = document.getElementById("planetMenuOverlay");
    
//     // Check if we are latched to a planet
//     const latchedId = sim.state.latched_planet_id;
    
//     if (latchedId !== null) {
//         // Find the specific planet in the data
//         const p = sim.state.planets.find(planet => planet.id === latchedId);
        
//         // Only show for "good" (Blue) planets
//         if (p && p.status === "good") {
//             // Only show prompt if the large menu isn't already open
//             if (planetMenu.style.display !== "grid") {
//                 orbitalPrompt.style.display = "flex";
//             } else {
//                 orbitalPrompt.style.display = "none";
//             }
//             return; // Exit early to keep UI visible
//         }
//     }
    
//     // If not latched or not a blue planet, hide everything
//     orbitalPrompt.style.display = "none";
// }


let ignoredPlanetId = null;

// version 2: great
// function updatePlanetUI() {
//     if (!sim.state) return;
//     const orbitalPrompt = document.getElementById("orbitalPrompt");
//     const planetMenu = document.getElementById("planetMenuOverlay");
//     const latchedId = sim.state.latched_planet_id;

//     // Reset ignore flag if we leave the planet
//     if (latchedId === null) {
//         ignoredPlanetId = null;
//         orbitalPrompt.style.display = "none";
//         return;
//     }

//     const p = sim.state.planets.find(planet => planet.id === latchedId);
    
//     // Check if it's a blue planet and we haven't clicked "Ignore" yet
//     if (p && p.status === "good" && latchedId !== ignoredPlanetId) {
//         if (planetMenu.style.display !== "grid") {
//             orbitalPrompt.style.display = "flex";
//         }
//     } else {
//         orbitalPrompt.style.display = "none";
//     }
// }


window.visitedPlanets = new Set(); // Using window makes it global


// version3 : good, but the pop up is not disaperaing, when choosing to stay in orbit
// js/main.js
// function updatePlanetUI() {
//     if (!sim.state) return;
//     const orbitalPrompt = document.getElementById("orbitalPrompt");
//     const planetMenu = document.getElementById("planetMenuOverlay");
//     const latchedId = sim.state.latched_planet_id;

//     // If we aren't latched, just hide the prompt
//     if (latchedId === null) {
//         orbitalPrompt.style.display = "none";
//         return;
//     }

//     const p = sim.state.planets.find(planet => planet.id === latchedId);
    
//     // Condition: Is it a blue planet AND have we NOT visited it yet?
//     const isBluePlanet = p && p.status === "good";
//     const alreadyVisited = visitedPlanets.has(latchedId);

//     if (isBluePlanet && !alreadyVisited) {
//         // Only show if the big menu is closed
//         if (planetMenu.style.display !== "grid") {
//             orbitalPrompt.style.display = "flex";
//         }
//     } else {
//         // Hide if we've already landed here or it's not a blue planet
//         orbitalPrompt.style.display = "none";
//     }
// }


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




// version 5: pulling from events.py
// js/main.js
// let isFetchingEvent = false; 

// async function updatePlanetUI() {
//     if (!sim.state) return;
//     const orbitalPrompt = document.getElementById("orbitalPrompt");
//     const eventText = document.getElementById("orbitalEventText");
//     const latchedId = sim.state.latched_planet_id;

//     // Reset when you leave orbit
//     if (latchedId === null) {
//         orbitalPrompt.style.display = "none";
//         isFetchingEvent = false; 
//         return;
//     }

//     const p = sim.state.planets.find(planet => planet.id === latchedId);
//     const alreadyHandled = window.visitedPlanets.has(latchedId);

//     // Only trigger if: Good planet AND haven't handled it AND not currently fetching
//     if (p && p.status === "good" && !alreadyHandled) {
//         if (orbitalPrompt.style.display === "none" && !isFetchingEvent) {
//             isFetchingEvent = true; // Lock the logic
            
//             try {
//                 // Pulls random story from events.py via backend
//                 const res = await fetch('http://127.0.0.1:5000/api/land', { method: 'POST' });
//                 const data = await res.json();
                
//                 // Update the text in the prompt dynamically
//                 if (eventText) eventText.textContent = data.event.text;
                
//                 orbitalPrompt.style.display = "flex";
//             } catch (e) {
//                 console.error("Event fetch failed", e);
//                 isFetchingEvent = false; // Release lock on error
//             }
//         }
//     } else {
//         orbitalPrompt.style.display = "none";
//     }
// }





// Update the ignoreBtn in initPlanetMenu
document.getElementById("ignoreBtn").onclick = () => {
    ignoredPlanetId = sim.state.latched_planet_id; // Remember this planet
    document.getElementById("orbitalPrompt").style.display = "none";
};






// --- this is so that when the user interacts with the button, some actions can be performed
// --- Button Setup for Planet Landing ---
// last working version
// function initPlanetMenu() {
//     const orbitalPrompt = document.getElementById("orbitalPrompt");
//     const planetMenu = document.getElementById("planetMenuOverlay");
//     const landBtn = document.getElementById("landBtn");
//     const ignoreBtn = document.getElementById("ignoreBtn");
//     const exitBtn = document.getElementById("exitPlanetBtn");

//     // "YES, LAND" -> Show large window, hide small prompt
//     landBtn.onclick = () => {
//         orbitalPrompt.style.display = "none";
//         planetMenu.style.display = "grid"; // Ana's style uses display: grid
//         sim.started = false; // Pause game while menu is open
//     };

//     // "NO, STAY IN ORBIT" -> Just hide the prompt
//     ignoreBtn.onclick = () => {
//         orbitalPrompt.style.display = "none";
//         // Prompt will reappear in the next tick if updatePlanetUI() sees we are still latched
//     };

//     // "EXIT" (on large window) -> Back to the game
//     exitBtn.onclick = () => {
//         planetMenu.style.display = "none";
//         sim.started = true; // Resume the simulation
//     };
// }

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