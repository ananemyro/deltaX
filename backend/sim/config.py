DT = 10.0
G = 1.0
SOFTENING_KM = 200.0       # prevents singularities at close range
DT_MIN = 0.001
DT_MAX = 60.0
MAX_WORLD_ABS = 2.0e9

DV_MAX = 2.0
PLAN_COOLDOWN_S = 0.25

CAM_ALPHA = 0.35
LOOKAHEAD = 0.0
ZOOM_DEFAULT = 1.0e-5

GOOD_COUNT = 10
BAD_COUNT = 12
GOOD_MU_RANGE = (1e5, 5e6)
BAD_MU_RANGE  = (5e6, 2e8)
PLANET_RADIUS_RANGE = (2_000.0, 70_000.0)  # km

HAZARD_RADIUS_FACTOR = 20.0
DEATH_RADIUS_FACTOR = 50
CRASH_RADIUS_FACTOR = 1.0

REVEAL_MARGIN = 0.0
HAZARD_RADIUS_MIN_KM = 600_000.0

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))
