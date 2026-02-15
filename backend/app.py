from flask import Flask, jsonify, request
from flask_cors import CORS

from sim.world import reset_world
from sim.serialize import state_payload
from sim.physics import step_sim
from sim.state import STATE
from sim.config import clamp, DT_MIN, DT_MAX, DV_MAX, PLAN_COOLDOWN_S
from sim.mathutil import norm, unit

app = Flask(__name__)
CORS(app)

@app.get("/api/state")
def api_state():
    return jsonify(state_payload())

@app.post("/api/reset")
def api_reset():
    data = request.get_json(silent=True) or {}
    seed = data.get("seed")
    reset_world(seed=seed)
    return jsonify(state_payload())


# version 0 : last working version (wt counter decreasing yet)
# @app.post("/api/plan")
# def api_plan():
#     if STATE["status"] != "running":
#         return jsonify(state_payload())

#     data = request.get_json(silent=True) or {}
#     t = float(STATE["t"])

#     if (t - float(STATE["last_plan_time"])) < PLAN_COOLDOWN_S:
#         return jsonify(state_payload())

#     rocket = STATE["rocket"]

#     if "dvx" in data and "dvy" in data:
#         dvx = float(data["dvx"])
#         dvy = float(data["dvy"])
#     else:
#         dx = float(data.get("dx", 0.0))
#         dy = float(data.get("dy", 0.0))
#         pixels_to_world = float(data.get("pixels_to_world", 1.0))
#         dvx = dx * pixels_to_world
#         dvy = dy * pixels_to_world

#     mag = norm(dvx, dvy)
#     if mag > DV_MAX:
#         ux, uy = unit(dvx, dvy)
#         dvx, dvy = ux * DV_MAX, uy * DV_MAX

#     rocket.vx += dvx
#     rocket.vy += dvy
#     STATE["latched_planet_id"] = None   # such that the user can fire again, when rocket latches onto orbit
#     STATE["last_plan_time"] = t
#     return jsonify(state_payload())



# version1: taking into account the difference between like 
# @app.post("/api/plan")
# def api_plan():
#     if STATE["status"] != "running":
#         return jsonify(state_payload())

#     data = request.get_json(silent=True) or {}
#     t = float(STATE["t"])

#     # 1. Anti-spam cooldown check
#     if (t - float(STATE["last_plan_time"])) < PLAN_COOLDOWN_S:
#         return jsonify(state_payload())

#     rocket = STATE["rocket"]
#     is_latched = STATE.get("latched_planet_id") is not None

#     # 2. EMERGENCY BURN LOGIC: Only allow if latched OR if charges remain
#     if not is_latched:
#         burns_left = STATE.get("space_burns_left", 0)
        
#         can_burn = STATE.get("can_space_burn", True)
        
#         if burns_left <= 0 or not can_burn:
#             # Block the move if out of charges or cooling down
#             return jsonify(state_payload())

#     # 3. APPLY VELOCITY (standard physics)
#     dvx = float(data.get("dvx", 0.0))
#     dvy = float(data.get("dvy", 0.0))
#     rocket.vx += dvx
#     rocket.vy += dvy

#     # 4. UPDATE CHARGES
#     if is_latched:
#         # Orbital: Unlimited burns + Reset the space capability
#         STATE["latched_planet_id"] = None
#         STATE["can_space_burn"] = True 
#     else:
#         # Deep Space: Spend a charge and lock until next latch
#         STATE["space_burns_left"] -= 1
#         STATE["can_space_burn"] = False 
#         # Deduct 15% fuel for emergency maneuvers
#         STATE["fuel"] = max(0, STATE.get("fuel", 100) - 15.0) 

#     STATE["last_plan_time"] = t
#     return jsonify(state_payload())


# versio2 : allowing multiple consecutive propulsion
@app.post("/api/plan")
def api_plan():
    if STATE["status"] != "running":
        return jsonify(state_payload())

    data = request.get_json(silent=True) or {}
    t = float(STATE["t"])
    rocket = STATE["rocket"]
    is_latched = STATE.get("latched_planet_id") is not None

    # --- UPDATED PROPULSION LOGIC ---
    if not is_latched:
        total_left = STATE.get("space_burns_left", 0)
        burst_count = STATE.get("consecutive_burns", 0)
        
        # Check total pool (10) and burst limit (3)
        if total_left <= 0 or burst_count >= 3:
            return jsonify(state_payload())

    # Apply Velocity
    dvx = float(data.get("dvx", 0.0))
    dvy = float(data.get("dvy", 0.0))
    rocket.vx += dvx
    rocket.vy += dvy

    # Handle State Transitions
    if is_latched:
        STATE["latched_planet_id"] = None
        STATE["consecutive_burns"] = 0   # Reset when taking off from a planet
        STATE["can_space_burn"] = True
    else:
        # Increment the burst count
        STATE["consecutive_burns"] = STATE.get("consecutive_burns", 0) + 1 
        STATE["space_burns_left"] -= 1
        
        # If 3 burns are hit, lock the engines
        if STATE["consecutive_burns"] >= 3:
            STATE["can_space_burn"] = False
            
    STATE["last_plan_time"] = t
    return jsonify(state_payload())









@app.post("/api/step")
def api_step():
    data = request.get_json(silent=True) or {}
    dt = float(data.get("dt", 0.016))
    dt = clamp(dt, DT_MIN, DT_MAX)
    step_sim(dt)
    return jsonify(state_payload())

if __name__ == "__main__":
    reset_world()
    app.run(host="127.0.0.1", port=5000, debug=True)
