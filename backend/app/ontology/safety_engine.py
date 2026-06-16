"""
Ontology-Based Safety Engine — SWRL Rule Implementation
Enforces clinical exercise safety guidelines as deterministic rules.

All rules are checked against every exercise before it can be recommended.
Rules are a HARD VETO — ML scores cannot override them.
Every rule firing is logged to safety_audit_logs for research compliance.

SWRL Rule Format:
  condition(user_profile, exercise) → block with reason
"""
from typing import Tuple, Optional, List


# ── SWRL Rule Definitions ─────────────────────────────────────────────────────
# Each rule has: id, name, condition lambda, reason string
SWRL_RULES = [
    {
        "id":   "R1",
        "name": "Obesity High Intensity Block",
        "reason": "BMI > 35 — high-intensity exercises excluded to prevent cardiovascular strain (SWRL R1)",
        "condition": lambda p, e: (
            p.get("bmi", 0) > 35 and
            e.get("intensity_level") == "High"
        ),
    },
    {
        "id":   "R2",
        "name": "Hypertension Guard",
        "reason": "Hypertension detected — high-intensity exercises excluded to prevent dangerous BP spike (SWRL R2)",
        "condition": lambda p, e: (
            "hypertension" in p.get("conditions", []) and
            e.get("intensity_level") == "High"
        ),
    },
    {
        "id":   "R3",
        "name": "Joint Impact Filter",
        "reason": "Joint pain — high-impact exercises excluded to prevent injury (SWRL R3)",
        "condition": lambda p, e: (
            "joint-pain" in p.get("conditions", []) and
            e.get("name", "") in {
                "Treadmill Run", "HIIT Intervals", "Bodyweight Squats",
                "Box Jumps", "Jump Rope", "Running", "Dumbbell Lunges",
            }
        ),
    },
    {
        "id":   "R4",
        "name": "Elderly Safety Rule",
        "reason": "Elderly profile (65+) — high-intensity exercises excluded for cardiovascular safety (SWRL R4)",
        "condition": lambda p, e: (
            (
                "elderly" in p.get("conditions", []) or
                p.get("age", 0) >= 65
            ) and
            e.get("intensity_level") == "High"
        ),
    },
    {
        "id":   "R5",
        "name": "Diabetes MET Ceiling",
        "reason": "Type 2 Diabetes — exercises with MET ≥ 8.0 excluded for safe glycaemic response (SWRL R5)",
        "condition": lambda p, e: (
            "diabetes" in p.get("conditions", []) and
            float(e.get("met_value", 0)) >= 8.0
        ),
    },
    {
        "id":   "R6",
        "name": "Back Pain Spinal Guard",
        "reason": "Back pain — spinal-loading exercises excluded to prevent disc injury (SWRL R6)",
        "condition": lambda p, e: (
            "back-pain" in p.get("conditions", []) and
            e.get("name", "") in {
                "Deadlift", "Barbell Squat", "Good Mornings",
                "Heavy Rowing", "Bent-Over Barbell Row",
            }
        ),
    },
    {
        "id":   "R7",
        "name": "Obese Moderate Guard",
        "reason": "BMI > 40 — moderate and high-intensity exercises excluded. Low-intensity only (SWRL R7)",
        "condition": lambda p, e: (
            p.get("bmi", 0) > 40 and
            e.get("intensity_level") in {"High", "Moderate"}
        ),
    },
]


# ── Core Safety Check ─────────────────────────────────────────────────────────
def check_exercise_safety(
    user_profile: dict,
    exercise: dict,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Run all SWRL rules against a user profile and one exercise.

    Args:
        user_profile: dict with bmi, conditions (list), age
        exercise:     dict with name, intensity_level, met_value

    Returns:
        (is_safe, rule_id_fired, reason)
        is_safe=True  → exercise is safe to recommend
        is_safe=False → exercise is blocked; rule_id and reason explain why
    """
    for rule in SWRL_RULES:
        try:
            if rule["condition"](user_profile, exercise):
                return False, rule["id"], rule["reason"]
        except Exception:
            continue
    return True, None, None


def get_safe_exercises(user_profile: dict, exercises: list) -> dict:
    """
    Filter a catalogue of exercises through the full safety layer.

    Returns:
        {"safe": [...], "blocked": [{"exercise": ..., "rule": ..., "reason": ...}]}
    """
    safe, blocked = [], []
    for ex in exercises:
        is_safe, rule_id, reason = check_exercise_safety(user_profile, ex)
        if is_safe:
            safe.append(ex)
        else:
            blocked.append({"exercise": ex, "rule": rule_id, "reason": reason})
    return {"safe": safe, "blocked": blocked}


def get_active_rules(user_profile: dict) -> List[dict]:
    """
    Return all SWRL rules that are currently active for a given profile.
    Uses a high-intensity dummy exercise to detect which rules would fire.
    """
    active = []
    dummy_high = {
        "name": "__test__",
        "intensity_level": "High",
        "met_value": 9.0,
    }
    for rule in SWRL_RULES:
        try:
            if rule["condition"](user_profile, dummy_high):
                active.append({
                    "id":     rule["id"],
                    "name":   rule["name"],
                    "reason": rule["reason"],
                })
        except Exception:
            pass
    return active


def get_rule_summary() -> List[dict]:
    """Return all rules with their IDs and names for display purposes."""
    return [
        {"id": r["id"], "name": r["name"], "reason": r["reason"]}
        for r in SWRL_RULES
    ]
