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
    "pending_event": None,  # {type, planet_id, prompt, choices[]} or None

    "latched_planet_id": None,  # Stores the ID of the planet we are stuck to
    "countdown": 0.0,           # Timer for orange planets

    "crew_health": 100.0,
    "ship_health":  100.0,
    "food": 100.0,
    "water": 100.0,
    
    "oxygen": 100.0,
    "fuel": 100.0,
    "morale": 100.0,
    "good_streak": 0,          # consecutive good planets visited
    # When water hits 0: you may latch onto 1 more planet, then game over.
    "water_grace_planets": None,  # int or None

    # When food hits 0: you may latch onto 2 more planets, then game over.
    "food_grace_planets": None,  # int or None

    "space_burns_left": 3,      # 3-times allowed propulsion (out of orbit)
    "can_space_burn": True,
}
