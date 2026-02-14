import math
from typing import Tuple, List

from sim.state import STATE
from sim.models import Rocket, Planet, Destination, Camera
from sim.config import (
    G, SOFTENING_R2, REVEAL_MARGIN,
    CRASH_RADIUS_FACTOR, DEATH_RADIUS_FACTOR,
    MAX_WORLD_ABS, CAM_ALPHA, LOOKAHEAD
)
from sim.mathutil import dist

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

    # Current speed
    vx, vy = rocket.vx, rocket.vy
    speed = math.hypot(vx, vy)

    # --- LOOKAHEAD: cap how far ahead we look in WORLD units ---
    # Max lookahead distance in world coords (tune 120..400)
    MAX_AHEAD = 220.0

    if speed > 1e-6:
        ux, uy = vx / speed, vy / speed
    else:
        ux, uy = 0.0, 0.0

    # Map speed to ahead distance, but cap it hard
    # (tune the 6.0 to change how quickly it reaches MAX_AHEAD)
    ahead = min(MAX_AHEAD, 6.0 * speed)

    target_x = rocket.x + ux * ahead
    target_y = rocket.y + uy * ahead

    # --- SMOOTHING: keep it stable ---
    # With DV_MAX=60 you generally want strong follow
    alpha = CAM_ALPHA  # keep your config value
    cam.cx += (target_x - cam.cx) * alpha
    cam.cy += (target_y - cam.cy) * alpha

    # --- SAFETY SNAP: if rocket would be off-screen, snap to rocket ---
    # This uses a world-distance threshold (tune 350..800 depending on zoom/scale)
    SNAP_DIST = 500.0
    dx = rocket.x - cam.cx
    dy = rocket.y - cam.cy
    if (dx * dx + dy * dy) > (SNAP_DIST * SNAP_DIST):
        cam.cx = rocket.x
        cam.cy = rocket.y
