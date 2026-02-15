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
        updatePlanetUI();
      } catch (e) {
        console.error(e);
        setStatus("bad", "backend error");
      }
    }
    if (sim.started && !sim.freeze && !sim.missed && (s === "ready" || s === "running")) {
      await apiStep(STEP_DT);
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



function updatePlanetUI() {
    if (!sim.state) return;
    const orbitalPrompt = document.getElementById("orbitalPrompt");
    const planetMenu = document.getElementById("planetMenuOverlay");
    const latchedId = sim.state.latched_planet_id;

    if (latchedId === null) {
        orbitalPrompt.style.display = "none";
        return;
    }

    const p = sim.state.planets.find(planet => planet.id === latchedId);
    
    // Check if it's a blue planet AND we haven't visited/ignored it yet
    const isBluePlanet = p && p.status === "good";
    const alreadyHandled = window.visitedPlanets.has(latchedId);

    if (isBluePlanet && !alreadyHandled) {
        if (planetMenu.style.display !== "grid") {
            orbitalPrompt.style.display = "flex";
        }
    } else {
        orbitalPrompt.style.display = "none";
    }
}









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
    const planetMenu = document.getElementById("planetMenuOverlay");
    const landBtn = document.getElementById("landBtn");
    const exitBtn = document.getElementById("exitPlanetBtn");

    landBtn.onclick = () => {
        // Mark the current planet as visited
        if (sim.state.latched_planet_id) {
            visitedPlanets.add(sim.state.latched_planet_id);
        }
        
        orbitalPrompt.style.display = "none";
        planetMenu.style.display = "grid";
        sim.started = false; // Pause physics
    };

    // --- NEW LOGIC: FIX FOR THE HICCUP ---
    ignoreBtn.onclick = () => {
        if (sim.state.latched_planet_id) {
            // Treat 'ignoring' as 'visited' so the loop won't show it again
            window.visitedPlanets.add(sim.state.latched_planet_id); 
        }
        orbitalPrompt.style.display = "none";
    };


    exitBtn.onclick = () => {
        planetMenu.style.display = "none";
        // Prompt will stay hidden because we added the ID to visitedPlanets
        sim.started = true; // Resume physics
    };
}





// Call this once during bootup
initPlanetMenu();
