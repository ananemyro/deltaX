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

import random

@app.post("/api/event/resolve")
def api_event_resolve():
    if STATE["status"] != "running":
        return jsonify(state_payload())

    data = request.get_json(silent=True) or {}
    choice = data.get("choice")

    ev = STATE.get("pending_event")
    if not ev:
        return jsonify(state_payload())

    ev_type = ev.get("type")

    valid = {
        "planet_latch_repair": {"repair", "skip"},
        "planet_water_recycler": {"fix", "ignore"},
    }.get(ev_type, set())

    if choice not in valid:
        return jsonify(state_payload())

    # --- Apply consequences for this event type ---
    if ev_type == "planet_latch_repair":
        if choice == "repair":
            # Food goes down 10% (current value)
            STATE["food"] = max(0.0, STATE.get("food", 100.0) * 0.90)

            # Morale boost for taking care of ship
            STATE["morale"] = min(100.0, STATE.get("morale", 100.0) + 6.0)

        elif choice == "skip":
            # Ship health decreases randomly
            dmg = random.uniform(5.0, 20.0)
            STATE["ship_health"] = max(0.0, STATE.get("ship_health", 100.0) - dmg)

            # Morale penalty for ignoring repairs
            STATE["morale"] = max(0.0, STATE.get("morale", 100.0) - 8.0)

        # If ship health < 50, oxygen decreases by 25% at every planet decision
        if STATE.get("ship_health", 100.0) < 50.0:
            STATE["oxygen"] = max(0.0, STATE.get("oxygen", 100.0) * 0.75)

    elif ev_type == "planet_water_recycler":
        if choice == "fix":
            # Food cost
            STATE["food"] = max(0.0, STATE.get("food", 100.0) * 0.90)

            # Morale boost for fixing systems
            STATE["morale"] = min(100.0, STATE.get("morale", 100.0) + 6.0)

        elif choice == "ignore":
            # Water drops immediately
            STATE["water"] = max(0.0, STATE.get("water", 100.0) - 20.0)

            # Morale penalty for taking the risk
            STATE["morale"] = max(0.0, STATE.get("morale", 100.0) - 4.0)

    # Clear event so sim resumes
    STATE["pending_event"] = None
    return jsonify(state_payload())

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
        STATE["space_burns_left"] -= 1
        STATE["consecutive_burns"] += 1
        
        # implement fuel deduction after each emergency propulsion
        # Subtract 10% of total fuel per emergency thrust
        STATE["fuel"] = max(0, STATE.get("fuel", 100.0) - 10.0)

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