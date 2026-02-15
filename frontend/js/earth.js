function clamp01(x){ return Math.max(0, Math.min(1, x)); }
function lerp(a,b,t){ return a + (b-a)*t; }

function hash2(x, y, seed) {
  const s = Math.sin(x * 127.1 + y * 311.7 + seed * 91.3) * 43758.5453123;
  return s - Math.floor(s);
}

function noise2(x, y, seed) {
  const x0 = Math.floor(x), y0 = Math.floor(y);
  const x1 = x0 + 1, y1 = y0 + 1;

  const sx = x - x0;
  const sy = y - y0;

  const n00 = hash2(x0, y0, seed);
  const n10 = hash2(x1, y0, seed);
  const n01 = hash2(x0, y1, seed);
  const n11 = hash2(x1, y1, seed);

  const u = sx * sx * (3 - 2 * sx);
  const v = sy * sy * (3 - 2 * sy);

  const ix0 = lerp(n00, n10, u);
  const ix1 = lerp(n01, n11, u);
  return lerp(ix0, ix1, v);
}

function fbm(x, y, seed) {
  let f = 0;
  let amp = 0.55;
  let freq = 1.0;
  for (let i = 0; i < 5; i++) {
    f += amp * noise2(x * freq, y * freq, seed + i * 19.7);
    freq *= 2.0;
    amp *= 0.55;
  }
  return f;
}

// Cache: seed -> offscreen canvas (fixed size)
const _cache = new Map();
const TEX = 512; // fixed quality/perf knob (384/512/768)

function buildEarthTexture(seed) {
  const off = document.createElement("canvas");
  off.width = TEX;
  off.height = TEX;

  const ctx = off.getContext("2d");
  const img = ctx.createImageData(TEX, TEX);
  const data = img.data;

  for (let j = 0; j < TEX; j++) {
    for (let i = 0; i < TEX; i++) {
      const u = (i / (TEX - 1)) * 2 - 1;   // -1..1
      const v = (j / (TEX - 1)) * 2 - 1;   // -1..1
      const rr = u*u + v*v;

      const idx = (j * TEX + i) * 4;
      if (rr > 1) { data[idx+3] = 0; continue; }

      const z = Math.sqrt(1 - rr);

      // Static pseudo lon/lat (no rotation)
      let lon = Math.atan2(v, u) / (Math.PI * 2);
      lon = (lon + 1) % 1;

      const lat = clamp01(1 - Math.sqrt(rr));

      // Center-facing north pole ice
      const center = clamp01((0.55 - rr) / 0.55);
      const iceNoise = fbm(lon * 12.0, lat * 12.0, seed + 202);
      const ice = clamp01(Math.pow(center, 1.6) * (0.55 + 0.55 * iceNoise));

      // Ocean (deep -> bright blue)
      const oceanNoise = fbm(lon * 6.0, lat * 6.0, seed + 10);
      const oceanDeep = { r: 5,  g: 20,  b: 55 };
      const oceanMid  = { r: 40, g: 140, b: 220 };
      const ot = clamp01(0.25 + oceanNoise * 0.55);

      let R = lerp(oceanDeep.r, oceanMid.r, ot);
      let G = lerp(oceanDeep.g, oceanMid.g, ot);
      let B = lerp(oceanDeep.b, oceanMid.b, ot);

      // Land mask (keep ocean-heavy)
      const n = fbm(lon * 4.2, lat * 3.6, seed);
      const landMask = n - 0.70;

      if (landMask > 0) {
        const coast = { r: 230, g: 215, b: 165 };
        const grass = { r: 80,  g: 170, b: 110 };
        const forest= { r: 20,  g: 90,  b: 60 };

        const h = clamp01(landMask * 2.0);
        const elev = fbm(lon * 12.0, lat * 12.0, seed + 77);
        const t = clamp01(0.20 + h * 0.65 + elev * 0.25);

        let lr, lg, lb;
        if (t < 0.35) {
          const tt = t / 0.35;
          lr = lerp(coast.r, grass.r, tt);
          lg = lerp(coast.g, grass.g, tt);
          lb = lerp(coast.b, grass.b, tt);
        } else {
          const tt = (t - 0.35) / 0.65;
          lr = lerp(grass.r, forest.r, tt);
          lg = lerp(grass.g, forest.g, tt);
          lb = lerp(grass.b, forest.b, tt);
        }

        const shore = clamp01(landMask * 10.0);
        R = lerp(R, lr, shore);
        G = lerp(G, lg, shore);
        B = lerp(B, lb, shore);
      }

      // Clouds (static)
      const c1 = fbm(lon * 6.0 + 0.15, lat * 8.0 + 0.05, seed + 999);
      const c2 = fbm(lon * 14.0,      lat * 14.0,        seed + 1337);
      let cloud = clamp01((c1 - 0.58) * 3.0);
      cloud *= (0.55 + 0.45 * c2);
      const cloudAlpha = cloud * 0.50;

      R = lerp(R, 245, cloudAlpha);
      G = lerp(G, 250, cloudAlpha);
      B = lerp(B, 255, cloudAlpha);

      // Ice overlay
      R = lerp(R, 235, ice);
      G = lerp(G, 245, ice);
      B = lerp(B, 255, ice);

      // Lighting
      const lx = -0.55, ly = -0.35, lz = 0.75;
      const ndotl = clamp01(u*lx + v*ly + z*lz);
      const light = 0.28 + ndotl * 0.82;
      const terminator = clamp01((ndotl - 0.15) / 0.85);
      const night = lerp(0.38, 1.0, terminator);

      R = R * light * night;
      G = G * light * night;
      B = B * light * night;

      data[idx+0] = R|0;
      data[idx+1] = G|0;
      data[idx+2] = B|0;
      data[idx+3] = 255;
    }
  }

  ctx.putImageData(img, 0, 0);
  return off;
}

/**
 * Draw Earth at screen coords (x,y) with radius in pixels.
 * This is FAST: uses cached fixed-size texture.
 */
export function drawEarthAtScreen(ctx, x, y, radiusPx, seed = 42) {
  let tex = _cache.get(seed);
  if (!tex) {
    tex = buildEarthTexture(seed);
    _cache.set(seed, tex);
  }

  const r = radiusPx;

  ctx.save();
  ctx.translate(x, y);

  // Atmosphere glow
  ctx.beginPath();
  ctx.arc(0, 0, r + 9, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(120,220,255,0.14)";
  ctx.lineWidth = 10;
  ctx.stroke();

  // Clip sphere
  ctx.save();
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.clip();

  // Scale cached texture
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(tex, -r, -r, r * 2, r * 2);

  // Shine
  const shine = ctx.createRadialGradient(-r*0.35, -r*0.35, r*0.10, -r*0.20, -r*0.20, r*0.95);
  shine.addColorStop(0.0, "rgba(255,255,255,0.22)");
  shine.addColorStop(0.35, "rgba(255,255,255,0.08)");
  shine.addColorStop(1.0, "rgba(255,255,255,0.0)");
  ctx.fillStyle = shine;
  ctx.fillRect(-r, -r, r*2, r*2);

  ctx.restore(); // clip restore

  // Outline + rim
  ctx.beginPath();
  ctx.arc(0, 0, r + 0.5, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(255,255,255,0.18)";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(0, 0, r + 3, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(120,220,255,0.22)";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.restore();
}
