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
import random

def clamp01_100(v: float) -> float:
    return max(0.0, min(100.0, v))

def arm_grace_counters_if_needed() -> None:
    """When food/water first hit 0, arm the grace planets counters."""
    if STATE.get("water", 100.0) <= 0 and STATE.get("water_grace_planets") is None:
        STATE["water_grace_planets"] = 1

    if STATE.get("food", 100.0) <= 0 and STATE.get("food_grace_planets") is None:
        STATE["food_grace_planets"] = 2

def check_instant_gameover() -> None:
    """Immediate game over conditions."""
    if STATE.get("oxygen", 100.0) <= 0:
        STATE["status"] = "failed"
        STATE["fail_reason"] = "oxygen_depleted"
        return

    if STATE.get("morale", 100.0) <= 0:
        STATE["status"] = "failed"
        STATE["fail_reason"] = "morale_depleted"
        return

def apply_morale_on_latch(kind: str) -> None:
    morale = float(STATE.get("morale", 100.0))

    if kind == "good":
        # streak grows only on good planets
        STATE["good_streak"] = int(STATE.get("good_streak", 0)) + 1
        streak = STATE["good_streak"]

        # streak bonus grows but caps
        bonus = min(2.0 + streak, 10.0)
        morale += bonus
    else:
        # reset streak on non-good planets
        STATE["good_streak"] = 0

        if kind == "okay":
            morale -= 10.0
        elif kind == "bad":
            morale -= 25.0
        else:
            # unknown kinds: no change
            pass

    STATE["morale"] = clamp01_100(morale)

def update_morale_from_low_stats(dt: float) -> None:
    morale = float(STATE.get("morale", 100.0))

    # -------------------------
    # DEBUG: super fast morale drop
    # Turn on/off by changing this flag.
    # -------------------------
    DEBUG_FAST_MORALE = False
    if DEBUG_FAST_MORALE:
        # drains 200 morale per sim-second -> hits 0 in ~0.5s
        morale -= 200.0 * dt
        STATE["morale"] = clamp01_100(morale)
        return

    # Normal logic (your existing one)
    oxygen = float(STATE.get("oxygen", 100.0))
    food = float(STATE.get("food", 100.0))
    ship = float(STATE.get("ship_health", 100.0))
    crew = float(STATE.get("crew_health", 100.0))

    pen = 0.0
    if oxygen < 50.0: pen += 1.6
    if food < 50.0:   pen += 0.8
    if ship < 50.0:   pen += 1.2
    if crew < 50.0:   pen += 1.2

    morale -= pen * dt
    STATE["morale"] = clamp01_100(morale)


def maybe_create_latch_event(planet_id: str) -> None:
    # Don’t overwrite an existing event
    if STATE.get("pending_event") is not None:
        return

    # Example: 50/50 which event appears (tweak later)
    # You can also do weighted choices.
    r = random.random()

    if r < 0.5:
        # Ship repair event (your existing one)
        STATE["pending_event"] = {
            "type": "planet_latch_repair",
            "planet_id": planet_id,
            "prompt": "Vessel latched. Stop to repair ship?",
            "choices": [
                {"id": "repair", "label": "YES, PROCEED"},
                {"id": "skip", "label": "NO, STAY IN ORBIT"},
            ],
        }
    else:
        # New: water recycler failure event
        STATE["pending_event"] = {
            "type": "planet_water_recycler",
            "planet_id": planet_id,
            "prompt": "Water recycler is failing. Stop to fix it?",
            "choices": [
                {"id": "fix", "label": "YES, FIX IT"},
                {"id": "ignore", "label": "NO, RISK IT"},
            ],
        }


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
    
    # 1. ORBITING LOGIC
    if STATE.get("latched_planet_id") is not None:
        # Find the planet we are latched to
        p = next((p for p in planets if p.id == STATE["latched_planet_id"]), None)
        if not p: return

        if p.kind == "okay":
            STATE["countdown"] -= dt 
            if STATE["countdown"] <= 0:
                p.kind = "bad"
                p.color = "#ff2c2c"
                STATE["status"] = "failed"
                STATE["fail_reason"] = "planet_instability_explosion"
                return

        # Orbital Physics
        dx, dy = rocket.x - p.x, rocket.y - p.y
        r = math.sqrt(dx * dx + dy * dy)
        orbital_speed = math.sqrt(G * p.mass / r)
        tx, ty = dy / r, -dx / r # Tangent vector
        
        target_vx = tx * orbital_speed
        target_vy = ty * orbital_speed

        # Smooth blending
        SMOOTH_FACTOR = 0.1 
        rocket.vx += (target_vx - rocket.vx) * SMOOTH_FACTOR
        rocket.vy += (target_vy - rocket.vy) * SMOOTH_FACTOR

        # Radial Correction
        TARGET_R = p.radius + 20.0
        r_err = TARGET_R - r
        rocket.x += (dx / r) * r_err * 0.1
        rocket.y += (dy / r) * r_err * 0.1

        rocket.x += rocket.vx * dt
        rocket.y += rocket.vy * dt
        return

    # 2. CAPTURE & CRASH LOGIC
    for p in planets:
        d = dist((rocket.x, rocket.y), (p.x, p.y))
        CAPTURE_ZONE = p.radius + 20.0 

        # A. DEAD CENTER CRASH (Priority)
        if d <= (p.radius * CRASH_RADIUS_FACTOR):
            STATE["status"] = "failed"
            STATE["fail_reason"] = f"crashed_into_{p.id}"
            return

        # B. LATCH CHECK
        if not p.revealed and d <= CAPTURE_ZONE:
            p.revealed = True
            # --- Grace-based depletion game over (triggered on planet stops) ---
            arm_grace_counters_if_needed()

            # If water is 0 and grace is already used up -> game over BEFORE latching
            if STATE.get("water", 100.0) <= 0:
                gp = STATE.get("water_grace_planets")
                if gp is not None and gp <= 0:
                    STATE["status"] = "failed"
                    STATE["fail_reason"] = "water_depleted"
                    return

            # If food is 0 and grace is already used up -> game over BEFORE latching
            if STATE.get("food", 100.0) <= 0:
                gp = STATE.get("food_grace_planets")
                if gp is not None and gp <= 0:
                    STATE["status"] = "failed"
                    STATE["fail_reason"] = "food_depleted"
                    return

            STATE["latched_planet_id"] = p.id
            # If we are at/below 0, spending a planet stop consumes grace
            if STATE.get("water", 100.0) <= 0 and STATE.get("water_grace_planets") is not None:
                STATE["water_grace_planets"] -= 1

            if STATE.get("food", 100.0) <= 0 and STATE.get("food_grace_planets") is not None:
                STATE["food_grace_planets"] -= 1

            apply_morale_on_latch(p.kind)

            STATE["food"] = max(0.0, STATE.get("food", 100.0) - 10.0)

            # after orbiting a planet, the consecutive burns should reset
            STATE["consecutive_burns"] = 0   # Resets the 3/3 counter to 0/3
            STATE["can_space_burn"] = True    # Unlocks the "Red" lockout
            # STATE["space_burns_left"] = 10    # (Optional) Replenish charges on landing
            if STATE.get("pending_event") is None:
                # (optional) only ask on good planets to match your current UI
                if p.kind == "good":
                    maybe_create_latch_event(p.id)


            # Snap position to avoid clipping
            push_x, push_y = (rocket.x - p.x) / d, (rocket.y - p.y) / d
            rocket.x = p.x + push_x * CAPTURE_ZONE
            rocket.y = p.y + push_y * CAPTURE_ZONE
            
            if p.kind == "okay":
                STATE["countdown"] = 10.0
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

    # Always tick resources + gameover, even if a prompt is open
    update_resources(dt)
    arm_grace_counters_if_needed()
    check_instant_gameover()
    if STATE["status"] != "running":
        return

    # If an event prompt is up, pause physics, but keep the world “alive”
    if STATE.get("pending_event") is not None:
        update_camera()
        return

    update_reveals_and_collisions(dt)

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

    update_morale_from_low_stats(dt)
    update_camera()


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


# this is about the 3-times allowed propulsion (out of orbit)
def apply_propulsion(dvx, dvy):
    is_latched = STATE.get("latched_planet_id") is not None
    
    if is_latched:
        # Standard propulsion: Always allowed in orbit
        STATE["rocket"].vx += dvx
        STATE["rocket"].vy += dvy
        # Once you launch from orbit, you are back in space
        STATE["latched_planet_id"] = None 
        # Reset the space burn cooldown so you can use one immediately if needed
        STATE["can_space_burn"] = True 
        
    elif STATE["space_burns_left"] > 0 and STATE["can_space_burn"]:
        # Emergency Space Burn: Allowed only 3 times, not in a row
        STATE["rocket"].vx += dvx
        STATE["rocket"].vy += dvy
        STATE["space_burns_left"] -= 1
        STATE["can_space_burn"] = False # Lock the next space burn
    else:
        # Action blocked: Either out of charges or cooldown active
        pass

# 
def update_resources(dt: float) -> None:
    # DEBUG: super fast oxygen drain
    DEBUG_FAST_OXYGEN = True
    if DEBUG_FAST_OXYGEN:
        STATE["oxygen"] -= 200.0 * dt  # hits 0 in ~0.5 sec
    else:
        STATE["oxygen"] -= 0.05 * dt
    # 1. Oxygen and Food drop slowly over time
    # (0.05 units per second means ~33 minutes of real-time play)
    STATE["food"] -= 0.03 * dt

    # 
    
    # 2. Fuel only drops when the rocket is NOT latched (moving through deep space)
    if STATE.get("latched_planet_id") is None:
        STATE["fuel"] -= 0.01 * dt

    # 3. Crew Health starts dropping if Oxygen or Food hits 0
    if STATE["oxygen"] <= 0 or STATE["food"] <= 0:
        STATE["crew_survival"] -= 0.5 * dt # Health drops faster than resources

    if STATE.get("water_recycler_broken", False):
        STATE["water"] -= 0.10 * dt  # faster drain
    else:
        STATE["water"] -= 0.04 * dt  # normal

    # Clamp everything to 0 so they don't go negative
    for key in ["oxygen", "food", "water", "fuel", "crew_health"]:
        STATE[key] = max(0, STATE[key])