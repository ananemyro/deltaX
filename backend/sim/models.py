from dataclasses import dataclass

@dataclass
class Rocket:
    x: float
    y: float
    vx: float
    vy: float

@dataclass
class Planet:
    id: int
    x: float
    y: float
    mass: float
    radius: float
    kind: str
    revealed: bool
    recoverable: bool
    color: str 

@dataclass
class Destination:
    x: float
    y: float
    radius: float

@dataclass
class Camera:
    cx: float
    cy: float
    zoom: float
