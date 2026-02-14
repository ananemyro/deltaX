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

    # If latched, gravity doesn't move us (we are stuck)
    if STATE.get("latched_planet_id") is not None:
        return 0.0, 0.0

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



# version 4: implementation of gravitational assist to slingshot 
def update_reveals_and_collisions(dt: float) -> None:
    rocket: Rocket = STATE["rocket"]
    planets: List[Planet] = STATE["planets"]
    
    if STATE.get("latched_planet_id") is not None:

        # --- NEW: Orbiting Logic ---
        p = next(p for p in planets if p.id == STATE["latched_planet_id"])
        

        # --- NEW: COUNTDOWN LOGIC ---
        if p.kind == "okay":
            STATE["countdown"] -= dt # Subtract time passed
            
            # If time runs out, the planet turns red and explodes
        if STATE["countdown"] <= 0:
                p.kind = "bad"
                p.color = "#ff2c2c" # Turn Red
                STATE["status"] = "failed"
                STATE["fail_reason"] = "planet_instability_explosion"


        # 1. Calculate the vector from planet to rocket
        dx, dy = rocket.x - p.x, rocket.y - p.y
        r = math.sqrt(dx * dx + dy * dy)
        
        # 2. Required velocity for a stable orbit
        orbital_speed = math.sqrt(G * p.mass / r)
        
        # 3. Calculate Tangent Vector (perpendicular to radius)
        # To go clockwise: (dx, dy) -> (dy, -dx)
        tx, ty = dy / r, -dx / r
        
        # 4. Apply velocity and move rocket along the circle
        rocket.vx, rocket.vy = tx * orbital_speed, ty * orbital_speed
        rocket.x += rocket.vx * dt
        rocket.y += rocket.vy * dt
        return

    for p in planets:
        d = dist((rocket.x, rocket.y), (p.x, p.y))
        CAPTURE_ZONE = p.radius + 20.0 # Your new tighter radius

        if not p.revealed and d <= CAPTURE_ZONE:
            p.revealed = True
            STATE["latched_planet_id"] = p.id
            # We don't stop anymore! The logic above takes over next frame.
            # Initialize timer if we hit an orange planet

            if p.kind == "okay":    # its and orange planet
                STATE["countdown"] = 10.0   # start the countdown before it turrns red
            return
        
        # CRASH LOGIC
        # Now this only triggers if the user was "aiming for the center"
        # and bypassed the capture zone logic (or if planet is already revealed)
        if d <= (p.radius * CRASH_RADIUS_FACTOR):
            STATE["status"] = "failed"
            STATE["fail_reason"] = f"crashed_into_{p.id}"
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

    # This now handles both "capture" and "orbital movement"
    update_reveals_and_collisions(dt)
    
    # Only calculate general gravity if we aren't locked into an orbit
    if STATE.get("latched_planet_id") is None:
        ax, ay = accel_from_planets(STATE["rocket"], STATE["planets"])
        rocket = STATE["rocket"]
        rocket.vx += ax * dt
        rocket.vy += ay * dt
        rocket.x += rocket.vx * dt
        rocket.y += rocket.vy * dt

    STATE["t"] += dt
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