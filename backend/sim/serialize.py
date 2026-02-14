from dataclasses import asdict
from typing import Any, Dict, List
from sim.state import STATE
from sim.models import Planet, Rocket, Destination, Camera
from sim.hud import hud

def serialize_planet(p: Planet) -> Dict[str, Any]:

    # version 1: with the good and bad 
    # UI wants: white by default; green/red once revealed
    # if not p.revealed:
    #     color = "white"
    #     status = "unknown"
    # else:
    #     if p.kind == "good":
    #         color = "green"
    #         status = "good"
    #     else:
    #         color = "red"
    #         status = "bad"


    #----
    # implement different types of "planets"
    #----

    # version2: code works, but not reavling colors...
    if not p.revealed:
            color = "grey"
            status = "unknown"
    else:

        status = p.kind # Keep the actual kind

        # Map specific colors based on the 'kind' or other attributes
        if p.kind == "good":            # "Good planets"
            color = "#9bb0ff"
        elif p.kind == "bad":           # "bad planets", rocket will crash
            color = "#ff2c2c"
        elif p.kind == "okay":          # "ish good planet "
            color = "#FF991c"
        else:
            color = "#f8f7ff" # Default white
            
        status = p.kind
       
        
    # version 3: not working
    # if not p.revealed:
    #         color = "grey"
    #         status = "unknown"
    # else:

    #     # status = p.kind # Keep the actual kind

    #     # Map specific colors based on the 'kind' or other attributes
    #     if p.kind == "good":            # "Good planets"
    #         color = "#9bb0ff"
    #         status = "good"
    #     elif p.kind == "bad":           # "bad planets", rocket will crash
    #         color = "#ff2c2c"
    #         status = "bad"
    #     elif p.kind == "okay":          # "ish good planet "
    #         color = "#FF991c"
    #         status = "okay"
    #     else:
    #         color = "#f8f7ff" # Default white
            

        

    




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