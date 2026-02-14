import math
from typing import Tuple

def norm(x: float, y: float) -> float:
    return math.sqrt(x * x + y * y)

def unit(x: float, y: float) -> Tuple[float, float]:
    n = norm(x, y)
    if n < 1e-9:
        return (0.0, 0.0)
    return (x / n, y / n)

def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return norm(a[0] - b[0], a[1] - b[1])
