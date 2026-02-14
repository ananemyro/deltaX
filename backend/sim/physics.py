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

    # Look-ahead in direction of movement
    target_x = rocket.x + rocket.vx * LOOKAHEAD
    target_y = rocket.y + rocket.vy * LOOKAHEAD

    cam.cx += (target_x - cam.cx) * CAM_ALPHA
    cam.cy += (target_y - cam.cy) * CAM_ALPHA
