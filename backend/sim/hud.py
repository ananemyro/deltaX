import math
from typing import Any, Dict, List

from sim.state import STATE
from sim.mathutil import norm, unit, dist
from sim.config import clamp
from sim.models import Rocket, Destination, Planet


def compute_success_score() -> float:
    rocket = STATE["rocket"]
    dest = STATE["dest"]
    planets = STATE["planets"]

    to_dx, to_dy = dest.x - rocket.x, dest.y - rocket.y
    d = norm(to_dx, to_dy)
    ux, uy = unit(to_dx, to_dy)

    v = norm(rocket.vx, rocket.vy)  # km/s
    wx, wy = unit(rocket.vx, rocket.vy)
    alignment = ux * wx + uy * wy  # [-1,1]

    # Risk term based on gravitational acceleration magnitude ~ mu/r^2
    risk = 0.0
    for p in planets:
        if p.revealed and p.kind == "bad":
            r = max(1_000.0, dist((rocket.x, rocket.y), (p.x, p.y)))  # km
            risk += (p.mu / (r * r)) * (1.25 if not p.recoverable else 1.0)

    # Normalize scales so numbers stay ~O(1)
    # 1 AU ~ 150 million km
    d0 = 10 * 149_597_870.7
    dist_term = d / d0

    # Typical heliocentric speeds are ~25–40 km/s
    v_term = v / 30.0

    score = (1.5 * alignment) - (1.2 * dist_term) - (0.00002 * risk) + (0.2 * v_term)
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
        "success_score": compute_success_score(),
        "status": STATE["status"],
        "fail_reason": STATE["fail_reason"],
    }