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




# version1: rocket doenst stop yet
# def update_reveals_and_collisions() -> None:
#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]
#     rx, ry = rocket.x, rocket.y

#     for p in planets:
#         d = dist((rx, ry), (p.x, p.y))

#         # Reveal on approach
#         if not p.revealed and d <= (p.radius + REVEAL_MARGIN):
#             p.revealed = True

#         # Crash into any planet (simple rule)
#         if d <= (p.radius * CRASH_RADIUS_FACTOR):
#             STATE["status"] = "failed"
#             STATE["fail_reason"] = f"crashed_into_planet_{p.id}"
#             return

#         # Unrecoverable bad planet death-zone
#         if p.kind == "bad" and (not p.recoverable):
#             if d <= (p.radius * DEATH_RADIUS_FACTOR):
#                 STATE["status"] = "failed"
#                 STATE["fail_reason"] = f"overwhelmed_by_gravity_{p.id}"
#                 return




# Version 2: implementation of latching, not working, it just directly crahsing 
# def update_reveals_and_collisions(dt: float) -> None:
#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]
#     rx, ry = rocket.x, rocket.y

#     # --- 1. HANDLE EXISTING LATCH ---
#     if STATE.get("latched_planet_id") is not None:
#         # Find the planet we are stuck to
#         p = next((p for p in planets if p.id == STATE["latched_planet_id"]), None)
#         if p:
#             # Lock rocket to planet center
#             rocket.x, rocket.y = p.x, p.y
#             rocket.vx, rocket.vy = 0.0, 0.0 
            
#             # If it's "okay" (Orange), tick the timer
#             if p.kind == "okay":
#                 STATE["countdown"] -= dt
#                 if STATE["countdown"] <= 0:
#                     STATE["status"] = "failed"
#                     STATE["fail_reason"] = "planet_instability_explosion"
#         return

#     # --- 2. CHECK FOR NEW LATCHES & COLLISIONS ---
#     for p in planets:
#         d = dist((rx, ry), (p.x, p.y))

#         # NEW: Latch on approach (Reveal Margin = Orbital Radius)
#         if not p.revealed and d <= (p.radius + REVEAL_MARGIN):
#             p.revealed = True
#             STATE["latched_planet_id"] = p.id
            
#             # Stop the rocket immediately
#             rocket.vx, rocket.vy = 0.0, 0.0
#             rocket.x, rocket.y = p.x, p.y
            
#             # Start timer if orange
#             if p.kind == "okay":
#                 STATE["countdown"] = 10.0
#             return

#         # Crash logic (only for revealed planets)
#         if d <= (p.radius * CRASH_RADIUS_FACTOR):
#             STATE["status"] = "failed"
#             STATE["fail_reason"] = f"crashed_into_planet_{p.id}"
#             return

#         # Death zone logic
#         if p.kind == "bad" and (not p.recoverable):
#             if d <= (p.radius * DEATH_RADIUS_FACTOR):
#                 STATE["status"] = "failed"
#                 STATE["fail_reason"] = f"overwhelmed_by_gravity_{p.id}"
#                 return

# version 3: still latching onto the center
# def update_reveals_and_collisions(dt: float) -> None:
#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]
    
#     # 1. If already latched, keep us frozen
#     if STATE.get("latched_planet_id") is not None:
#         p = next((p for p in planets if p.id == STATE["latched_planet_id"]), None)
#         if p:
#             rocket.x, rocket.y = p.x, p.y
#             rocket.vx, rocket.vy = 0.0, 0.0
#         return

#     # 2. Check for new captures
#     for p in planets:
#         d = dist((rocket.x, rocket.y), (p.x, p.y))
        
#         # THE CAPTURE ZONE (Arbitrary value: 120 units)
#         CAPTURE_DISTANCE = p.radius + 120.0

#         if not p.revealed and d <= CAPTURE_DISTANCE:
#             # LATCH IMMEDIATELY
#             p.revealed = True
#             STATE["latched_planet_id"] = p.id
            
#             # KILL PHYSICS
#             rocket.vx, rocket.vy = 0.0, 0.0
#             rocket.x, rocket.y = p.x, p.y # Snap to center
#             return # Stop checking other planets this frame

#         # THE CRASH ZONE (Only if already revealed and we got too close)
#         if d <= (p.radius * CRASH_RADIUS_FACTOR):
#             STATE["status"] = "failed"
#             STATE["fail_reason"] = f"crashed_into_{p.id}"
#             return

# version 4: last working model, USE THIS ONE!
# def update_reveals_and_collisions(dt: float) -> None:
#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]
    
#     # 1. If already latched, stay frozen exactly where we are
#     if STATE.get("latched_planet_id") is not None:
#         rocket.vx, rocket.vy = 0.0, 0.0
#         return

#     # 2. Check for new captures
#     for p in planets:
#         d = dist((rocket.x, rocket.y), (p.x, p.y))
        
#         CAPTURE_ZONE = p.radius + 20.0      # establich the orbital zone at which the rocket can "latch onto"

#         # LATCH ON THE EDGE
#         if not p.revealed and d <= CAPTURE_ZONE:
#             p.revealed = True
#             STATE["latched_planet_id"] = p.id
            
#             # STOP IMMEDIATELY at the current position (the edge)
#             rocket.vx, rocket.vy = 0.0, 0.0
            
#             # Remove the line that sets rocket.x/y to p.x/y!
#             return 

#         # CRASH LOGIC
#         # Now this only triggers if the user was "aiming for the center"
#         # and bypassed the capture zone logic (or if planet is already revealed)
#         if d <= (p.radius * CRASH_RADIUS_FACTOR):
#             STATE["status"] = "failed"
#             STATE["fail_reason"] = f"crashed_into_{p.id}"
#             return

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
                p.color = "#ff2c2c"
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



# old version ; rocket doesnt latch 
# def step_sim(dt: float) -> None:
#     if STATE["status"] != "running":
#         return

#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]

#     ax, ay = accel_from_planets(rocket, planets)

#     # Semi-implicit Euler (good stability for games)
#     rocket.vx += ax * dt
#     rocket.vy += ay * dt
#     rocket.x += rocket.vx * dt
#     rocket.y += rocket.vy * dt

#     STATE["t"] += dt

#     update_reveals_and_collisions()
#     if STATE["status"] == "running":
#         check_success_and_bounds()

#     update_camera()



# Version2: this version is working trying to implement latching 
# def step_sim(dt: float) -> None:
#     if STATE["status"] != "running":
#         return

#     # Pass dt to update_reveals_and_collisions for the timer
#     update_reveals_and_collisions(dt)
    
#     # Only move the rocket if we aren't latched
#     if STATE.get("latched_planet_id") is None:
#         rocket: Rocket = STATE["rocket"]
#         planets: List[Planet] = STATE["planets"]

#         ax, ay = accel_from_planets(rocket, planets)

#         rocket.vx += ax * dt
#         rocket.vy += ay * dt
#         rocket.x += rocket.vx * dt
#         rocket.y += rocket.vy * dt

#     STATE["t"] += dt

#     if STATE["status"] == "running":
#         check_success_and_bounds()

#     update_camera()



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
