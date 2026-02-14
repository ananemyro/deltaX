import random
from typing import List, Optional, Tuple

from sim.state import STATE
from sim.models import Rocket, Planet, Destination, Camera
from sim.config import (
    GOOD_COUNT, BAD_COUNT,
    GOOD_MASS_RANGE, BAD_MASS_RANGE,
    PLANET_RADIUS_RANGE, ZOOM_DEFAULT
)

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