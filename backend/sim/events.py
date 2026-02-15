# sim/events.py
import random

EVENTS = {
    "ice_mining": {
        "text": "Scanners detect deep glacial deposits. Deploy mining drones for water?",
        "yes": {"water": 30, "fuel": -10, "text": "Drones returned with ice! Water +30, Fuel -10."},
        "no": {"text": "You decide to conserve fuel and move on."}
    },
    "ship_salvage": {
        "text": "An old wreck lies nearby. Scavenge it for hull plating?",
        "yes": {"ship_health": 20, "food": -5, "text": "Found scrap metal! Health +20, Food -5."},
        "no": {"text": "The wreck looks unstable. Better safe than sorry."}
    },
    "local_flora": {
        "text": "Strange glowing moss is edible but looks suspicious. Harvest for food?",
        "yes": {"food": 40, "ship_health": -15, "text": "The moss is nutritious, but released corrosive spores. Food +40, Health -15."},
        "no": {"text": "You ignore the moss. Survival requires caution."}
    }
}

def get_random_event():
    event_id = random.choice(list(EVENTS.keys()))
    return {"id": event_id, **EVENTS[event_id]}

