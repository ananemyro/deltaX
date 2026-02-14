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

@app.post("/api/plan")
def api_plan():
    if STATE["status"] != "running":
        return jsonify(state_payload())

    data = request.get_json(silent=True) or {}
    t = float(STATE["t"])

    if (t - float(STATE["last_plan_time"])) < PLAN_COOLDOWN_S:
        return jsonify(state_payload())

    rocket = STATE["rocket"]

    if "dvx" in data and "dvy" in data:
        dvx = float(data["dvx"])
        dvy = float(data["dvy"])
    else:
        dx = float(data.get("dx", 0.0))
        dy = float(data.get("dy", 0.0))
        pixels_to_world = float(data.get("pixels_to_world", 1.0))
        dvx = dx * pixels_to_world
        dvy = dy * pixels_to_world

    mag = norm(dvx, dvy)
    if mag > DV_MAX:
        ux, uy = unit(dvx, dvy)
        dvx, dvy = ux * DV_MAX, uy * DV_MAX

    rocket.vx += dvx
    rocket.vy += dvy
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
