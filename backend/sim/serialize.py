from dataclasses import asdict
from typing import Any, Dict, List
from sim.state import STATE
from sim.models import Planet, Rocket, Destination, Camera
from sim.hud import hud

def serialize_planet(p: Planet) -> Dict[str, Any]:
    # UI wants: white by default; green/red once revealed
    if not p.revealed:
        color = "white"
        status = "unknown"
    else:
        if p.kind == "good":
            color = "green"
            status = "good"
        else:
            color = "red"
            status = "bad"

    return {
        "id": p.id,
        "x": p.x, "y": p.y,
        "mass": p.mass,
        "radius": p.radius,
        "revealed": p.revealed,
        "recoverable": p.recoverable,
        "status": status,
        "color": color,
    }

def state_payload() -> Dict[str, Any]:
    rocket: Rocket = STATE["rocket"]
    dest: Destination = STATE["dest"]
    cam: Camera = STATE["camera"]
    planets: List[Planet] = STATE["planets"]

    return {
        "t": STATE["t"],
        "seed": STATE.get("seed"),
        "rocket": asdict(rocket),
        "destination": asdict(dest),
        "camera": asdict(cam),
        "planets": [serialize_planet(p) for p in planets],
        "hud": hud(),
    }