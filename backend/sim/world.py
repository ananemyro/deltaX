import random
from typing import List, Optional, Tuple

from sim.state import STATE
from sim.models import Rocket, Planet, Destination, Camera
from sim.config import (
    GOOD_COUNT, BAD_COUNT,
    GOOD_MU_RANGE, BAD_MU_RANGE,
    PLANET_RADIUS_RANGE, ZOOM_DEFAULT
)

def generate_good_positions(seed: int, dest_x: float) -> List[Tuple[float, float]]:
    rng = random.Random(seed)
    pts = []
    for i in range(GOOD_COUNT):
        t = (i + 1) / (GOOD_COUNT + 1)     # evenly spaced fraction
        x = t * dest_x + rng.uniform(-5_000_000, 5_000_000)
        y = rng.uniform(-10_000_000, 10_000_000)
        pts.append((x, y))
    return pts


def generate_bad_positions(
    seed: int,
    start: Tuple[float, float],
    dest: Tuple[float, float]
) -> List[Tuple[float, float]]:
    rng = random.Random(seed + 1337)
    pts: List[Tuple[float, float]] = []

    sx, sy = start
    dx, dy = dest
    corridor_len = dx - sx

    # --- km-scale spreads (tune these) ---
    X_JITTER = 3_000_000.0      # ±3 million km along x
    Y_SPREAD = 50_000_000.0     # ±50 million km off-corridor

    for _ in range(BAD_COUNT):
        # Place somewhere along the corridor
        t = rng.uniform(0.10, 0.95)

        # Base point along the line from start to dest
        x = sx + t * corridor_len + rng.uniform(-X_JITTER, X_JITTER)

        # Off-corridor: mostly hazards above/below the route
        # (bias away from y≈0 so they actually matter)
        y = rng.uniform(-Y_SPREAD, Y_SPREAD)
        if abs(y) < 10_000_000.0:  # avoid near-corridor band ±10 million km
            y = 10_000_000.0 * (1 if rng.random() < 0.5 else -1) + rng.uniform(-5_000_000.0, 5_000_000.0)

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
    AU = 149_597_870.7

    V0 = 30.0  # km/s
    rocket = Rocket(x=0.0, y=0.0, vx=V0, vy=0.0)
    dest = Destination(
        x=10 * AU,
        y=0.0,
        radius=500_000.0
    )

    # Generate planets
    goods = generate_good_positions(seed, min(dest.x, 300_000_000.0))
    bads = generate_bad_positions(seed, (rocket.x, rocket.y), (dest.x, dest.y))

    planets: List[Planet] = []
    pid = 1

    rmin, rmax = PLANET_RADIUS_RANGE

    for (x, y) in goods:
        u = rng.random()
        radius = rmin * (rmax / rmin) ** u
        has_rings = (rng.random() < 0.65)
        planets.append(
            Planet(
                id=pid,
                x=x, y=y,
                mu=rng.uniform(*GOOD_MU_RANGE),
                radius=radius,
                kind="good",
                revealed=False,
                recoverable=True,
                has_rings=has_rings,
            )
        )
        pid += 1

    for (x, y) in bads:
        u = rng.random()
        radius = rmin * (rmax / rmin) ** u
        has_rings = (rng.random() < 0.65)
        # Some bad planets are "too strong" => unrecoverable
        unrecoverable = (rng.random() < 0.35)

        planets.append(
            Planet(
                id=pid,
                x=x, y=y,
                mu=rng.uniform(*BAD_MU_RANGE) * (1.35 if unrecoverable else 1.0),
                radius=radius * (1.15 if unrecoverable else 1.0),
                kind="bad",
                revealed=False,
                recoverable=not unrecoverable,
                has_rings=has_rings,
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