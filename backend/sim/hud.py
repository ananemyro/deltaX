import math
from typing import Any, Dict, List

from sim.state import STATE
from sim.mathutil import norm, unit, dist
from sim.config import clamp
from sim.models import Rocket, Destination, Planet


# The "Data Scientist." It calculates high-level stats for the UI, most importantly the Success Probability, which uses a sigmoid function to guess if the player is currently on a winning trajectory.
# HERE WE ARE TRANSLATING THOSE NUMBERS INTO SOMETHING THE USER WILL UNDERSTAND
def compute_success_probability() -> float:
    """
    Heuristic "probability of success" that reacts to alignment, distance,
    and revealed bad-planet risk. Returns [0,1].
    """
    status = STATE["status"]
    if status == "failed":
        return 0.0
    if status == "success":
        return 1.0
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
