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
# def update_reveals_and_collisions(dt: float) -> None:
#     rocket: Rocket = STATE["rocket"]
#     planets: List[Planet] = STATE["planets"]
    
#     if STATE.get("latched_planet_id") is not None:

#         # --- NEW: Orbiting Logic ---
#         p = next(p for p in planets if p.id == STATE["latched_planet_id"])
        

#         # --- NEW: COUNTDOWN LOGIC ---
#         if p.kind == "okay":
#             STATE["countdown"] -= dt # Subtract time passed
            
#             # If time runs out, the planet turns red and explodes
#             if STATE["countdown"] <= 0:
#                 p.kind = "bad"
#                 p.color = "#ff2c2c" # Turn Red
#                 STATE["status"] = "failed"
#                 STATE["fail_reason"] = "planet_instability_explosion"


#         # 1. Calculate the vector from planet to rocket
#         dx, dy = rocket.x - p.x, rocket.y - p.y
#         r = math.sqrt(dx * dx + dy * dy)
        
#         # 2. Required velocity for a stable orbit
#         orbital_speed = math.sqrt(G * p.mass / r)
        
#         # 3. Calculate Tangent Vector (perpendicular to radius)
#         # To go clockwise: (dx, dy) -> (dy, -dx)
#         tx, ty = dy / r, -dx / r
        
#         # 4. Apply velocity and move rocket along the circle
#         # rocket.vx, rocket.vy = tx * orbital_speed, ty * orbital_speed # for debugging 
#         target_vx = tx * orbital_speed
#         target_vy = ty * orbital_speed
#         # SMOOTH_FACTOR = 0.05 # Lower = smoother/rubbery, Higher = snappier
#         # rocket.vx += (target_vx - rocket.vx) * SMOOTH_FACTOR
#         # rocket.vy += (target_vy - rocket.vy) * SMOOTH_FACTOR
#         SMOOTH_FACTOR = 1 
#         rocket.vx += (target_vx - rocket.vx) * SMOOTH_FACTOR
#         rocket.vy += (target_vy - rocket.vy) * SMOOTH_FACTOR

        
#         # This gently pulls the rocket onto the specific orbit radius (radius + 20)
#         TARGET_R = p.radius + 20.0
#         r_err = TARGET_R - r
#         # Nudge position toward the ideal circle line
#         rocket.x += (dx / r) * r_err * 0.1
#         rocket.y += (dy / r) * r_err * 0.1

#         # Final Movement
#         rocket.x += rocket.vx * dt
#         rocket.y += rocket.vy * dt

#         return

#     # version 1: somehow rocket crashing into planet way to often 
#     # for p in planets:
#     #     d = dist((rocket.x, rocket.y), (p.x, p.y))
#     #     CAPTURE_ZONE = p.radius + 20.0 # Your new tighter radius

#     #     if not p.revealed and d <= CAPTURE_ZONE:
#     #         p.revealed = True
#     #         STATE["latched_planet_id"] = p.id
#     #         # We don't stop anymore! The logic above takes over next frame.
#     #         # Initialize timer if we hit an orange planet

#     #         if p.kind == "okay":    # its and orange planet
#     #             STATE["countdown"] = 10.0   # start the countdown before it turrns red
#     #         return
        
#     #     # CRASH LOGIC
#     #     # Now this only triggers if the user was "aiming for the center"
#     #     # and bypassed the capture zone logic (or if planet is already revealed)
#     #     if d <= (p.radius * CRASH_RADIUS_FACTOR):
#     #         STATE["status"] = "failed"
#     #         STATE["fail_reason"] = f"crashed_into_{p.id}"
#     #         return





# # Inside update_reveals_and_collisions in physics.py

#     for p in planets:
#         d = dist((rocket.x, rocket.y), (p.x, p.y))
#         CAPTURE_ZONE = p.radius + 20.0 

#         # 1. PRIORITY: Latch Logic
#         if not p.revealed and d <= CAPTURE_ZONE:
#             p.revealed = True
#             STATE["latched_planet_id"] = p.id
            
#             # --- THE FIX: SNAP TO ORBIT ---
#             # Calculate the "push out" direction
#             push_x = (rocket.x - p.x) / d
#             push_y = (rocket.y - p.y) / d
            
#             # Force the rocket to the EXACT edge of the orbit line
#             # This prevents it from ever being "inside" the crash zone on entry
#             rocket.x = p.x + push_x * CAPTURE_ZONE
#             rocket.y = p.y + push_y * CAPTURE_ZONE
            
#             if p.kind == "okay":
#                 STATE["countdown"] -= 10.0
#             return
            
#             # # Stop checking this frame! This prevents the crash logic below
#             # # from seeing you inside the planet.
#             #     if STATE["countdown"] <= 0:
#             #         p.kind = "bad"
#             #         p.color = "#ff2c2c"
#             #         STATE["status"] = "failed"
#             #         STATE["fail_reason"] = "planet_instability_explosion"
#             #         return # Exit early if we failed

#         # 2. Crash Logic (Only checked if we didn't just latch)
#         if d <= (p.radius * CRASH_RADIUS_FACTOR):
#             STATE["status"] = "failed"
#             STATE["fail_reason"] = f"crashed_into_{p.id}"
#             return




# ------------------
#   1. Check if you are already in orbit
#       - if yes, then do the math to keep the rocket orbiting the planet
#   2. if you are not yet in orbit, then 
#       - then you need to see if the user was aiming towards the center of the planet, aka GAME OVER
#
#   Note: 
# • CAPTURE_LINE : distance from the center of the planet
# • CAPTURE_ZONE : 
# ------------------
def update_reveals_and_collisions(dt: float) -> None:
    rocket: Rocket = STATE["rocket"]
    planets: List[Planet] = STATE["planets"]
    

    # 1. checks if you are already in orbit 
    if STATE.get("latched_planet_id") is not None:
        # Find the specific planet we are orbiting
        p = next(p for p in planets if p.id == STATE["latched_planet_id"])
        

        # for the 'okay' (orange) planets, you start the countdown timer on the screen
        if p.kind == "okay":
            STATE["countdown"] -= dt # Subtract time passed
            
            # If time runs out, the planet turns red and explodes
            if STATE["countdown"] <= 0:
                p.kind = "bad"
                p.color = "#ff2c2c" # Change color to Red in the state
                STATE["status"] = "failed"
                STATE["fail_reason"] = "planet_instability_explosion"
                return


        # -------- THE MATH BEHIND THE ROCKET's ORBIT AROUND THE PLANET
        # The following is to calculate the math behind the orbiting
        # i.e the orbital_speed, based on the distance and planet's mass
        dx, dy = rocket.x - p.x, rocket.y - p.y
        r = math.sqrt(dx * dx + dy * dy)
        
        # Required velocity for a stable orbit based on G and planet mass
        orbital_speed = math.sqrt(G * p.mass / r)
        
        # Tangent Vector (Clockwise): (dx, dy) -> (dy, -dx)
        tx, ty = dy / r, -dx / r
        target_vx = tx * orbital_speed
        target_vy = ty * orbital_speed


        # ---- THIS IS TO SMOOTH OUT THE "LATCHING" of the rocket
        # We blend the current velocity toward the target to prevent "snappy" jerks
        SMOOTH_FACTOR = 0.1 
        rocket.vx += (target_vx - rocket.vx) * SMOOTH_FACTOR
        rocket.vy += (target_vy - rocket.vy) * SMOOTH_FACTOR

        # RADIAL CORRECTION (The "Tractor Beam")
        # Gently nudge position toward the ideal orbital radius (radius + 20)
        TARGET_R = p.radius + 20.0
        r_err = TARGET_R - r
        rocket.x += (dx / r) * r_err * 0.1
        rocket.y += (dy / r) * r_err * 0.1

        # Apply final velocity to move rocket
        rocket.x += rocket.vx * dt
        rocket.y += rocket.vy * dt
        return



    # 2. CHECK FOR NEW COLLISIONS & CAPTURES
    for p in planets:
        d = dist((rocket.x, rocket.y), (p.x, p.y))
        CAPTURE_ZONE = p.radius + 20.0 # Standard orbital distance

        # --- A. DEAD CENTER CHECK (Highest Priority) ---
        # If the rocket is heading straight for the core, it crashes regardless of color.
        # CRASH_RADIUS_FACTOR is typically around 0.8 to 1.0 of the visual radius.
        if d <= (p.radius * CRASH_RADIUS_FACTOR):
            STATE["status"] = "failed"
            STATE["fail_reason"] = f"crashed_into_{p.id}"
            return

        # --- B. ORBITAL LATCH CHECK (Priority 2) ---
        # If we aren't aimed at the center, check if we've touched the capture line.
        if not p.revealed and d <= CAPTURE_ZONE:
            p.revealed = True
            STATE["latched_planet_id"] = p.id
            
            # SNAP TO ORBIT: Force position to the edge to prevent clipping into the planet
            push_x, push_y = (rocket.x - p.x) / d, (rocket.y - p.y) / d
            rocket.x = p.x + push_x * CAPTURE_ZONE
            rocket.y = p.y + push_y * CAPTURE_ZONE
            
            # Start 10s fuse only for Orange planets
            if p.kind == "okay":
                STATE["countdown"] = 10.0
            else:
                # Blue planets are stable, so we effectively ignore the countdown
                STATE["countdown"] = 0.0
                
            return # Exit loop so we don't check other planets this frame
        





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




# version 1: when rocket latches onto the orbit, the camaera frame "SNAPS" ...
# def update_camera() -> None:
#     rocket: Rocket = STATE["rocket"]
#     cam: Camera = STATE["camera"]

#     # Current speed
#     vx, vy = rocket.vx, rocket.vy
#     speed = math.hypot(vx, vy)

#     # --- LOOKAHEAD: cap how far ahead we look in WORLD units ---
#     # Max lookahead distance in world coords (tune 120..400)
#     MAX_AHEAD = 220.0

#     if speed > 1e-6:
#         ux, uy = vx / speed, vy / speed
#     else:
#         ux, uy = 0.0, 0.0

#     # Map speed to ahead distance, but cap it hard
#     # (tune the 6.0 to change how quickly it reaches MAX_AHEAD)
#     ahead = min(MAX_AHEAD, 6.0 * speed)

#     target_x = rocket.x + ux * ahead
#     target_y = rocket.y + uy * ahead

#     # --- SMOOTHING: keep it stable ---
#     # With DV_MAX=60 you generally want strong follow
#     alpha = CAM_ALPHA  # keep your config value
#     cam.cx += (target_x - cam.cx) * alpha
#     cam.cy += (target_y - cam.cy) * alpha

#     # --- SAFETY SNAP: if rocket would be off-screen, snap to rocket ---
#     # This uses a world-distance threshold (tune 350..800 depending on zoom/scale)
#     SNAP_DIST = 500.0
#     dx = rocket.x - cam.cx
#     dy = rocket.y - cam.cy
#     if (dx * dx + dy * dy) > (SNAP_DIST * SNAP_DIST):
#         cam.cx = rocket.x
#         cam.cy = rocket.y



# def update_camera() -> None:
#     rocket: Rocket = STATE["rocket"]
#     cam: Camera = STATE["camera"]

#     # 1. Check if we are currently latched
#     is_latched = STATE.get("latched_planet_id") is not None

#     vx, vy = rocket.vx, rocket.vy
#     speed = math.hypot(vx, vy)

#     # 2. Adjust Lookahead
#     # If flying: Look ahead by 220 units. 
#     # If latched: Set to 0 so the camera centers on the rocket/planet.
#     MAX_AHEAD = 0.0 if is_latched else 220.0

#     if speed > 1e-6:
#         ux, uy = vx / speed, vy / speed
#     else:
#         ux, uy = 0.0, 0.0

#     ahead = min(MAX_AHEAD, 6.0 * speed)
#     target_x = rocket.x + ux * ahead
#     target_y = rocket.y + uy * ahead

#     # 3. Dynamic Smoothing (Alpha)
#     # If latched, we use a much smaller alpha (0.03) to make the camera 
#     # "drift" slowly into position rather than snapping.
#     alpha = 0.03 if is_latched else CAM_ALPHA 
    
#     cam.cx += (target_x - cam.cx) * alpha
#     cam.cy += (target_y - cam.cy) * alpha

#     # 4. Remove or increase the "Safety Snap"
#     # The safety snap usually causes the biggest "jerk"
#     SNAP_DIST = 800.0 # Increase this so it doesn't trigger during smooth orbits
#     dx = rocket.x - cam.cx
#     dy = rocket.y - cam.cy
#     if (dx * dx + dy * dy) > (SNAP_DIST * SNAP_DIST):
#         cam.cx = rocket.x
#         cam.cy = rocket.y



def update_camera() -> None:
    rocket: Rocket = STATE["rocket"]
    cam: Camera = STATE["camera"]

    latched_id = STATE.get("latched_planet_id")
    is_latched = latched_id is not None

    if is_latched:
        # Find the planet we are stuck to
        p = next(p for p in STATE["planets"] if p.id == latched_id)
        # The camera's goal is now the planet's center, not the moving rocket
        target_x, target_y = p.x, p.y
        # Use a very firm alpha so it settles quickly and stays there
        alpha = 0.05 
    else:
        # Standard flying logic
        vx, vy = rocket.vx, rocket.vy
        speed = math.hypot(vx, vy)
        
        # Keep your lookahead logic for flight
        MAX_AHEAD = 220.0
        ux, uy = (vx / speed, vy / speed) if speed > 1e-6 else (0.0, 0.0)
        ahead = min(MAX_AHEAD, 6.0 * speed)
        
        target_x = rocket.x + ux * ahead
        target_y = rocket.y + uy * ahead
        alpha = CAM_ALPHA

    # Apply the movement
    cam.cx += (target_x - cam.cx) * alpha
    cam.cy += (target_y - cam.cy) * alpha

    # --- SAFETY: Disable the "Safety Snap" when latched ---
    if not is_latched:
        SNAP_DIST = 800.0
        dx = rocket.x - cam.cx
        dy = rocket.y - cam.cy
        if (dx * dx + dy * dy) > (SNAP_DIST * SNAP_DIST):
            cam.cx = rocket.x
            cam.cy = rocket.y