from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# -------------------------
# Tunables (game feel)
# -------------------------
G = 1.0
SOFTENING_R2 = 25.0        # prevents singularities
DT_MIN, DT_MAX = 0.001, 0.05
MAX_WORLD_ABS = 4000.0     # out-of-bounds fail
REVEAL_MARGIN = 10.0

# Controls / planning
DV_MAX = 3.0               # max speed change per "burn"
PLAN_COOLDOWN_S = 0.25     # optional: prevent spam burns

# Camera
CAM_ALPHA = 0.10
LOOKAHEAD = 25.0
ZOOM_DEFAULT = 1.0

# Planets
GOOD_COUNT = 10
BAD_COUNT = 12
GOOD_MASS_RANGE = (900.0, 1800.0)
BAD_MASS_RANGE = (1600.0, 4200.0)
PLANET_RADIUS_RANGE = (14.0, 26.0)

# Failure
DEATH_RADIUS_FACTOR = 0.65  # if bad & unrecoverable: fail when dist < factor*radius
CRASH_RADIUS_FACTOR = 1.0   # for any planet: crash when dist < radius*factor


# -------------------------
# Data model
# -------------------------
@dataclass
class Rocket:
    x: float
    y: float
    vx: float
    vy: float

@dataclass
class Planet:
    id: int
    x: float
    y: float
    mass: float
    radius: float
    kind: str              # "good" | "bad"
    revealed: bool
    recoverable: bool      # only meaningful for bad planets

@dataclass
class Destination:
    x: float
    y: float
    radius: float

@dataclass
class Camera:
    cx: float
    cy: float
    zoom: float


STATE: Dict[str, Any] = {
    "t": 0.0,
    "rocket": Rocket(x=0.0, y=0.0, vx=3.0, vy=0.6),
    "planets": [],  # List[Planet]
    "dest": Destination(x=2600.0, y=0.0, radius=40.0),
    "camera": Camera(cx=0.0, cy=0.0, zoom=ZOOM_DEFAULT),
    "status": "running",  # running | success | failed
    "fail_reason": None,
    "last_plan_time": -1e9,
}


# -------------------------
# Utility math
# -------------------------
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def norm(x: float, y: float) -> float:
    return math.sqrt(x * x + y * y)

def unit(x: float, y: float) -> Tuple[float, float]:
    n = norm(x, y)
    if n < 1e-9:
        return (0.0, 0.0)
    return (x / n, y / n)

def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return norm(a[0] - b[0], a[1] - b[1])


# -------------------------
# World generation
# -------------------------
def generate_good_positions(seed: int) -> List[Tuple[float, float]]:
    """
    Hand-curated-ish "corridor" of planets toward the destination,
    but with randomness so runs differ.
    """
    rng = random.Random(seed)
    pts: List[Tuple[float, float]] = []
    x = 300.0
    y = 0.0
    for _ in range(GOOD_COUNT):
        x += rng.uniform(180.0, 320.0)
        y = rng.uniform(-240.0, 240.0)
        pts.append((x, y))
    return pts

def generate_bad_positions(seed: int, start: Tuple[float, float], dest: Tuple[float, float]) -> List[Tuple[float, float]]:
    rng = random.Random(seed + 1337)
    pts: List[Tuple[float, float]] = []

    sx, sy = start
    dx, dy = dest
    corridor_len = dx - sx

    for _ in range(BAD_COUNT):
        # Place somewhere along the corridor with wider y spread
        t = rng.uniform(0.10, 0.95)
        x = sx + t * corridor_len + rng.uniform(-80.0, 80.0)
        y = rng.uniform(-600.0, 600.0)
        pts.append((x, y))
    return pts

def reset_world(seed: Optional[int] = None) -> None:
    seed = int(seed) if seed is not None else random.randint(1, 10_000_000)
    rng = random.Random(seed)

    # Rocket start and destination
    STATE["t"] = 0.0
    STATE["status"] = "running"
    STATE["fail_reason"] = None
    STATE["last_plan_time"] = -1e9

    rocket = Rocket(
        x=0.0,
        y=0.0,
        vx=rng.uniform(2.7, 3.6),   # "reasonable initial speed"
        vy=rng.uniform(-0.8, 0.8),
    )
    dest = Destination(
        x=rng.uniform(2400.0, 2900.0),
        y=rng.uniform(-120.0, 120.0),
        radius=40.0,
    )

    # Generate planets
    goods = generate_good_positions(seed)
    bads = generate_bad_positions(seed, (rocket.x, rocket.y), (dest.x, dest.y))

    planets: List[Planet] = []
    pid = 1

    for (x, y) in goods:
        planets.append(
            Planet(
                id=pid,
                x=x, y=y,
                mass=rng.uniform(*GOOD_MASS_RANGE),
                radius=rng.uniform(*PLANET_RADIUS_RANGE),
                kind="good",
                revealed=False,
                recoverable=True,
            )
        )
        pid += 1

    for (x, y) in bads:
        # Some bad planets are "too strong" => unrecoverable
        unrecoverable = (rng.random() < 0.35)
        planets.append(
            Planet(
                id=pid,
                x=x, y=y,
                mass=rng.uniform(*BAD_MASS_RANGE) * (1.35 if unrecoverable else 1.0),
                radius=rng.uniform(*PLANET_RADIUS_RANGE) * (1.15 if unrecoverable else 1.0),
                kind="bad",
                revealed=False,
                recoverable=not unrecoverable,
            )
        )
        pid += 1

    # Shuffle positions slightly so good/bad aren't visually patterned
    rng.shuffle(planets)

    STATE["rocket"] = rocket
    STATE["dest"] = dest
    STATE["planets"] = planets
    STATE["camera"] = Camera(cx=rocket.x, cy=rocket.y, zoom=ZOOM_DEFAULT)
    STATE["seed"] = seed


# -------------------------
# Physics + game rules
# -------------------------
def accel_from_planets(rocket: Rocket, planets: List[Planet]) -> Tuple[float, float]:
    ax, ay = 0.0, 0.0
    for p in planets:
        dx = p.x - rocket.x
        dy = p.y - rocket.y
        r2 = dx * dx + dy * dy
        r2 = max(r2, SOFTENING_R2)
        r = math.sqrt(r2)
        a = G * p.mass / r2
        ax += a * dx / r
        ay += a * dy / r
    return ax, ay

def update_reveals_and_collisions() -> None:
    rocket: Rocket = STATE["rocket"]
    planets: List[Planet] = STATE["planets"]

    rx, ry = rocket.x, rocket.y

    for p in planets:
        d = dist((rx, ry), (p.x, p.y))

        # Reveal on approach
        if not p.revealed and d <= (p.radius + REVEAL_MARGIN):
            p.revealed = True

        # Crash into any planet (simple rule)
        if d <= (p.radius * CRASH_RADIUS_FACTOR):
            STATE["status"] = "failed"
            STATE["fail_reason"] = f"crashed_into_planet_{p.id}"
            return

        # Unrecoverable bad planet death-zone
        if p.kind == "bad" and (not p.recoverable):
            if d <= (p.radius * DEATH_RADIUS_FACTOR):
                STATE["status"] = "failed"
                STATE["fail_reason"] = f"overwhelmed_by_gravity_{p.id}"
                return

def check_success_and_bounds() -> None:
    rocket: Rocket = STATE["rocket"]
    dest: Destination = STATE["dest"]

    # Destination
    if dist((rocket.x, rocket.y), (dest.x, dest.y)) <= dest.radius:
        STATE["status"] = "success"
        STATE["fail_reason"] = None
        return

    # Bounds
    if abs(rocket.x) > MAX_WORLD_ABS or abs(rocket.y) > MAX_WORLD_ABS:
        STATE["status"] = "failed"
        STATE["fail_reason"] = "out_of_bounds"
        return

def step_sim(dt: float) -> None:
    if STATE["status"] != "running":
        return

    rocket: Rocket = STATE["rocket"]
    planets: List[Planet] = STATE["planets"]

    ax, ay = accel_from_planets(rocket, planets)

    # Semi-implicit Euler (good stability for games)
    rocket.vx += ax * dt
    rocket.vy += ay * dt
    rocket.x += rocket.vx * dt
    rocket.y += rocket.vy * dt

    STATE["t"] += dt

    update_reveals_and_collisions()
    if STATE["status"] == "running":
        check_success_and_bounds()

    update_camera()

def update_camera() -> None:
    rocket: Rocket = STATE["rocket"]
    cam: Camera = STATE["camera"]

    # Look-ahead in direction of movement
    target_x = rocket.x + rocket.vx * LOOKAHEAD
    target_y = rocket.y + rocket.vy * LOOKAHEAD

    cam.cx += (target_x - cam.cx) * CAM_ALPHA
    cam.cy += (target_y - cam.cy) * CAM_ALPHA


# -------------------------
# HUD metrics
# -------------------------
def compute_success_probability() -> float:
    """
    Heuristic "probability of success" that reacts to alignment, distance,
    and revealed bad-planet risk. Returns [0,1].
    """
    rocket: Rocket = STATE["rocket"]
    dest: Destination = STATE["dest"]
    planets: List[Planet] = STATE["planets"]

    # Distance & alignment
    to_dx, to_dy = (dest.x - rocket.x), (dest.y - rocket.y)
    d = norm(to_dx, to_dy)
    ux, uy = unit(to_dx, to_dy)

    v = norm(rocket.vx, rocket.vy)
    wx, wy = unit(rocket.vx, rocket.vy)
    alignment = ux * wx + uy * wy  # [-1,1]

    # Risk from revealed bad planets (closer + heavier => worse)
    risk = 0.0
    for p in planets:
        if p.revealed and p.kind == "bad":
            r = max(30.0, dist((rocket.x, rocket.y), (p.x, p.y)))
            risk += (p.mass / (r * r)) * (1.25 if not p.recoverable else 1.0)
    risk = min(risk, 2.5)

    # Normalize distance
    d0 = 2600.0
    dist_term = d / d0

    # Score -> sigmoid
    score = (1.5 * alignment) - (1.2 * dist_term) - (1.1 * risk) + (0.2 * (v / 4.0))
    p = 1.0 / (1.0 + math.exp(-score))
    return float(clamp(p, 0.0, 1.0))

def hud() -> Dict[str, Any]:
    rocket: Rocket = STATE["rocket"]
    dest: Destination = STATE["dest"]

    d = dist((rocket.x, rocket.y), (dest.x, dest.y))
    v = norm(rocket.vx, rocket.vy)

    return {
        "distance_to_destination": d,
        "speed": v,
        "success_probability": compute_success_probability(),
        "status": STATE["status"],
        "fail_reason": STATE["fail_reason"],
    }


# -------------------------
# Serialization for UI
# -------------------------
def serialize_planet(p: Planet) -> Dict[str, Any]:
    # UI wants: white by default; green/red once revealed
    if not p.revealed:
        color = "white"
        status = "unknown"
    else:
        if p.kind == "good":
            color = "green"
            status = "good"
        else:
            color = "red"
            status = "bad"

    return {
        "id": p.id,
        "x": p.x, "y": p.y,
        "mass": p.mass,
        "radius": p.radius,
        "revealed": p.revealed,
        "recoverable": p.recoverable,
        "status": status,
        "color": color,
    }

def state_payload() -> Dict[str, Any]:
    rocket: Rocket = STATE["rocket"]
    dest: Destination = STATE["dest"]
    cam: Camera = STATE["camera"]
    planets: List[Planet] = STATE["planets"]

    return {
        "t": STATE["t"],
        "seed": STATE.get("seed"),
        "rocket": asdict(rocket),
        "destination": asdict(dest),
        "camera": asdict(cam),
        "planets": [serialize_planet(p) for p in planets],
        "hud": hud(),
    }


# -------------------------
# API
# -------------------------
@app.get("/api/state")
def api_state():
    return jsonify(state_payload())

@app.post("/api/reset")
def api_reset():
    data = request.get_json(silent=True) or {}
    seed = data.get("seed")
    reset_world(seed=seed)
    return jsonify(state_payload())

@app.post("/api/plan")
def api_plan():
    """
    Apply a "burn" based on UI drag vector.

    Expected JSON (choose one):
      - world vector: { "dvx": ..., "dvy": ... }
      - screen vector: { "dx": ..., "dy": ..., "pixels_to_world": ... }
        where dx,dy are screen drag (end-start), and pixels_to_world scales to world units.
    """
    if STATE["status"] != "running":
        return jsonify(state_payload())

    data = request.get_json(silent=True) or {}
    t = float(STATE["t"])

    # Optional cooldown to avoid spamming
    if (t - float(STATE["last_plan_time"])) < PLAN_COOLDOWN_S:
        return jsonify(state_payload())

    rocket: Rocket = STATE["rocket"]

    if "dvx" in data and "dvy" in data:
        dvx = float(data["dvx"])
        dvy = float(data["dvy"])
    else:
        dx = float(data.get("dx", 0.0))
        dy = float(data.get("dy", 0.0))
        pixels_to_world = float(data.get("pixels_to_world", 1.0))
        # Typical UI drag: right is +x, down is +y in screen space;
        # In most canvases, world y increases upward, so invert dy if needed in UI.
        dvx = dx * pixels_to_world
        dvy = dy * pixels_to_world

    # Clamp magnitude
    mag = norm(dvx, dvy)
    if mag > DV_MAX:
        ux, uy = unit(dvx, dvy)
        dvx, dvy = ux * DV_MAX, uy * DV_MAX

    rocket.vx += dvx
    rocket.vy += dvy
    STATE["last_plan_time"] = t

    return jsonify(state_payload())

@app.post("/api/step")
def api_step():
    data = request.get_json(silent=True) or {}
    dt = float(data.get("dt", 0.016))
    dt = clamp(dt, DT_MIN, DT_MAX)
    step_sim(dt)
    return jsonify(state_payload())


# -------------------------
# Init
# -------------------------
reset_world()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
