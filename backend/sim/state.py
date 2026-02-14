from typing import Any, Dict
from sim.models import Rocket, Destination, Camera
from sim.config import ZOOM_DEFAULT

STATE: Dict[str, Any] = {
    "t": 0.0,
    "rocket": Rocket(x=0.0, y=0.0, vx=3.0, vy=0.6),
    "planets": [],
    "dest": Destination(x=2600.0, y=0.0, radius=40.0),
    "camera": Camera(cx=0.0, cy=0.0, zoom=ZOOM_DEFAULT),
    "status": "running",
    "fail_reason": None,
    "last_plan_time": -1e9,
    "seed": None,

    "latched_planet_id": None,  # Stores the ID of the planet we are stuck to
    "countdown": 0.0,           # Timer for 'okay' planets

}