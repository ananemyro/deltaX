import random
from typing import List, Optional, Tuple

from sim.state import STATE
from sim.models import Rocket, Planet, Destination, Camera
from sim.mathutil import dist
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

# helper function, such that no two planets can be created on top of each other 
def is_space_free(x: float, y: float, radius: float, existing_planets: List[Planet], buffer: float = 150.0) -> bool:
    """Checks if a new planet at (x,y) overlaps with any existing planets."""
    for p in existing_planets:
        # Distance between centers
        d = dist((x, y), (p.x, p.y))
        # Minimum safe distance: sum of radii + orbital buffer
        if d < (radius + p.radius + buffer):
            return False
    return True







def reset_world(seed: Optional[int] = None) -> None:
    seed = int(seed) if seed is not None else random.randint(1, 10_000_000)
    rng = random.Random(seed)

    # Rocket start and destination
    STATE["t"] = 0.0
    STATE["status"] = "running"
    STATE["fail_reason"] = None
    STATE["last_plan_time"] = -1e9
    STATE["latched_planet_id"] = None
    STATE["countdown"] = 0.0

    rocket = Rocket(
        x=0.0,
        y=0.0,
        vx=3.0,
        vy=0.0,
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


    # version 5: last good version
    # for (x, y) in goods:
    #     planets.append(
    #         Planet(
    #             id=pid,
    #             x=x, y=y,
    #             mass=rng.uniform(*GOOD_MASS_RANGE),
    #             radius=rng.uniform(*PLANET_RADIUS_RANGE),
    #             kind="good",         # "Good planets" = blue
    #             revealed=False,
    #             # revealed=True,      # for debuging 
    #             recoverable=True,
    #             color = "#9bb0ff"
    #         )
    #     )
    #     pid += 1



    # for (x, y) in bads:
    #     # Some bad planets are "too strong" => unrecoverable
    #     unrecoverable = (rng.random() < 0.35)
    #     planets.append(
    #         Planet(
    #             id=pid,
    #             x=x, y=y,
    #             mass=rng.uniform(*BAD_MASS_RANGE) * (1.35 if unrecoverable else 1.0),
    #             radius=rng.uniform(*PLANET_RADIUS_RANGE) * (1.15 if unrecoverable else 1.0),
    #             kind="bad",             # "Bad planets" = red
    #             revealed=False,
    #             recoverable=not unrecoverable,
    #             color = "#ff2c2c"
    #         )
    #     )
    #     pid += 1



    # version 3: had initiall all three colors
    # for (x, y) in bads:
    #     # 1. Roll to decide if this "bad" spot is LETHAL (bad) or DANGEROUS (okay)
    #     is_lethal = rng.random() < 0.40  # 40% are Red, 60% are Orange
        
    #     if is_lethal:
    #         p_kind = "bad"
    #         p_color = "#ff2c2c" # Red
    #         recoverable = False
    #         mass_mult = 1.35    # Red stars are heavier
    #     else:
    #         p_kind = "okay"
    #         p_color = "#FF991c" # Orange
    #         recoverable = True
    #         mass_mult = 1.0     # Orange stars are standard

    #     planets.append(
    #         Planet(
    #             id=pid,
    #             x=x, y=y,
    #             mass=rng.uniform(*BAD_MASS_RANGE) * mass_mult,
    #             radius=rng.uniform(*PLANET_RADIUS_RANGE),
    #             kind=p_kind,
    #             revealed=False,
    #             # revealed=True,      # for debuging 
    #             recoverable=recoverable,
    #             color=p_color
    #         )
    #     )
    #     pid += 1



    # version 4: Last good version  only have blue and ornage planet in the begining 
    # for (x, y) in bads:
    #     # All "bad" positions start as "okay" (Orange)
    #     p_kind = "okay"
    #     p_color = "#FF991c"
        
    #     # 20% chance this orange star is actually a Red Giant/Lethal
    #     if rng.random() < 0.20:
    #         p_kind = "bad"
    #         p_color = "#ff2c2c"

    #     planets.append(
    #         Planet(
    #             id=pid,     # assign the id's to planet, to keep track of them
    #             x=x, y=y,
    #             mass=rng.uniform(*BAD_MASS_RANGE),
    #             radius=rng.uniform(*PLANET_RADIUS_RANGE),
    #             kind=p_kind,
    #             revealed=False, # Set back to False for gameplay!
    #             recoverable=True if p_kind == "okay" else False,
    #             color=p_color
    #         )
    #     )
    #     pid += 1    # new id for each planet generated


    for coords, is_good_pass in [(goods, True), (bads, False)]:
            for (x, y) in coords:
                p_radius = rng.uniform(*PLANET_RADIUS_RANGE)
                
                # Find a free spot using Jitter (Attempt up to 15 times)
                placed_x, placed_y = x, y
                found_spot = False
                
                for attempt in range(15):
                    # If first try fails, move the x,y randomly within a 150-unit box
                    test_x = x + (rng.uniform(-150, 150) if attempt > 0 else 0)
                    test_y = y + (rng.uniform(-150, 150) if attempt > 0 else 0)
                    
                    if is_space_free(test_x, test_y, p_radius, planets):
                        placed_x, placed_y = test_x, test_y
                        found_spot = True
                        break
                
                if not found_spot:
                    continue # Skip this planet if no room is found

                # 5. Define Planet Properties
                if is_good_pass:
                    # Always Blue
                    p_kind, p_color, p_recoverable = "good", "#9bb0ff", True
                    p_mass = rng.uniform(*GOOD_MASS_RANGE)
                else:
                    # Orange planets (20% chance of being secretly Red)
                    is_red = rng.random() < 0.20
                    p_kind = "bad" if is_red else "okay"
                    p_color = "#ff2c2c" if is_red else "#FF991c"
                    p_recoverable = not is_red
                    p_mass = rng.uniform(*BAD_MASS_RANGE)

                # 6. Add to list and increment pid
                planets.append(
                    Planet(
                        id=pid, x=placed_x, y=placed_y, mass=p_mass,
                        radius=p_radius, kind=p_kind, revealed=False,
                        recoverable=p_recoverable, color=p_color
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