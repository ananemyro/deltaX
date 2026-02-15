"""
YES/NO terminal prototype for Slingshot + Crew Events.

Design:
- Every event asks ONE yes/no question.
- "Yes" and "No" each have their own probability-driven outcome.
- Includes: resources + morale/trust/health, stress/chaos, butterfly flags, causal recap.

Run:
  python3 slingshot_yesno.py
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
import random

# -----------------------------
# Utilities
# -----------------------------

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + (2.718281828459045 ** (-z)))

def chance(p: float) -> bool:
    return random.random() < clamp(p, 0.0, 1.0)

def ask_yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("Please type y or n.")

# -----------------------------
# Game State
# -----------------------------

@dataclass
class GameState:
    day: int = 1

    # Resources (0..100)
    oxygen: int = 85
    food: int = 80
    fuel: int = 70

    # Human stats (0..100)
    health: int = 85
    morale: int = 60
    trust: int = 60
    stress: int = 25

    # Chaos meter (0..100)
    chaos: int = 10

    # Butterfly flags
    flags: Dict[str, int] = field(default_factory=lambda: {
        "fatigue": 0,
        "micro_damage": 0,
        "infection_seed": 0,
        "lies_count": 0,
        "spares": 1,
    })

    history: List[Dict] = field(default_factory=list)
    crew_alive: bool = True
    ship_lost: bool = False

    def apply(self, **deltas: int) -> None:
        for k, v in deltas.items():
            if not hasattr(self, k):
                raise KeyError(f"Unknown state field: {k}")
            new_val = getattr(self, k) + v
            if k in ("oxygen", "food", "fuel", "health", "morale", "trust", "stress", "chaos"):
                new_val = int(clamp(new_val, 0, 100))
            setattr(self, k, new_val)

    def tick_day_costs(self) -> None:
        # baseline depletion per "stage/day"
        self.apply(
            oxygen=-5,
            food=-3,
            stress=+2 if self.oxygen < 30 or self.food < 30 else +1,
        )

        # stress bleed
        if self.stress > 70:
            self.apply(morale=-3, trust=-2)
        elif self.stress > 50:
            self.apply(morale=-2)
        elif self.stress > 30:
            self.apply(morale=-1)

        # critical resources hurt health
        if self.oxygen < 15:
            self.apply(health=-12, stress=+6)
        elif self.oxygen < 25:
            self.apply(health=-6, stress=+3)

        if self.food < 15:
            self.apply(health=-8, stress=+4)
        elif self.food < 25:
            self.apply(health=-4, stress=+2)

        if self.health <= 0 or self.oxygen <= 0:
            self.crew_alive = False

    def survival_forecast(self) -> float:
        z = (
            0.06 * self.oxygen
            + 0.04 * self.food
            + 0.03 * self.fuel
            + 0.02 * self.morale
            + 0.02 * self.trust
            - 0.06 * self.stress
            - 0.05 * self.chaos
            - 5.0
        )
        return sigmoid(z)

# -----------------------------
# Probability helpers
# -----------------------------

def chaos_penalty(gs: GameState) -> float:
    return 0.0030 * gs.chaos  # 100 -> 0.30

def fatigue_penalty(gs: GameState) -> float:
    return 0.12 * gs.flags.get("fatigue", 0)

def damage_penalty(gs: GameState) -> float:
    return 0.10 * gs.flags.get("micro_damage", 0)

# -----------------------------
# Yes/No Events
# -----------------------------

@dataclass
class YesNoOutcome:
    text: str
    apply: Callable[[GameState], None]
    because: Optional[str] = None

@dataclass
class YesNoEvent:
    name: str
    intro: str
    question: str
    trigger: Callable[[GameState], bool]

    # each branch has its own probability function + success/fail outcomes
    yes_prob: Callable[[GameState], float]
    yes_success: YesNoOutcome
    yes_fail: YesNoOutcome

    no_prob: Callable[[GameState], float]
    no_success: YesNoOutcome
    no_fail: YesNoOutcome

def make_events() -> List[YesNoEvent]:
    ev: List[YesNoEvent] = []

    # 1) Oxygen repair: "Do we attempt emergency repair now?"
    ev.append(YesNoEvent(
        name="Oxygen Filter Clog",
        intro="ALERT: Oxygen filtration clog detected. Left unchecked, oxygen loss accelerates.",
        question="Attempt emergency repair NOW?",
        trigger=lambda gs: gs.day == 1 or gs.oxygen <= 80,

        yes_prob=lambda gs: clamp(
            0.78 + 0.002 * gs.trust + 0.001 * gs.morale
            - chaos_penalty(gs) - fatigue_penalty(gs),
            0.05, 0.95
        ),
        yes_success=YesNoOutcome(
            text="Repair succeeds. Oxygen stabilizes.",
            apply=lambda gs: gs.apply(oxygen=+18, morale=+3, stress=-3),
        ),
        yes_fail=YesNoOutcome(
            text="Repair fails and worsens the leak. Hull strain increases.",
            apply=lambda gs: (
                gs.apply(oxygen=-15, health=-6, stress=+8, trust=-4),
                gs.flags.__setitem__("micro_damage", gs.flags["micro_damage"] + 1),
                gs.apply(chaos=+4),
            ),
            because="Rushing repairs can create micro-damage (future failures more likely)."
        ),

        no_prob=lambda gs: clamp(0.92 - chaos_penalty(gs), 0.05, 0.98),
        no_success=YesNoOutcome(
            text="You delay repairs without immediate disaster. But oxygen continues dropping.",
            apply=lambda gs: gs.apply(oxygen=-10, stress=+2, morale=-1),
        ),
        no_fail=YesNoOutcome(
            text="Delay backfires: clog accelerates unexpectedly.",
            apply=lambda gs: gs.apply(oxygen=-18, stress=+5, trust=-2, chaos=+3),
            because="High chaos makes systems less predictable."
        ),
    ))

    # 2) Rest: "Allow a rest break?"
    ev.append(YesNoEvent(
        name="Crew Fatigue",
        intro="MESSAGE: Crew reports mounting fatigue before the next maneuver.",
        question="Grant a short rest break?",
        trigger=lambda gs: gs.day in (2, 3),

        yes_prob=lambda gs: 0.95,
        yes_success=YesNoOutcome(
            text="Rest granted. Crew performance improves.",
            apply=lambda gs: (
                gs.apply(morale=+6, stress=-6, trust=+2),
                gs.flags.__setitem__("fatigue", max(0, gs.flags["fatigue"] - 1)),
            ),
        ),
        yes_fail=YesNoOutcome(
            text="Rest is disrupted by alarms. Minimal benefit.",
            apply=lambda gs: gs.apply(morale=+1, stress=-1),
        ),

        no_prob=lambda gs: clamp(0.90 - chaos_penalty(gs), 0.05, 0.95),
        no_success=YesNoOutcome(
            text="You push onward. Crew complies, but fatigue rises.",
            apply=lambda gs: (
                gs.apply(trust=-2, morale=-3, stress=+4, chaos=+3),
                gs.flags.__setitem__("fatigue", gs.flags["fatigue"] + 1),
            ),
            because="Denied rest increases fatigue (hurts future repair odds)."
        ),
        no_fail=YesNoOutcome(
            text="Crew argues openly. Morale and trust drop sharply.",
            apply=lambda gs: (
                gs.apply(trust=-6, morale=-5, stress=+6, chaos=+6),
                gs.flags.__setitem__("fatigue", gs.flags["fatigue"] + 1),
            ),
            because="Conflict raises chaos (more cascading failures)."
        ),
    ))

    # 3) Close flyby: "Go for a very close slingshot?"
    ev.append(YesNoEvent(
        name="Close Flyby Option",
        intro="NAV: A very close flyby could give a major slingshot boost but risks structural strain.",
        question="Attempt the VERY close flyby?",
        trigger=lambda gs: gs.day >= 3,

        yes_prob=lambda gs: clamp(
            0.70 + 0.001 * gs.morale
            - chaos_penalty(gs) - damage_penalty(gs),
            0.05, 0.90
        ),
        yes_success=YesNoOutcome(
            text="Massive boost achieved. You save time, but strain the hull.",
            apply=lambda gs: (
                gs.apply(stress=+3, chaos=+6),
                gs.flags.__setitem__("micro_damage", gs.flags["micro_damage"] + 1),
            ),
            because="Aggressive maneuvers add micro-damage (butterfly seed)."
        ),
        yes_fail=YesNoOutcome(
            text="Near-miss causes vibration damage and scares the crew.",
            apply=lambda gs: (
                gs.apply(fuel=-8, stress=+10, morale=-5, chaos=+10),
                gs.flags.__setitem__("micro_damage", gs.flags["micro_damage"] + 2),
            ),
            because="Botched close flyby amplifies chaos and damage."
        ),

        no_prob=lambda gs: 0.96,
        no_success=YesNoOutcome(
            text="You take a safer route. Slower return means more resource drain later.",
            apply=lambda gs: gs.apply(stress=-2),
        ),
        no_fail=YesNoOutcome(
            text="Solar activity disrupts sensors briefly.",
            apply=lambda gs: gs.apply(stress=+3, chaos=+2),
        ),
    ))

    # 4) Planet stop: "Stop to resupply?"
    ev.append(YesNoEvent(
        name="Planet Stop Decision",
        intro="SCAN: Nearby body has ice deposits. Estimated 65% safe, 35% toxic exposure risk.",
        question="Stop to resupply?",
        trigger=lambda gs: gs.food < 55 or gs.oxygen < 55,

        yes_prob=lambda gs: clamp(0.65 - chaos_penalty(gs), 0.05, 0.90),
        yes_success=YesNoOutcome(
            text="Resupply succeeds. Supplies replenished!",
            apply=lambda gs: gs.apply(food=+25, oxygen=+20, morale=+4, stress=-4),
        ),
        yes_fail=YesNoOutcome(
            text="Toxic exposure. Someone falls ill.",
            apply=lambda gs: (
                gs.apply(health=-18, morale=-6, stress=+10, chaos=+8),
                gs.flags.__setitem__("infection_seed", gs.flags["infection_seed"] + 1),
            ),
            because="Stopping planted an infection seed (future medical events)."
        ),

        no_prob=lambda gs: 0.95,
        no_success=YesNoOutcome(
            text="You skip the stop. Crew worries, but mission continues.",
            apply=lambda gs: gs.apply(morale=-3, trust=-1, stress=+2),
        ),
        no_fail=YesNoOutcome(
            text="Rumors spread: 'We could've resupplied.' Trust drops.",
            apply=lambda gs: gs.apply(trust=-4, morale=-4, stress=+4),
        ),
    ))

    # 5) Medical consequence: "Quarantine?"
    ev.append(YesNoEvent(
        name="Medical: Fever",
        intro="MED: A crew member shows fever-like symptoms.",
        question="Quarantine immediately?",
        trigger=lambda gs: gs.flags.get("infection_seed", 0) >= 1 and gs.day >= 5,

        yes_prob=lambda gs: clamp(0.80 - chaos_penalty(gs), 0.05, 0.95),
        yes_success=YesNoOutcome(
            text="Quarantine slows spread. Morale dips from fear.",
            apply=lambda gs: (
                gs.apply(health=-2, morale=-4, stress=+2),
                gs.flags.__setitem__("infection_seed", max(0, gs.flags["infection_seed"] - 1)),
            ),
            because="Quarantine contained earlier exposure."
        ),
        yes_fail=YesNoOutcome(
            text="Too late. Multiple cases appear.",
            apply=lambda gs: gs.apply(health=-12, morale=-8, stress=+10, chaos=+10),
            because="Infection cascaded under high chaos."
        ),

        no_prob=lambda gs: clamp(0.72 + 0.001 * gs.trust - chaos_penalty(gs), 0.05, 0.95),
        no_success=YesNoOutcome(
            text="You treat quietly. Symptoms fade and crew stays calm.",
            apply=lambda gs: (
                gs.apply(health=+2, morale=+2, trust=+2, stress=-2),
                gs.flags.__setitem__("infection_seed", max(0, gs.flags["infection_seed"] - 1)),
            ),
        ),
        no_fail=YesNoOutcome(
            text="Crew finds out you hid it. Panic rises.",
            apply=lambda gs: (
                gs.apply(health=-8, morale=-10, trust=-12, stress=+12, chaos=+12),
                gs.flags.__setitem__("lies_count", gs.flags["lies_count"] + 1),
            ),
            because="Secrecy backfired and damaged trust."
        ),
    ))

    return ev

# -----------------------------
# Engine
# -----------------------------

def pick_event(gs: GameState, events: List[YesNoEvent]) -> Optional[YesNoEvent]:
    eligible = [e for e in events if e.trigger(gs)]
    if not eligible:
        return None
    return random.choice(eligible)

def show_state(gs: GameState) -> None:
    forecast = gs.survival_forecast()
    confidence = clamp(1.0 - gs.chaos / 120.0, 0.15, 1.0)
    displayed = forecast if chance(confidence) else clamp(forecast + random.uniform(-0.20, 0.20), 0.0, 1.0)

    print("\n--- STATUS ---")
    print(f"Day: {gs.day}")
    print(f"Resources: O2={gs.oxygen:3d}  Food={gs.food:3d}  Fuel={gs.fuel:3d}")
    print(f"Crew:      Health={gs.health:3d}  Morale={gs.morale:3d}  Trust={gs.trust:3d}")
    print(f"Hidden-ish: Stress={gs.stress:3d}  Chaos={gs.chaos:3d}  Flags={gs.flags}")
    print(f"AI survival forecast: {displayed*100:5.1f}%  (confidence ~{confidence*100:4.0f}%)")

def log_history(gs: GameState, event: YesNoEvent, answered_yes: bool, success: bool, outcome: YesNoOutcome) -> None:
    gs.history.append({
        "day": gs.day,
        "event": event.name,
        "question": event.question,
        "answer": "YES" if answered_yes else "NO",
        "success": success,
        "result": outcome.text,
        "because": outcome.because,
        "snapshot": {
            "oxygen": gs.oxygen, "food": gs.food, "fuel": gs.fuel,
            "health": gs.health, "morale": gs.morale, "trust": gs.trust,
            "stress": gs.stress, "chaos": gs.chaos, "flags": dict(gs.flags),
        }
    })

def run_stage(gs: GameState, events: List[YesNoEvent]) -> None:
    show_state(gs)

    if not gs.crew_alive:
        print("\n[NO RESPONSE FROM CREW]")
        return

    event = pick_event(gs, events)
    if event is None:
        print("\nNo major events today. The mission continues...")
        return

    print("\n" + "=" * 60)
    print(f"EVENT: {event.name}")
    print(event.intro)
    answered_yes = ask_yes_no(event.question)

    if answered_yes:
        p = event.yes_prob(gs)
        ok = chance(p)
        outcome = event.yes_success if ok else event.yes_fail
    else:
        p = event.no_prob(gs)
        ok = chance(p)
        outcome = event.no_success if ok else event.no_fail

    print(f"\nBranch success chance was ~{p*100:.1f}%. Outcome: {'SUCCESS' if ok else 'FAIL'}")
    print(outcome.text)

    outcome.apply(gs)
    log_history(gs, event, answered_yes, ok, outcome)

def recap(gs: GameState) -> None:
    print("\n" + "=" * 60)
    print("CAUSAL CHAIN RECAP")
    print("=" * 60)

    if not gs.history:
        print("No events occurred.")
        return

    for h in gs.history:
        tag = "✓" if h["success"] else "✗"
        print(f"\nDay {h['day']:2d} {tag}  {h['event']}")
        print(f"  Q: {h['question']}")
        print(f"  A: {h['answer']}")
        print(f"  Result: {h['result']}")
        if h["because"]:
            print(f"  Butterfly link: {h['because']}")

    print("\nFINAL STATUS:")
    print(f"  Crew alive: {gs.crew_alive}")
    print(f"  Oxygen/Food/Fuel: {gs.oxygen}/{gs.food}/{gs.fuel}")
    print(f"  Health/Morale/Trust: {gs.health}/{gs.morale}/{gs.trust}")
    print(f"  Stress/Chaos: {gs.stress}/{gs.chaos}")
    print(f"  Flags: {gs.flags}")

def main(seed: Optional[int] = None) -> None:
    if seed is not None:
        random.seed(seed)

    gs = GameState()
    events = make_events()

    print("Slingshot Crew Prototype (YES/NO edition)")
    print("Goal: Return home AND keep the crew alive.\n")

    MAX_STAGES = 12

    while gs.day <= MAX_STAGES and gs.crew_alive and not gs.ship_lost:
        run_stage(gs, events)
        gs.tick_day_costs()
        gs.day += 1

    if not gs.crew_alive:
        print("\nMission log ends abruptly. No further crew responses.")
    else:
        print("\nYou reach the end of the prototype timeline.")

    recap(gs)

if __name__ == "__main__":
    main()
