from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import math

app = Flask(__name__)
CORS(app)

G = 1.0  # placeholder "game units" gravitational constant

@dataclass
class Body:
    x: float
    y: float
    vx: float
    vy: float
    m: float

# Simple in-memory state (fine for a hackathon demo)
STATE = {
    "planet": Body(x=0.0, y=0.0, vx=0.0, vy=0.0, m=2000.0),
    "ship":   Body(x=-250.0, y=-60.0, vx=2.2, vy=1.1, m=1.0),
    "t": 0.0,
}

def accel_due_to_gravity(ship: Body, planet: Body) -> tuple[float, float]:
    dx = planet.x - ship.x
    dy = planet.y - ship.y
    r2 = dx*dx + dy*dy
    # Avoid singularity / blow-ups if you get too close
    softening = 25.0
    r2 = max(r2, softening)
    r = math.sqrt(r2)
    a = G * planet.m / r2
    ax = a * dx / r
    ay = a * dy / r
    return ax, ay

def step(dt: float) -> None:
    ship: Body = STATE["ship"]
    planet: Body = STATE["planet"]

    ax, ay = accel_due_to_gravity(ship, planet)

    # Semi-implicit Euler (stable enough for demos)
    ship.vx += ax * dt
    ship.vy += ay * dt
    ship.x += ship.vx * dt
    ship.y += ship.vy * dt

    STATE["t"] += dt

def serialize_state() -> Dict[str, Any]:
    return {
        "t": STATE["t"],
        "planet": asdict(STATE["planet"]),
        "ship": asdict(STATE["ship"]),
    }

@app.get("/api/state")
def get_state():
    return jsonify(serialize_state())

@app.post("/api/step")
def post_step():
    data = request.get_json(silent=True) or {}
    dt = float(data.get("dt", 0.016))  # ~60 FPS default
    dt = max(0.001, min(dt, 0.2))      # clamp for safety
    step(dt)
    return jsonify(serialize_state())

@app.post("/api/reset")
def post_reset():
    data = request.get_json(silent=True) or {}
    # Allow optional overrides from UI
    STATE["planet"] = Body(
        x=float(data.get("planet_x", 0.0)),
        y=float(data.get("planet_y", 0.0)),
        vx=0.0,
        vy=0.0,
        m=float(data.get("planet_m", 2000.0)),
    )
    STATE["ship"] = Body(
        x=float(data.get("ship_x", -250.0)),
        y=float(data.get("ship_y", -60.0)),
        vx=float(data.get("ship_vx", 2.2)),
        vy=float(data.get("ship_vy", 1.1)),
        m=1.0,
    )
    STATE["t"] = 0.0
    return jsonify(serialize_state())

if __name__ == "__main__":
    # Run: python app.py
    app.run(host="127.0.0.1", port=5000, debug=True)
