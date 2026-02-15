import { sim } from "./state.js";
import { STAR_COUNT, SHIP_SIZE, DEST_EDGE_ARROW_SIZE } from "./config.js";
import { worldToScreen } from "./canvas.js";
import { drawEarthAtScreen } from "./earth.js";

const stars = Array.from({ length: STAR_COUNT }, () => ({
  x: Math.random(),
  y: Math.random(),
  r: Math.random() * 1.6 + 0.2,
  a: Math.random() * 0.6 + 0.2,
}));

const AU_KM = 149_597_870.7;

function remainingDistanceUnits() {
  const r = sim.state.rocket;
  const d = sim.state.destination;
  const dx = d.x - r.x;
  const dy = d.y - r.y;
  return Math.sqrt(dx * dx + dy * dy);
}

function len(x, y) { return Math.sqrt(x * x + y * y); }

function drawStars(canvas, ctx) {
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  for (const s of stars) {
    ctx.beginPath();
    ctx.arc(s.x * w, s.y * h, s.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${s.a})`;
    ctx.fill();
  }
}

function drawTrail(canvas, ctx) {
  if (!sim.state || sim.trail.length < 2) return;

  ctx.beginPath();
  for (let i = 0; i < sim.trail.length; i++) {
    const p = sim.trail[i];
    const sp = worldToScreen(canvas, p.x, p.y);
    if (i === 0) ctx.moveTo(sp.x, sp.y);
    else ctx.lineTo(sp.x, sp.y);
  }
  ctx.strokeStyle = "rgba(95,227,255,0.22)";
  ctx.lineWidth = 2;
  ctx.stroke();
}




// old version with 'good' and 'bad' 
// function drawPlanets(canvas, ctx) {
//   for (const p of sim.state.planets) {
//     const sp = worldToScreen(canvas, p.x, p.y);
//     const radius = p.radius * sim.state.camera.zoom;

//     ctx.save();
//     ctx.translate(sp.x, sp.y);

//     if (p.mass > 2500 || p.color === "green") {
//       ctx.beginPath();
//       ctx.ellipse(0, 0, radius * 2.2, radius * 0.8, Math.PI / 6, 0, Math.PI * 2);
//       ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
//       ctx.lineWidth = 3;
//       ctx.stroke();
//     }

//     const grad = ctx.createRadialGradient(-radius/3, -radius/3, radius/10, 0, 0, radius);
//     if (p.color === "green") { grad.addColorStop(0, "#a2f3a2"); grad.addColorStop(1, "#27ae60"); }
//     else if (p.color === "red") { grad.addColorStop(0, "#ff7675"); grad.addColorStop(1, "#c0392b"); }
//     else { grad.addColorStop(0, "#dfe6e9"); grad.addColorStop(1, "#636e72"); }

//     ctx.beginPath();
//     ctx.arc(0, 0, radius, 0, Math.PI * 2);
//     ctx.fillStyle = grad;
//     ctx.fill();

//     ctx.globalAlpha = 0.3;
//     if (p.color === "red" || p.radius < 40) {
//       ctx.fillStyle = "rgba(0,0,0,0.2)";
//       ctx.beginPath(); ctx.arc(-radius/2, radius/4, radius/5, 0, Math.PI*2); ctx.fill();
//       ctx.beginPath(); ctx.arc(radius/3, -radius/3, radius/6, 0, Math.PI*2); ctx.fill();
//     } else {
//       ctx.fillStyle = "white";
//       ctx.fillRect(-radius, -radius/4, radius*2, radius/2);
//     }
//     ctx.globalAlpha = 1.0;

//     ctx.beginPath();
//     ctx.arc(0, 0, radius + 5, 0, Math.PI * 2);
//     ctx.strokeStyle = p.color === "green" ? "rgba(46, 204, 113, 0.2)" : "rgba(231, 76, 60, 0.2)";
//     ctx.lineWidth = 4;
//     ctx.stroke();

//     ctx.restore();
//   }
// }




// version 2: this is the good version, it implements like blue, orange and red 
// function drawPlanets(canvas, ctx) {
//   for (const p of sim.state.planets) {
//     const sp = worldToScreen(canvas, p.x, p.y);
//     const radius = p.radius * sim.state.camera.zoom;

//     ctx.save();
//     ctx.translate(sp.x, sp.y);

//     // 1. Planetary Rings (Now checking for "good" or large mass)
//     if (p.mass > 2500 || p.status === "good") {
//       ctx.beginPath();
//       ctx.ellipse(0, 0, radius * 2.2, radius * 0.8, Math.PI / 6, 0, Math.PI * 2);
//       ctx.strokeStyle = "rgba(155, 176, 255, 0.15)";
//       ctx.lineWidth = 3;
//       ctx.stroke();
//     }

//     // 2. Dynamic Gradient: This is the magic part!
//     const grad = ctx.createRadialGradient(-radius/3, -radius/3, radius/10, 0, 0, radius);
    
//     // Use the exact hex color from Python (p.color) 
//     // We mix it with black at the edge to give it that 3D sphere look
//     grad.addColorStop(0, p.color); 
//     grad.addColorStop(1, "#1a1a1a"); 

//     ctx.beginPath();
//     ctx.arc(0, 0, radius, 0, Math.PI * 2);
//     ctx.fillStyle = grad;
//     ctx.fill();

//     // 3. Surface Details
//     ctx.globalAlpha = 0.3;
//     // Red planets (bad) or small ones get craters
//     if (p.status === "bad" || p.radius < 40) {
//       ctx.fillStyle = "rgba(0,0,0,0.2)";
//       ctx.beginPath(); ctx.arc(-radius/2, radius/4, radius/5, 0, Math.PI*2); ctx.fill();
//       ctx.beginPath(); ctx.arc(radius/3, -radius/3, radius/6, 0, Math.PI*2); ctx.fill();
//     } else {
//       // "Good" or "Okay" planets get a reflective shine
//       ctx.fillStyle = "white";
//       ctx.fillRect(-radius, -radius/4, radius*2, radius/2);
//     }
//     ctx.globalAlpha = 1.0;

//     // 4. Outer Atmosphere Glow
//     ctx.beginPath();
//     ctx.arc(0, 0, radius + 5, 0, Math.PI * 2);
//     // Use the planet's own color with low opacity for the glow
//     ctx.strokeStyle = p.color + "44"; // Adding '44' to the hex makes it transparent
//     ctx.lineWidth = 4;
//     ctx.stroke();

//     ctx.restore();
//   }
// }



// version3: implementation of atching
function drawPlanets(canvas, ctx) {
  for (const p of sim.state.planets) {
    const sp = worldToScreen(canvas, p.x, p.y);
    const zoom = sim.state.camera.zoom;
    const radius = p.radius * zoom;
    
    // Match the "Capture Zone" value from your physics (radius + 40)
    const orbitRadius = (p.radius + 20.0) * zoom; 

    ctx.save();
    ctx.translate(sp.x, sp.y);

    // --- 1. NEW: Dotted Orbit Line ---
    // This draws the "hitbox" for the latching mechanic
    ctx.beginPath();
    ctx.arc(0, 0, orbitRadius, 0, Math.PI * 2);
    ctx.setLineDash([5, 8]); // Creates the dotted effect [dash length, gap length]
    ctx.strokeStyle = "rgba(255, 255, 255, 0.25)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.setLineDash([]); // ALWAYS reset this so other lines aren't dotted!


        // Check if the rocket is latched to THIS planet and if it's an "okay" (orange) one
    if (sim.state.latched_planet_id === p.id && p.status === "okay") {
      const countdown = sim.state.countdown;
      
      // Turn text red and make it bigger when time is running out
      ctx.fillStyle = countdown < 3 ? "#ff7675" : "white"; 
      ctx.font = "bold 18px monospace";
      ctx.textAlign = "center";
      
      // Draw the seconds remaining above the planet
      ctx.fillText(Math.ceil(countdown) + "s", 0, -radius - 30);
      
      // Visual emergency pulse when under 3 seconds
      if (countdown < 3) {
        ctx.beginPath();
        ctx.arc(0, 0, radius + 15, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 44, 44, ${0.3 + Math.sin(Date.now()/100)*0.2})`;
        ctx.lineWidth = 4;
        ctx.stroke();
      }
    }

    // 2. Planetary Rings (For "good" or large mass)
    if (p.mass > 2500 || p.status === "good") {
      ctx.beginPath();
      ctx.ellipse(0, 0, radius * 2.2, radius * 0.8, Math.PI / 6, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(155, 176, 255, 0.15)";
      ctx.lineWidth = 3;
      ctx.stroke();
    }


    

    // 3. Dynamic Gradient (Sphere effect)
    const grad = ctx.createRadialGradient(-radius/3, -radius/3, radius/10, 0, 0, radius);
    grad.addColorStop(0, p.color); 
    grad.addColorStop(1, "#1a1a1a"); 

    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = grad;
    ctx.fill();

    // 4. Surface Details (Craters vs Shine)
    ctx.globalAlpha = 0.3;
    if (p.status === "bad" || p.radius < 40) {
      ctx.fillStyle = "rgba(0,0,0,0.2)";
      ctx.beginPath(); ctx.arc(-radius/2, radius/4, radius/5, 0, Math.PI*2); ctx.fill();
      ctx.beginPath(); ctx.arc(radius/3, -radius/3, radius/6, 0, Math.PI*2); ctx.fill();
    } else {
      ctx.fillStyle = "white";
      ctx.fillRect(-radius, -radius/4, radius*2, radius/2);
    }
    ctx.globalAlpha = 1.0;

    // 5. Outer Atmosphere / Latch Glow
    // If the rocket is currently latched to this planet, make it pulse or glow brighter
    const isLatched = sim.state.latched_planet_id === p.id;
    ctx.beginPath();
    ctx.arc(0, 0, radius + 5, 0, Math.PI * 2);
    ctx.strokeStyle = isLatched ? "white" : p.color + "44"; 
    ctx.lineWidth = isLatched ? 3 : 4;
    ctx.stroke();

    ctx.restore();
  }
}


//version 3: patchy version, not working properly
// New function that will have the flsahing timer for orange-> red timers
// function drawGlobalWarning(canvas, ctx) {
//   // 1. Check if we are even latched
//   const latchedId = sim.state.latched_planet_id;
//   if (latchedId === null) return;

//   const countdown = sim.state.countdown;
  
//   // 2. Find the planet
//   const currentPlanet = sim.state.planets.find(p => p.id === latchedId);

//   // 3. Only show if it's a ticking orange ("okay") planet
//   if (currentPlanet && currentPlanet.status === "okay") {
//     const w = canvas.getBoundingClientRect().width;
//     const opacity = 0.4 + Math.sin(Date.now() / 150) * 0.4;

//     // version 0
//     // ctx.save();
    
//     // // --- CRITICAL FIX: Reset the "painter" to screen coordinates (0,0) ---
//     // // This ignores any previous planet translations
//     // ctx.setTransform(1, 0, 0, 1, 0, 0);
    
//     // // Position of the box Timer: Top Right Corner
//     // const boxW = 180;
//     // const boxH = 60;
//     // const padding = 20;
//     // const x = w - boxW - padding;
//     // const y = padding;
//     // let x = w - boxW - 20;
//     // let y = 20;

//     // Inside drawGlobalWarning in render.js
//   ctx.save();

//   // FIX: Use devicePixelRatio to match the rest of your UI scaling
//   const dpr = window.devicePixelRatio || 1;
//   ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

//   // Position of the box Timer: Top Right Corner
//   const boxW = 180;
//   const boxH = 60;
//   const padding = 20;
//   const x = (w / dpr) - boxW - padding; // Adjust X for scaling
//   const y = padding;


//     // if (countdown < 3) {
//     //   // Shake the box randomly by a few pixels
//     //   x += (Math.random() - 0.5) * 5;
//     //   y += (Math.random() - 0.5) * 5;
//     // }



//     // Draw the Red Background Box
//     ctx.fillStyle = `rgba(231, 76, 60, ${opacity})`;
//     ctx.beginPath();
//     ctx.rect(x, y, boxW, boxH); 
//     ctx.fill();

//     // Draw the Border
//     ctx.strokeStyle = "white";
//     ctx.lineWidth = 2;
//     ctx.stroke();

//     // Draw Text
//     ctx.fillStyle = "white";
//     ctx.font = "bold 14px monospace";
//     ctx.textAlign = "center";
//     ctx.fillText("STABILITY WARNING", x + boxW / 2, y + 25);

//     ctx.font = "bold 24px monospace";
//     // Show countdown with 2 decimal places for intensity
//     ctx.fillText(countdown.toFixed(2) + "s", x + boxW / 2, y + 50);

//     ctx.restore();
//   }
// }


// versioj 4: better, but still out of place
// function drawGlobalWarning(canvas, ctx) {
//   const latchedId = sim.state.latched_planet_id;
//   if (latchedId === null) return;

//   const currentPlanet = sim.state.planets.find(p => p.id === latchedId);
//   if (currentPlanet && currentPlanet.status === "okay") {
//     const countdown = sim.state.countdown;
//     const w = canvas.getBoundingClientRect().width;
//     const opacity = 0.4 + Math.sin(Date.now() / 150) * 0.4;

//     ctx.save();
    
//     // --- FIX 1: Use the correct pixel ratio for your screen ---
//     const dpr = window.devicePixelRatio || 1;
//     ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    
//     // --- FIX 2: Move it further down so it isn't hidden by the progression chart ---
//     const boxW = 180;
//     const boxH = 60;
//     const padding = 20;
    
//     // Position it in the Top Right, but below the top of the screen
//     const x = w - boxW - padding;
//     const y = padding + 100; // Increased padding from 20 to 120

//     // Draw the Red Background Box
//     ctx.fillStyle = `rgba(231, 76, 60, ${opacity})`;
//     ctx.beginPath();
//     ctx.roundRect(x, y, boxW, boxH, 8); // Use roundRect for consistent UI style
//     ctx.fill();

//     ctx.strokeStyle = "white";
//     ctx.lineWidth = 2;
//     ctx.stroke();

//     // Draw Text
//     ctx.fillStyle = "white";
//     ctx.font = "bold 14px monospace";
//     ctx.textAlign = "center";
//     ctx.fillText("STABILITY WARNING", x + boxW / 2, y + 25);

//     ctx.font = "bold 24px monospace";
//     ctx.fillText(countdown.toFixed(2) + "s", x + boxW / 2, y + 52);

//     ctx.restore();
//   }
// }


function drawGlobalWarning(canvas, ctx) {
  // 1. Check if we are even latched
  const latchedId = sim.state.latched_planet_id;
  if (latchedId === null) return;

  const countdown = sim.state.countdown;
  
  // 2. Find the planet
  const currentPlanet = sim.state.planets.find(p => p.id === latchedId);

  // 3. Only show if it's a ticking orange ("okay") planet
  if (currentPlanet && currentPlanet.status === "okay") {
    const w = canvas.getBoundingClientRect().width;
    const opacity = 0.4 + Math.sin(Date.now() / 150) * 0.4;

    ctx.save();
    
    // --- CRITICAL FIX: Reset the "painter" to screen coordinates (0,0) ---
    // This ignores any previous planet translations
    ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);
    
    // Position of the box Timer: Top Right Corner
    const boxW = 180;
    const boxH = 60;
    const padding = 20;
    const x = w - boxW - padding;
    const y = padding;
    // let x = w - boxW - 20;
    // let y = 20;


    // if (countdown < 3) {
    //   // Shake the box randomly by a few pixels
    //   x += (Math.random() - 0.5) * 5;
    //   y += (Math.random() - 0.5) * 5;
    // }



    // Draw the Red Background Box
    ctx.fillStyle = `rgba(231, 76, 60, ${opacity})`;
    ctx.beginPath();
    ctx.rect(x, y, boxW, boxH); 
    ctx.fill();

    // Draw the Border
    ctx.strokeStyle = "white";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw Text
    ctx.fillStyle = "white";
    ctx.font = "bold 14px monospace";
    ctx.textAlign = "center";
    ctx.fillText("STABILITY WARNING", x + boxW / 2, y + 25);

    ctx.font = "bold 24px monospace";
    // Show countdown with 2 decimal places for intensity
    ctx.fillText(countdown.toFixed(2) + "s", x + boxW / 2, y + 50);

    ctx.restore();
  }
}








function drawShip(canvas, ctx) {
  const r = sim.state.rocket;
  const sp = worldToScreen(canvas, r.x, r.y);

  ctx.save();
  ctx.translate(sp.x, sp.y);

  const ang = Math.atan2(r.vy, r.vx);
  ctx.rotate(-ang);

  const scale = 1.4;

  const speed = Math.sqrt(r.vx * r.vx + r.vy * r.vy);
  if (speed > 0.1) {
    const flicker = Math.random() * 5;
    const flameLen = (15 + speed * 5) * scale + flicker;

    ctx.beginPath();
    ctx.moveTo(-10, 0);
    ctx.quadraticCurveTo(-15, -8, -10 - flameLen, 0);
    ctx.quadraticCurveTo(-15, 8, -10, 0);
    ctx.fillStyle = "rgba(255, 120, 0, 0.6)";
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(-10, 0);
    ctx.quadraticCurveTo(-12, -4, -10 - (flameLen * 0.6), 0);
    ctx.quadraticCurveTo(-12, 4, -10, 0);
    ctx.fillStyle = "rgba(255, 255, 100, 0.9)";
    ctx.fill();
  }

  ctx.fillStyle = "#e74c3c";
  ctx.beginPath();
  ctx.moveTo(-4, -6);
  ctx.bezierCurveTo(-15, -15, -20, -15, -12, -6);
  ctx.moveTo(-4, 6);
  ctx.bezierCurveTo(-15, 15, -20, 15, -12, 6);
  ctx.fill();

  const bodyGrad = ctx.createLinearGradient(0, -10, 0, 10);
  bodyGrad.addColorStop(0, "#ffffff");
  bodyGrad.addColorStop(0.5, "#dcdde1");
  bodyGrad.addColorStop(1, "#bdc3c7");

  ctx.beginPath();
  ctx.moveTo(20 * scale, 0);
  ctx.bezierCurveTo(15 * scale, -10 * scale, -10 * scale, -10 * scale, -12 * scale, 0);
  ctx.bezierCurveTo(-10 * scale, 10 * scale, 15 * scale, 10 * scale, 20 * scale, 0);
  ctx.fillStyle = bodyGrad;
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(20 * scale, 0);
  ctx.bezierCurveTo(18 * scale, -5 * scale, 12 * scale, -6 * scale, 10 * scale, -7 * scale);
  ctx.lineTo(10 * scale, 7 * scale);
  ctx.bezierCurveTo(12 * scale, 6 * scale, 18 * scale, 5 * scale, 20 * scale, 0);
  ctx.clip();
  ctx.fillStyle = "#e74c3c";
  ctx.fill();
  ctx.restore();

  ctx.beginPath();
  ctx.arc(2, 0, 3.5, 0, Math.PI * 2);
  ctx.fillStyle = "#3498db";
  ctx.fill();
  ctx.strokeStyle = "#2980b9";
  ctx.lineWidth = 1;
  ctx.stroke();

  ctx.restore();
}

function drawEarthDestination(canvas, ctx) {
  const dest = sim.state.destination;
  const ds = worldToScreen(canvas, dest.x, dest.y);

  const zoom = sim.state.camera.zoom;
  const rPx = dest.radius * zoom;

  // Only draw if it's somewhat near screen (saves a tiny bit)
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;
  if (ds.x < -rPx - 50 || ds.x > w + rPx + 50 || ds.y < -rPx - 50 || ds.y > h + rPx + 50) return;

  drawEarthAtScreen(ctx, ds.x, ds.y, rPx, 42, 0, false);


  // Optional label on the planet itself (like your screenshot)
  ctx.save();
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.font = "bold 16px system-ui";
  ctx.textAlign = "center";
  ctx.fillText("EARTH", ds.x, ds.y + 6);
  ctx.restore();
}

function drawDestinationAndArrow(canvas, ctx) {
  const dest = sim.state.destination;
  const rocket = sim.state.rocket;

  const ds = worldToScreen(canvas, dest.x, dest.y);
  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  const onScreen = (ds.x >= -60 && ds.x <= w + 60 && ds.y >= -60 && ds.y <= h + 60);

  // If destination is on-screen, don't draw arrow helper (prevents weird arrow on Earth)
  if (onScreen) return;

  // bring back these (you were using them later)
  const pulse = Math.sin(Date.now() / 200) * 1.5;
  const opacity = 0.5 + Math.sin(Date.now() / 200) * 0.1;

  const shipS = worldToScreen(canvas, rocket.x, rocket.y);
  const vx = ds.x - shipS.x;
  const vy = ds.y - shipS.y;

  const pad = 40;
  const minX = pad, maxX = w - pad, minY = pad, maxY = h - pad;

  let ax = ds.x, ay = ds.y;

  // Clamp arrow to screen edge
  const cx = w / 2, cy = h / 2;
  const rx = ds.x - cx, ry = ds.y - cy;
  const tCandidates = [];

  if (Math.abs(rx) > 1e-6) { tCandidates.push((minX - cx) / rx); tCandidates.push((maxX - cx) / rx); }
  if (Math.abs(ry) > 1e-6) { tCandidates.push((minY - cy) / ry); tCandidates.push((maxY - cy) / ry); }

  let best = null;
  for (const t of tCandidates) {
    if (t <= 0) continue;
    const x = cx + rx * t;
    const y = cy + ry * t;
    if (x >= minX - 2 && x <= maxX + 2 && y >= minY - 2 && y <= maxY + 2) {
      if (best === null || t < best.t) best = { t, x, y };
    }
  }
  if (best) { ax = best.x; ay = best.y; }

  const ang = Math.atan2(vy, vx);

  ctx.save();
  ctx.translate(ax, ay);
  ctx.rotate(ang);

  ctx.shadowBlur = 15;
  ctx.shadowColor = "rgba(95, 227, 255, 0.8)";

  ctx.beginPath();
  const arrowHeadSize = DEST_EDGE_ARROW_SIZE + pulse;
  ctx.moveTo(0, 0);
  ctx.lineTo(-arrowHeadSize, -arrowHeadSize / 1.5);
  ctx.lineTo(-arrowHeadSize * 0.7, 0);
  ctx.lineTo(-arrowHeadSize, arrowHeadSize / 1.5);
  ctx.closePath();

  ctx.fillStyle = `rgba(95, 227, 255, 0.9)`;
  ctx.fill();
  ctx.restore();

  // distance text
  if (sim.initialDistance == null) sim.initialDistance = remainingDistanceUnits();
  const dUnits = remainingDistanceUnits();
  const dAU = 10.0 * (dUnits / Math.max(1e-6, sim.initialDistance));

  ctx.fillStyle = `rgba(95, 227, 255, ${opacity})`;
  ctx.font = "bold 12px monospace";
  ctx.fillText(`${dAU.toFixed(2)} AU`, ax - 28, ay + 30);
}

function drawJoystickVector(canvas, ctx) {
  if (len(sim.joyVec.x, sim.joyVec.y) < 0.05) return;
  const r = sim.state.rocket;
  const ship = worldToScreen(canvas, r.x, r.y);

  const arrowPx = 110 * Math.min(1, len(sim.joyVec.x, sim.joyVec.y));
  const vx = -sim.joyVec.x;
  const vy = -sim.joyVec.y;

  const end = { x: ship.x + vx * arrowPx, y: ship.y + vy * arrowPx };

  ctx.beginPath();
  ctx.moveTo(ship.x, ship.y);
  ctx.lineTo(end.x, end.y);
  ctx.strokeStyle = "rgba(255,255,255,0.8)";
  ctx.lineWidth = 2;
  ctx.stroke();

  const a = Math.atan2(end.y - ship.y, end.x - ship.x);
  const head = 10;
  ctx.beginPath();
  ctx.moveTo(end.x, end.y);
  ctx.lineTo(end.x - head * Math.cos(a - 0.5), end.y - head * Math.sin(a - 0.5));
  ctx.lineTo(end.x - head * Math.cos(a + 0.5), end.y - head * Math.sin(a + 0.5));
  ctx.closePath();
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  ctx.fill();
}


// version 0: when it only had the initial brist count 
// function drawEmergencyBurnCounter(canvas, ctx) {
//   if (!sim.state) return;

//   const currentBurns = sim.state.space_burns_left ?? 3;
//   const canSpaceBurn = sim.state.can_space_burn ?? true;
//   const isLatched = sim.state.latched_planet_id !== null;

//   ctx.save();
//   // Ensure we are drawing in screen space
//   ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);

//   const w = canvas.getBoundingClientRect().width;
//   const h = canvas.getBoundingClientRect().height;

//   // --- POSITION ADJUSTMENT ---
//   const x = 20; 
//   const y = h - 80; // This moves it to the bottom-left corner

//   // 1. Draw Background Box
//   ctx.fillStyle = "rgba(13, 15, 20, 0.8)";
//   ctx.beginPath();
//   ctx.roundRect(x, y, 140, 60, 8);
//   ctx.fill();
//   ctx.strokeStyle = "rgba(255, 255, 255, 0.1)";
//   ctx.stroke();

//   // 2. Draw Label
//   ctx.fillStyle = "#9aa6b2"; 
//   ctx.font = "bold 10px monospace";
//   ctx.fillText("EMERGENCY THRUST", x + 10, y + 20);

//   // 3. Draw Number & Status
//   let statusColor = "#5fe3ff"; 
//   let statusText = "READY";

//   if (isLatched) {
//     statusColor = "#6dff57"; 
//     statusText = "ORBITAL: UNLIMITED";
//   } else if (!canSpaceBurn) {
//     statusColor = "#ff4d4d"; 
//     statusText = "COOLDOWN";
//   }

//   ctx.fillStyle = statusColor;
//   ctx.font = "bold 28px monospace";
//   ctx.fillText(currentBurns, x + 10, y + 45);

//   ctx.font = "bold 9px monospace";
//   ctx.fillText(statusText, x + 40, y + 45);

//   ctx.restore();
// }




// function drawEmergencyBurnCounter(canvas, ctx) {
//   if (!sim.state) return;

//   const currentBurns = sim.state.space_burns_left ?? 10;
//   const burstCount = sim.state.consecutive_burns ?? 0;
//   const canSpaceBurn = sim.state.can_space_burn ?? true;
//   const isLatched = sim.state.latched_planet_id !== null;

//   ctx.save();
//   ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);

//   const w = canvas.getBoundingClientRect().width;
//   const h = canvas.getBoundingClientRect().height;


//   // --- POSITION ADJUSTMENT ---
//   const x = 20;
//   const y = h - 80; // This moves it to the bottom-left corner


//   // 1. Draw Background Box
//   ctx.fillStyle = "rgba(13, 15, 20, 0.85)";
//   ctx.beginPath();
//   ctx.roundRect(x, y, 160, 60, 8); // Widened slightly for the extra text
//   ctx.fill();
  
//   // Visual alert: Red border if the burst limit is hit
//   ctx.strokeStyle = canSpaceBurn ? "rgba(255, 255, 255, 0.1)" : "#ff4d4d";
//   ctx.lineWidth = 2;
//   ctx.stroke();

//   // 2. Draw Label
//   ctx.fillStyle = "#9aa6b2"; 
//   ctx.font = "bold 9px monospace";
//   ctx.fillText("TOTAL CHARGES", x + 12, y + 18);

//   // 3. Draw Main Number (Total Pool)
//   let statusColor = canSpaceBurn ? "#5fe3ff" : "#ff4d4d";
//   if (isLatched) statusColor = "#6dff57";

//   if (isLatched) {
//     statusColor = "#6dff57";
//     statusText = "ORBITAL: UNLIMITED";
//   } else if (!canSpaceBurn) {
//     statusColor = "#ff4d4d";
//     statusText = "COOLDOWN";
//   }

//   // let statusColor = "#5fe3ff";
//   let statusText = "READY";

//   ctx.fillStyle = statusColor;
//   ctx.font = "bold 28px monospace";
//   ctx.fillText(`${currentBurns}`, x + 12, y + 48);




//   // 4. Draw Sub-status (Burst Tracker)
//   let burstStatus = `BURST: ${burstCount}/3`;
//   if (isLatched) {
//     burstStatus = "ORBITAL: UNLIMITED";
//   } else if (!canSpaceBurn) {
//     burstStatus = "LIMIT HIT: LATCH TO RESET";
//   }

//   ctx.fillStyle = statusColor;
//   ctx.font = "bold 10px monospace";
//   ctx.fillText(burstStatus, x + 50, y + 45);

//   ctx.restore();
// }


function drawEmergencyBurnCounter(canvas, ctx) {
  if (!sim.state) return;

  // Pull the new data you just added to serialize.py
  const currentBurns = sim.state.space_burns_left ?? 10;
  const burstCount = sim.state.consecutive_burns ?? 0;
  const canSpaceBurn = sim.state.can_space_burn ?? true;
  const isLatched = sim.state.latched_planet_id !== null;

  ctx.save();
  ctx.setTransform(window.devicePixelRatio || 1, 0, 0, window.devicePixelRatio || 1, 0, 0);

  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  const x = 20;
  const y = h - 80;

  // 1. Draw Background Box
  ctx.fillStyle = "rgba(13, 15, 20, 0.85)";
  ctx.beginPath();
  ctx.roundRect(x, y, 170, 60, 8); // Slightly wider for long status text
  ctx.fill();
  
  // Alert Border: Red if burst limit is hit
  ctx.strokeStyle = canSpaceBurn ? "rgba(255, 255, 255, 0.1)" : "#ff4d4d";
  ctx.lineWidth = 2;
  ctx.stroke();


  // 2. Determine Status Colors/Text
  // Inside drawEmergencyBurnCounter in render.js
  // 2. Determine Status Colors/Text - DECLARE WITH 'LET'
  let statusColor = "#5fe3ff"; 
  let burstText = `BURST: ${burstCount}/3`;

  if (isLatched) {
      statusColor = "#6dff57"; // Green
      burstText = "ORBITAL: UNLIMITED";
  } else if (!canSpaceBurn) {
      statusColor = "#ff4d4d"; // Red
      burstText = "LIMIT HIT: LATCH TO RESET";
  } else {
      statusColor = "#5fe3ff"; // Cyan
      burstText = `BURST: ${burstCount}/3`;
  }



  // 3. Draw Labels
  ctx.fillStyle = "#9aa6b2"; 
  ctx.font = "bold 9px monospace";
  ctx.fillText("TOTAL CHARGES", x + 12, y + 18);

  // 4. Draw Main Number (Total Pool)
  ctx.fillStyle = statusColor;
  ctx.font = "bold 28px monospace";
  ctx.fillText(`${currentBurns}`, x + 12, y + 48);

  // 5. Draw Sub-status (Burst Tracker)
  ctx.font = "bold 9px monospace";
  ctx.fillText(burstText, x + 55, y + 45);

  ctx.restore();
}



export function renderFrame(canvas, ctx) {
  if (!sim.state) return;

  const w = canvas.getBoundingClientRect().width;
  const h = canvas.getBoundingClientRect().height;

  ctx.clearRect(0, 0, w, h);
  drawStars(canvas, ctx);
  drawTrail(canvas, ctx);
  drawPlanets(canvas, ctx);

  // Draw Earth destination BEFORE the arrow helper
  drawEarthDestination(canvas, ctx);

  drawDestinationAndArrow(canvas, ctx);
  drawShip(canvas, ctx);
  drawJoystickVector(canvas, ctx);

  drawGlobalWarning(canvas, ctx); // this is the gobal timer (for orange planets)

  drawEmergencyBurnCounter(canvas, ctx);
}